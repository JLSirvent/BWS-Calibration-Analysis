#   --------------------------------------------------------------------------
# Copyright (c) <2017> <Lionel Garcia>
# BE-BI-PM, CERN (European Organization for Nuclear Research)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#   --------------------------------------------------------------------------
#
#   Not fully documented


import os
import time
import numpy as np
import configparser
import scipy.io as sio
import PyQt5.QtCore as QtCore
import matplotlib.pyplot as plt

from tqdm import tqdm
from scipy.stats import norm
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d

import lib.utils as utils
from lib import diagnostic_tools as mplt


def process_position(data, parameter_file, StartTime, showplot=False, filename=None, return_processing=False, camelback_threshold_on=True):
    """
    Processing of the angular position based on the raw data of the OPS
    Credits : Jose Luis Sirvent (BE-BI-PM, CERN)
    """

    # Recuperation of processing parameters
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    SlitsperTurn = eval(config.get('OPS processing parameters', 'slits_per_turn'))
    sampling_frequency = eval(config.get('OPS processing parameters', 'sampling_frequency'))
    rdcp = eval(config.get('OPS processing parameters', 'relative_distance_correction_prameters'))
    prominence = eval(config.get('OPS processing parameters', 'prominence'))
    camelback_threshold = eval(config.get('OPS processing parameters', 'camelback_threshold'))
    OPS_processing_filter_freq = eval(config.get('OPS processing parameters', 'OPS_processing_filter_freq'))
    REMP_reference_threshold = eval(config.get('OPS processing parameters', 'REMP_reference_threshold'))
    References_Timming = eval(config.get('OPS processing parameters','References_Timming'))


    AngularIncrement = 2 * np.pi / SlitsperTurn

    threshold_reference = np.amax(data) - camelback_threshold * np.mean(data)

    if camelback_threshold_on is True:
        data[np.where(data > threshold_reference)] = threshold_reference

    max_data = np.amax(data)
    min_data = np.amin(data)

    data = utils.butter_lowpass_filter(data, OPS_processing_filter_freq, sampling_frequency, order=5)

    data = data - min_data
    data = data / max_data

    maxtab, mintab = utils.peakdet(data, prominence)

    false = np.where(mintab[:, 1] > np.mean(maxtab[:, 1]))
    mintab = np.delete(mintab, false, 0)

    locs_up = np.array(maxtab)[:, 0]
    pck_up = np.array(maxtab)[:, 1]

    locs_dwn = np.array(mintab)[:, 0]
    pck_dwn = np.array(mintab)[:, 1]

    LengthMin = np.minimum(pck_up.size, pck_dwn.size)

    # ==========================================================================
    # Position processing based on crossing points: Rising edges only
    # ==========================================================================
    # Crosing psotion evaluation
    Crosingpos = np.ones((2, LengthMin))
    Crosingpos[1][:] = np.arange(1, LengthMin + 1)
    IndexDwn = 0
    IndexUp = 0
    A = []

    # Position calculation loop:
    for i in range(0, LengthMin - 1):

        # Ensure crossing point in rising edge (locs_dwn < locs_up)
        while locs_dwn[IndexDwn] >= locs_up[IndexUp]:
            IndexUp += 1

        while locs_dwn[IndexDwn + 1] < locs_up[IndexUp]:
            IndexDwn += 1

        # Calculate thresshold for current window: Mean point
        Threshold = (data[int(locs_dwn[IndexDwn])] + data[int(locs_up[IndexUp])]) / 2
        # Find time on crossing point:
        b = int(locs_dwn[IndexDwn]) + np.where(data[int(locs_dwn[IndexDwn]):int(locs_up[IndexUp])] >= Threshold)[0][0]
        idx_n = np.where(data[int(locs_dwn[IndexDwn]):int(locs_up[IndexUp])] < Threshold)[0]
        idx_n = idx_n[::-1][0]
        a = int(locs_dwn[IndexDwn]) + idx_n

        Crosingpos[0, i] = (Threshold - data[int(a)]) * (b - a) / (data[int(b)] - data[int(a)]) + a

        # if showplot is True or showplot is 1:
        A = np.append(A, Threshold);

        # Move to next window:
        IndexDwn = IndexDwn + 1
        IndexUp = IndexUp + 1

    # ==========================================================================
    # Position loss compensation
    # ==========================================================================
    # Un-corrected position and time
    Data_Time = Crosingpos[0][:] * 1 / sampling_frequency
    Data_Pos = Crosingpos[1][:] * AngularIncrement
    # Relative-distances method for slit-loss compensation:
    Distances = np.diff(Crosingpos[0][0:Crosingpos.size - 1])
    RelDistr = np.divide(Distances[1:Distances.size], Distances[0:Distances.size - 1])
    # Search of compensation points:
    PointsCompensation = np.where(RelDistr >= rdcp[0])[0]

    for b in np.arange(0, PointsCompensation.size):

        if RelDistr[PointsCompensation[b]] >= rdcp[1]:
            # These are the references
            Data_Pos[(PointsCompensation[b] + 2):Data_Pos.size] = Data_Pos[(
                PointsCompensation[b] + 2):Data_Pos.size] + 2 * AngularIncrement

        elif RelDistr[PointsCompensation[b]] >= rdcp[0] and RelDistr[PointsCompensation[b]] <= rdcp[1]:
            # These are 1 slit losses
            Data_Pos[(PointsCompensation[b] + 2):Data_Pos.size] = Data_Pos[(
                PointsCompensation[b] + 2):Data_Pos.size] + 1 * AngularIncrement

    # ==========================================================================
    # Alignment to First reference and Storage
    # ==========================================================================

    if StartTime > References_Timming[0]/1000 :
        Rtiming = References_Timming[1]
    else:
        Rtiming = References_Timming[0]

    Offset = np.where(Data_Time[0:Data_Time.size - 1] + StartTime > (Rtiming/1000))[0][0]
    #print(References_Timming[0] / 1000)
    #print(Data_Time[Offset])
    #Offset = 100

    _IndexRef1 = Offset + np.where(RelDistr[Offset:LengthMin - Offset] > rdcp[1])[0]
    IndexRef1 = _IndexRef1[0]

    #if len(np.where(A[_IndexRef1 + 1] > REMP_reference_threshold)[0]) > 1:
    #    IndexRef1 = _IndexRef1[np.where(A[_IndexRef1 + 1] > 0.35)][0]

    # else:
    #     try:
    #         IndexRef1 = _IndexRef1[0]
    #         print(filename)
    #     except:
    # IndexRef1 = 0

    #else:
    #    IndexRef1 = 0
    #    print(filename)
    #    print(A[_IndexRef1], A[_IndexRef1 + 1])


    # print(Data_Time[IndexRef1] + StartTime)

    Data_Pos = Data_Pos - Data_Pos[IndexRef1]
    Data = np.ndarray((2, Data_Pos.size - 1))
    Data[0] = Data_Time[0:Data_Time.size - 1] + StartTime
    Data[1] = Data_Pos[0:Data_Pos.size - 1]


    # ==========================================================================
    # Plotting script
    # ==========================================================================
    if showplot is True or showplot is 1:
        fig = plt.figure(figsize=(11,5))
        ax1 = fig.add_subplot(111)
        mplt.make_it_nice(ax1)
        plt.axhspan(0, threshold_reference / max_data, color='black', alpha=0.1)
        plt.axvspan(1e3 * StartTime + 1e3 * (data.size * 1 / 4) / sampling_frequency,
                    1e3 * StartTime + 1e3 * (data.size * 3 / 4) / sampling_frequency, color='black', alpha=0.1)
        plt.plot(1e3 * StartTime + 1e3 * np.arange(0, data.size) * 1 / sampling_frequency, data, linewidth=0.5)
        plt.plot(1e3 * StartTime + 1e3 * locs_up * 1 / sampling_frequency, pck_up, '.', MarkerSize=1.5)
        plt.plot(1e3 * StartTime + 1e3 * locs_dwn * 1 / sampling_frequency, pck_dwn, '.', MarkerSize=1.5)
        plt.plot(1e3 * StartTime + 1e3 * Crosingpos[0][0:A.size] * 1 / sampling_frequency, A, linewidth=0.5)
        ax1.set_title('Optical position sensor processing', loc='left')
        ax1.set_xlabel('Time (um)')
        ax1.set_ylabel('Normalized amplitude of signal (A.U.)')
        plt.show(block=False)
    # plt.plot(1e3*StartTime+1e3*IndexRef1*1/sampling_frequency + StartTime, data[IndexRef1], 'x')
    #        plt.plot(1e3*StartTime+1e3*np.arange(1,Distances.size)*1/sampling_frequency + StartTime, RelDistr, '.')

    if return_processing is True:
        return [1e3 * StartTime + 1e3 * np.arange(0, data.size) * 1 / sampling_frequency, data,
                1e3 * StartTime + 1e3 * locs_up * 1 / sampling_frequency, pck_up,
                1e3 * StartTime + 1e3 * locs_dwn * 1 / sampling_frequency, pck_dwn,
                1e3 * StartTime + 1e3 * Crosingpos[0][0:A.size] * 1 / sampling_frequency, A,
                threshold_reference / max_data,
                1e3 * StartTime + 1e3 * Crosingpos[0][IndexRef1] * (1 / sampling_frequency)]

    else:
        return Data


def find_occlusions(data, IN=True, diagnostic_plot=False, StartTime=0, return_processing=False):
    """
      TO DO
      """

    # Cutting of the first part wich can contain parasite peaks
    #    beginingoff = lambda x: x[int(x.size/4)::]
    #    data = beginingoff(data)

    # We use a parameter file
    parameter_file = utils.resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    sampling_frequency = eval(config.get('OPS processing parameters', 'sampling_frequency'))
    peaks_detection_filter_freq = eval(config.get('OPS processing parameters', 'peaks_detection_filter_freq'))

    or_data = data

    # Modif by Jose (for compatibility when not using Photodiode):
    # ------------------------------------------------------------
    try:
        data = np.abs(-data)
        filtered_data = utils.butter_lowpass_filter(data, peaks_detection_filter_freq, sampling_frequency, order=5)

        # Modif by Jose (to avoid false peaks detection)
        margin = 3e-3  # temporal window around min in seconds

        valmax = np.amax(filtered_data)
        #print(valmax)

        indexvalmax = np.where(filtered_data == valmax)[0][0]
        #print(indexvalmax)

        indexleft = indexvalmax - np.int((margin / 2) * sampling_frequency)
        indexright = indexvalmax + np.int((margin / 2) * sampling_frequency)

        #print(indexleft)
        #print(indexright)

        filtered_data_short = filtered_data[indexleft:indexright]
        # -----

        pcks = utils.peakdet(filtered_data_short, valmax / 4)[0]
        pcks = np.transpose(pcks)

        # Modif by Jose:
        # -------------

        # try:
        locs = pcks[0] + indexleft
        # except:
        #    plt.figure()
        #    plt.plot(filtered_data)
        #    plt.show()
        #    return -1

        # -------------

        pcks = pcks[1]

        sorted_indexes = np.argsort(locs)

        if IN is False:
            sorted_indexes = sorted_indexes[::-1]

        locs = locs[sorted_indexes].astype(int)  # + int(data.size/4)

        if diagnostic_plot == True:
            plt.figure()
            mplt.nice_style()
            plt.plot(StartTime + 20e-6 * np.arange(0, filtered_data.size), filtered_data)
            plt.plot(StartTime + 20e-6 * locs, filtered_data[locs], '.')
            plt.show(block=False)

        if return_processing is True:

            return [StartTime + 1 / sampling_frequency * locs[0:2], or_data[locs[0:2]],
                    StartTime + 1 / sampling_frequency * np.arange(0, filtered_data.size), -filtered_data]

        else:
            return locs[0:2]

    except:
        print('Unable to find occlusions')
        locs = np.asarray([460331, 464319])
        locs = locs[0:2].astype(int)
        return [StartTime + 1 / sampling_frequency * locs[0:2], or_data[locs[0:2]],
                StartTime + 1 / sampling_frequency * np.arange(0, filtered_data.size), -filtered_data]
        # ------------------------------------------------------------


def process_complete_calibration(raw_data_folder, destination_folder):

    convert_raw_data = utils.CreateRawDataFolder(raw_data_folder, destination_folder)
    convert_raw_data.run()

    raw_data_processing = ProcessRawData(destination_folder + '\RAW_DATA\RAW_OUT', destination_folder)
    raw_data_processing.run()

    raw_data_processing = ProcessRawData(destination_folder + '\RAW_DATA\RAW_IN', destination_folder)
    raw_data_processing.run()

    utils.create_processed_data_folder(raw_data_folder, destination_folder, force_overwrite='y')

    process_calibration_results = ProcessCalibrationResults([raw_data_folder])
    process_calibration_results.run()


def mean_fit_parameters(folders, folders_name=None):
    
    a_IN = []
    b_IN = []
    c_IN = []

    a_OUT = []
    b_OUT = []
    c_OUT = []

    for folder in folders:
        if os.path.exists(folder + '/' + 'calibration_results.mat'):
            data = sio.loadmat(folder + '/' + 'calibration_results.mat', struct_as_record=False, squeeze_me=True)
            p = data['f_parameters_IN']
            a_IN.append(p[0])
            b_IN.append(p[1])
            c_IN.append(p[2])
            p = data['f_parameters_OUT']
            a_OUT.append(p[0])
            b_OUT.append(p[1])
            c_OUT.append(p[2])

    a_IN = np.asarray(a_IN)
    a_IN = np.mean(a_IN)
    b_IN = np.asarray(b_IN)
    b_IN = np.mean(b_IN)
    c_IN = np.asarray(c_IN)
    c_IN = np.mean(c_IN)

    a_OUT = np.asarray(a_OUT)
    a_OUT = np.mean(a_OUT)
    b_OUT = np.asarray(b_OUT)
    b_OUT = np.mean(b_OUT)
    c_OUT = np.asarray(c_OUT)
    c_OUT = np.mean(c_OUT)

    path = os.path.dirname(folders[0])

    if folders_name is not None:

        sio.savemat(path + '/mean_fit.mat',

                    dict(f_parameters_IN=[a_IN, b_IN, c_IN],
                         f_parameters_OUT=[a_OUT, b_OUT, c_OUT],
                         PROCESSED_folders_used=folders_name))
    else:

        sio.savemat(path + '/mean_fit.mat',

                    dict(f_parameters_IN=[a_IN, b_IN, c_IN],
                         f_parameters_OUT=[a_OUT, b_OUT, c_OUT]))


class ProcessRawData(QtCore.QThread):

    notifyProgress = QtCore.pyqtSignal(int)
    notifyState = QtCore.pyqtSignal(str)
    notifyFile = QtCore.pyqtSignal(str)

    def __init__(self, raw_data_folder, destination_folder, verbose=False, parent=None):

        self.raw_data_folder = raw_data_folder
        self.destination_folder = destination_folder
        self.verbose = verbose
        super(ProcessRawData, self).__init__(parent)

    def run(self):

        IN = self.raw_data_folder.find('_IN') != -1
        OUT = self.raw_data_folder.find('_OUT') != -1

        # ==========================================================================
        # Variables and parameters definiton
        # ==========================================================================
        angular_position_SA = []
        angular_position_SB = []
        data_PD = []
        eccentricity = []
        laser_position = []
        occlusion_position = []
        original_time_SB = []
        scan_number = []
        speed_SA = []
        speed_SB = []
        time_PD = []
        time_SA = []
        time_SB = []

        # We use a parameter file
        parameter_file = utils.resource_path('data/parameters.cfg')
        config = configparser.RawConfigParser()
        config.read(parameter_file)
        IN_range = eval(config.get('OPS processing parameters', 'IN_range'))
        OUT_range = eval(config.get('OPS processing parameters', 'OUT_range'))
        sampling_frequency = eval(config.get('OPS processing parameters', 'sampling_frequency'))
        process_occlusions = eval(config.get('OPS processing parameters','Process_Occlusions'))
        compensate_eccentricity =  eval(config.get('OPS processing parameters','Compensate_Eccentricity'))

        #mat_files, dir_path = utils.mat_list_from_folder(self.raw_data_folder)
        mat_files = utils.mat_list_from_folder_sorted(self.raw_data_folder)

        #mat = sio.loadmat(dir_path + '/' + mat_files[0])
        mat = sio.loadmat(mat_files[0])

        speed = mat['speed'][0]
        INorOUT = mat['INorOUT'][0]

        if IN is True:
            print('------- OPS Processing IN -------')
            StartTime = IN_range[0]
            self.notifyState.emit('OPS Processing IN')
            time.sleep(0.1)
        elif OUT is True:
            StartTime = OUT_range[0]
            print('------- OPS Processing OUT -------')
            self.notifyState.emit('OPS Processing OUT')
            time.sleep(0.1)


        # ==========================================================================
        # Raw data file names extraction
        # ==========================================================================


        # ==========================================================================
        # Main processing loop
        # ==========================================================================

        i = 0

        for mat_file in tqdm(mat_files):
            try:
                if self.verbose is True:
                    print(mat_file)

                self.notifyProgress.emit(int(i * 100 / len(mat_files)))
                time.sleep(0.1)

                self.notifyFile.emit(mat_file)
                time.sleep(0.1)

                #mat = sio.loadmat(dir_path + '/' + mat_file)
                mat = sio.loadmat(mat_file)

                _data_SA = mat['data_SA'][0]
                _data_SB = mat['data_SB'][0]
                _data_PD = mat['data_PD'][0]

                Data_SA = process_position(_data_SA, utils.resource_path('data/parameters.cfg'), StartTime, showplot=0, filename=mat_file)
                Data_SB = process_position(_data_SB, utils.resource_path('data/parameters.cfg'), StartTime, showplot=0, filename=mat_file)

                Data_SB_R = utils.resample(Data_SB, Data_SA)
                Data_SA_R = utils.resample(Data_SA, Data_SB)

                # Eccentricity from OPS processing and saving in list
                _eccentricity = np.subtract(Data_SA[1], Data_SB_R[1]) / 2
                eccentricity.append(_eccentricity)

                _eccentricity_B = np.subtract(Data_SB[1], Data_SA_R[1]) / 2

                # Decide Eccentricity compensation or not
                # ---------------------------------------
                if compensate_eccentricity is True:
                    Data_SA[1] = np.subtract(Data_SA[1], _eccentricity)
                    Data_SB[1] = np.subtract(Data_SB[1], _eccentricity_B)
                    Data_SB_R[1] = np.add(Data_SB_R[1], _eccentricity)
                # ---------------------------------------

                # OPS data saving in list
                angular_position_SA.append(Data_SA[1])
                angular_position_SB.append(Data_SB[1])

                # OPSA time saving in list
                time_SA.append(Data_SA[0])
                time_SB.append(Data_SB[0])

                # OPS speed processing and saving in list
                _speed_SA = np.divide(np.diff(Data_SA[1]), np.diff(Data_SA[0]))
                _speed_SB = np.divide(np.diff(Data_SB[1]), np.diff(Data_SB[0]))
                speed_SA.append(_speed_SA)
                speed_SB.append(_speed_SB)

                # Finding of occlusions and saving into a list
                if process_occlusions is True:
                    _time_PD = StartTime + np.arange(0, _data_PD.size) * 1 / sampling_frequency
                    occlusions = find_occlusions(_data_PD, IN)

                    # if occlusions is -1:
                    #     log.log_no_peaks(mat_file, IN)

                    # Modified by Jose:
                    # -----------------

                    # -- Old Method --
                    #Data_SA_R = utils.resample(Data_SA, np.array([_time_PD, _data_PD]))
                    #occ1 = Data_SA_R[1][int(occlusions[0])]
                    #occ2 = Data_SA_R[1][int(occlusions[1])]

                    # -- New Method: Slightly faster --
                    finterp = interp1d(Data_SA[0],Data_SA[1])
                    occ1 = finterp(_time_PD[int(occlusions[0])])
                    occ2 = finterp(_time_PD[int(occlusions[1])])
                    # -----------------

                    _occlusion = (occ2 - occ1) / 2 + occ1
                else:
                    _occlusion = StartTime + 0.02

                #test_range = np.array([0, np.pi])

                # if _occlusion < test_range[0] or _occlusion > test_range[1]:
                #     log.log_peaks_out_of_range(test_range, _occlusion, mat_file, IN)

                occlusion_position.append(_occlusion)

                # Laser position and scan number extraction from file name and saving in list
                _laser_position, _scan_number = utils.find_scan_info(mat_file)
                scan_number.append(int(_scan_number))
                laser_position.append(float(_laser_position))

            except:

                self.notifyState.emit("Error in file:" + mat_file)
                self.notifyProgress.emit("Error in file:" + mat_file)
                print("Error in file:" + mat_file)

            i += 1

        if IN is True:
            filename = 'PROCESSED_IN.mat'

        elif OUT is True:
            filename = 'PROCESSED_OUT.mat'

        # ==========================================================================
        # Matfile Saving
        # ==========================================================================
        sio.savemat(self.destination_folder + '/' + filename,

                    {'angular_position_SA': angular_position_SA,
                     'angular_position_SB': angular_position_SB,
                     'data_PD': data_PD,
                     'eccentricity': eccentricity,
                     'laser_position': laser_position,
                     'occlusion_position': occlusion_position,
                     'original_time_SB': original_time_SB,
                     'scan_number': scan_number,
                     'speed_SA': speed_SA,
                     'speed_SB': speed_SB,
                     'time_PD': time_PD,
                     'time_SA': time_SA,
                     'time_SB': time_SB},

                    do_compression=True)

        # log.log_file_saved(filename)

        if IN is True:
            filename = 'PROCESSED_IN.mat'
            self.notifyState.emit('done IN')
            time.sleep(0.1)
        elif OUT is True:
            filename = 'PROCESSED_OUT.mat'
            self.notifyState.emit('done OUT')
            time.sleep(0.1)


class ProcessCalibrationResults(QtCore.QThread):

    notifyProgress = QtCore.pyqtSignal(str)

    def __init__(self, folders, reference_folder=None, reference_file=None, tank_center=0, mean_fit=True, parent=None):

        self.reference_folder = reference_folder
        self.folders = folders
        self.reference_file = reference_file

        super(ProcessCalibrationResults, self).__init__(parent)

    def run(self):

        print('Calibration Results Processing')

        if self.reference_folder is not None:
            origin_file = self.reference_folder + '/mean_fit.mat'
            self.reference_file = self.reference_folder + '/mean_fit.mat'
        else:
            origin_file = 'None'

        for folder_name in self.folders:

            print('.processing' + folder_name)

            if os.path.exists(folder_name + '/PROCESSED_IN.mat'):

                self.notifyProgress.emit('Processing ' + folder_name.split('/')[::-1][0])

                newname = folder_name.split('file:///', 2)
                if len(newname) == 2:
                    folder_name = folder_name.split('file:///', 2)[1]

                parameter_file = utils.resource_path('data/parameters.cfg')
                config = configparser.RawConfigParser()
                config.read(parameter_file)
                positions_for_fit = eval(config.get('OPS processing parameters', 'positions_for_fit'))
                positions_for_analysis = eval(config.get('OPS processing parameters', 'positions_for_analysis'))
                tank_center = eval(config.get('OPS processing parameters', 'offset_center'))

                if self.reference_file is not None:
                    fit_file = sio.loadmat(self.reference_file, struct_as_record=False, squeeze_me=True)
                    origin_file = self.reference_file

                # IN

                filename = 'PROCESSED_IN.mat'

                data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
                occlusion_position = data['occlusion_position']
                laser_position = data['laser_position']
                idxs = np.argsort(laser_position)
                occlusion_position = occlusion_position[idxs]
                laser_position = laser_position[idxs]

                laser_position = -laser_position + tank_center

                unique_laser_position = np.unique(laser_position)
                occlusion_position_mean = []

                for laser_pos in unique_laser_position:
                    occlusion_position_mean.append(np.mean(occlusion_position[np.where(laser_position == laser_pos)[0]]))

                off1 = [int(positions_for_fit[0] / 100 * unique_laser_position.size),
                        int(positions_for_fit[1] / 100 * unique_laser_position.size)]

                occlusion_position_mean = np.asarray(occlusion_position_mean)
                popt, pcov = curve_fit(utils.theoretical_laser_position, occlusion_position_mean[off1[0]:off1[1]],
                                       unique_laser_position[off1[0]:off1[1]], bounds=([-10, 70, 90], [5, 1000, 1000]))

                theoretical_laser_position_mean = utils.theoretical_laser_position(occlusion_position_mean, popt[0], popt[1], popt[2])
                theoretical_laser_position = utils.theoretical_laser_position(occlusion_position, popt[0], popt[1], popt[2])

                if self.reference_file is not None:
                    theoretical_laser_position_origin = utils.theoretical_laser_position(occlusion_position, fit_file['f_parameters_IN'][0], fit_file['f_parameters_IN'][1], fit_file['f_parameters_IN'][2])
                    theoretical_laser_position_origin_mean = utils.theoretical_laser_position(occlusion_position_mean, fit_file['f_parameters_IN'][0], fit_file['f_parameters_IN'][1], fit_file['f_parameters_IN'][2])
                else:
                    theoretical_laser_position_origin = theoretical_laser_position
                    theoretical_laser_position_origin_mean = theoretical_laser_position_mean

                param = popt

                def theor_laser_position_i(y, a, b, c):
                    """
                     theoretical angular position of the wire in respect to the laser position
                     """
                    return np.pi + a - np.arccos((b - y) / c);

                center_IN = theor_laser_position_i(0, popt[0], popt[1], popt[2])
                f_parameters_IN = popt

                off2 = [int(positions_for_analysis[0] / 100 * laser_position.size),
                        int(positions_for_analysis[1] / 100 * laser_position.size)]

                laser_position = laser_position[off2[0]:off2[1]]
                theorical_laser_position = theoretical_laser_position[off2[0]:off2[1]]
                occlusion_position = occlusion_position[off2[0]:off2[1]]
                residuals = laser_position - theorical_laser_position
                residuals_mean = unique_laser_position - theoretical_laser_position_mean

                if self.reference_file is not None:
                    residuals_origin = laser_position - theoretical_laser_position_origin
                    residuals_origin_mean = unique_laser_position - theoretical_laser_position_origin_mean
                else:
                    residuals_origin = residuals
                    residuals_origin_mean = residuals_mean

                residuals = residuals[off2[0]:off2[1]]

                (mu, sigma) = norm.fit(residuals * 1e3)

                sigma_IN = sigma / np.sqrt(2)

                residuals_IN = residuals
                residuals_IN_origin = residuals_origin
                laser_position_IN = laser_position
                laser_position_IN_mean = unique_laser_position
                residuals_IN_mean = residuals_mean
                residuals_IN_origin_mean = residuals_origin_mean


                #####################################################
                # OUT
                ####################################################

                filename = 'PROCESSED_OUT.mat'

                data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
                occlusion_position = data['occlusion_position']
                laser_position = data['laser_position']
                idxs = np.argsort(laser_position)
                occlusion_position = occlusion_position[idxs]
                laser_position = laser_position[idxs]

                laser_position = -laser_position + tank_center

                occlusion_position = np.pi / 2 - occlusion_position

                unique_laser_position = np.unique(laser_position)
                occlusion_position_mean = []

                for laser_pos in unique_laser_position:
                    occlusion_position_mean.append(np.mean(occlusion_position[np.where(laser_position == laser_pos)[0]]))

                off1 = [int(positions_for_fit[0] / 100 * unique_laser_position.size),
                        int(positions_for_fit[1] / 100 * unique_laser_position.size)]

                occlusion_position_mean = np.asarray(occlusion_position_mean)
                popt, pcov = curve_fit(utils.theoretical_laser_position, occlusion_position_mean[off1[0]:off1[1]],
                                       unique_laser_position[off1[0]:off1[1]], bounds=([-10, 70, 90], [5, 1000, 1000]))

                theoretical_laser_position_mean = utils.theoretical_laser_position(occlusion_position_mean, popt[0], popt[1], popt[2])
                theorical_laser_position = utils.theoretical_laser_position(occlusion_position, popt[0], popt[1], popt[2])

                if self.reference_file is not None:
                    theoretical_laser_position_origin = utils.theoretical_laser_position(occlusion_position, fit_file['f_parameters_OUT'][0], fit_file['f_parameters_OUT'][1], fit_file['f_parameters_OUT'][2])
                    theoretical_laser_position_origin_mean = utils.theoretical_laser_position(occlusion_position_mean, fit_file['f_parameters_OUT'][0], fit_file['f_parameters_OUT'][1], fit_file['f_parameters_OUT'][2])
                    origin_file = self.reference_file
                else:
                    theoretical_laser_position_origin = theoretical_laser_position
                    theoretical_laser_position_origin_mean = theoretical_laser_position_mean

                param = popt

                def theor_laser_position_i(y, a, b, c):
                    return np.pi + a - np.arccos((b - y) / c);

                center_OUT = theor_laser_position_i(0, popt[0], popt[1], popt[2])
                f_parameters_OUT = popt

                off2 = [int(positions_for_analysis[0] / 100 * laser_position.size),
                        int(positions_for_analysis[1] / 100 * laser_position.size)]

                laser_position = laser_position[off2[0]:off2[1]]
                theoretical_laser_position = theorical_laser_position[off2[0]:off2[1]]
                occlusion_position = occlusion_position[off2[0]:off2[1]]
                residuals = laser_position - theorical_laser_position
                residuals_mean = unique_laser_position - theoretical_laser_position_mean

                if self.reference_file is not None:
                    residuals_origin = laser_position - theoretical_laser_position_origin
                    residuals_origin_mean = unique_laser_position - theoretical_laser_position_origin_mean
                else:
                    residuals_origin = residuals
                    residuals_origin_mean = residuals_mean

                residuals = residuals[off2[0]:off2[1]]
                residuals_OUT = residuals
                residuals_OUT_origin = residuals_origin
                residuals_OUT_mean = residuals_mean
                residuals_OUT_origin_mean = residuals_origin_mean

                (mu, sigma) = norm.fit(residuals * 1e3)

                sigma_OUT = sigma / np.sqrt(2)

                laser_position_OUT = laser_position
                laser_position_OUT_mean = unique_laser_position

                utils.create_results_file_from_calibration(folder_name=newname[0],
                                                           center_IN=center_IN,
                                                           center_OUT=center_OUT,
                                                           sigma_IN=sigma_IN,
                                                           sigma_OUT=sigma_OUT,
                                                           f_parameters_IN=f_parameters_IN,
                                                           f_parameters_OUT=f_parameters_OUT,
                                                           residuals_IN=residuals_IN,
                                                           residuals_IN_mean=residuals_IN_mean,
                                                           residuals_OUT=residuals_OUT,
                                                           residuals_OUT_mean=residuals_OUT_mean,
                                                           residuals_IN_origin=residuals_IN_origin,
                                                           residuals_IN_origin_mean=residuals_IN_origin_mean,
                                                           residuals_OUT_origin=residuals_OUT_origin,
                                                           residuals_OUT_origin_mean=residuals_OUT_origin_mean,
                                                           laser_position_IN=laser_position_IN,
                                                           laser_position_IN_mean=laser_position_IN_mean,
                                                           laser_position_OUT=laser_position_OUT,
                                                           laser_position_OUT_mean=laser_position_OUT_mean,
                                                           origin_file=origin_file)

            else:
                self.notifyProgress.emit(folder_name.split('/')[::-1][0] + ' not recognized as a PROCESSED folder')

        mean_fit_parameters(self.folders, folders_name=self.folders)

        self.notifyProgress.emit('Calibration results processing done!')