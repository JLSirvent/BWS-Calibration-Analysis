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
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d

import lib.utils as utils
from lib import diagnostic_tools as mplt

def process_position(data, parameter_file, StartTime, showplot=False, filename=None, return_processing=False,
                     camelback_threshold_on=True, INOUT = 'IN'):
    """
    Processing of the angular position based on the raw data of the OPS
    Credits : Jose Luis Sirvent (BE-BI-PM, CERN)
    """

    # Recuperation of processing parameters:
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    sampling_frequency = eval(config.get('OPS processing parameters', 'sampling_frequency'))
    SlitsperTurn = eval(config.get('OPS processing parameters', 'slits_per_turn'))
    rdcp = eval(config.get('OPS processing parameters', 'relative_distance_correction_prameters'))
    prominence = eval(config.get('OPS processing parameters', 'prominence'))
    #camelback_threshold = eval(config.get('OPS processing parameters', 'camelback_threshold'))
    OPS_processing_filter_freq = eval(config.get('OPS processing parameters', 'OPS_processing_filter_freq'))
    centroids = False
    References_Timming = eval(config.get('OPS processing parameters', 'References_Timming'))

    AngularIncrement = 2 * np.pi / SlitsperTurn

    # Data flip if analysing out scan (to always count from the same first reference found)
    if INOUT == 'OUT':
        data = np.flip(data,0)

    # Data Filtering
    data = utils.butter_lowpass_filter(data, OPS_processing_filter_freq, sampling_frequency, order=5)
    max_data = np.amax(data)

    # Data Normalization
    data = data - np.amin(data)
    data = data / max_data

    # start = time.time()

    # *** This is the part that takes most of the time!
    # Method A:
    # ---------
    # maxtab, mintab = utils.peakdet(data, prominence)
    # false = np.where(mintab[:, 1] > np.mean(maxtab[:, 1]))
    # mintab = np.delete(mintab, false, 0)
    #
    # locs_up = np.array(maxtab)[:, 0]
    # pck_up = np.array(maxtab)[:, 1]
    #
    # locs_dwn = np.array(mintab)[:, 0]
    # pck_dwn = np.array(mintab)[:, 1]


    # Method B: Seems Faster
    # ----------------------
    locs_up, _ = find_peaks(data, prominence = prominence)
    locs_dwn, _ = find_peaks(-data + 1, prominence = prominence)
    pck_up = data[locs_up]
    pck_dwn = data[locs_dwn]

    todelete = np.where(pck_dwn>np.mean(pck_up))
    locs_dwn = np.delete(locs_dwn,todelete,0)
    pck_dwn = np.delete(pck_dwn,todelete,0)

    # end = time.time()
    # print('Filter T: ')
    # print(end - start)

    LengthMin = np.minimum(pck_up.size, pck_dwn.size)

    # Crosing position evaluation
    Crosingpos = np.ones((2, LengthMin))
    Crosingpos[1][:] = np.arange(1, LengthMin + 1)

    if centroids == True:
        # ==========================================================================
        # Position processing based on centroids
        # ==========================================================================
        Crosingpos[0][:] = locs_dwn[0:LengthMin]
        A = np.ones(LengthMin)
    else:
        # ==========================================================================
        # Position processing based on crossing points: Rising edges only
        # ==========================================================================
        IndexDwn = 0
        IndexUp = 0
        A = []

        # Position calculation loop: OLD METHOD
        # for i in range(0, LengthMin - 1):
        #
        #     # Ensure crossing point in rising edge (locs_dwn < locs_up)
        #     while locs_dwn[IndexDwn] >= locs_up[IndexUp]:
        #         IndexUp += 1
        #
        #     while locs_dwn[IndexDwn + 1] < locs_up[IndexUp]:
        #         IndexDwn += 1
        #
        #     # Calculate thresshold for current window: Mean point
        #     Threshold = (data[int(locs_dwn[IndexDwn])] + data[int(locs_up[IndexUp])]) / 2
        #     # Find time on crossing point:
        #     b = int(locs_dwn[IndexDwn]) + np.where(data[int(locs_dwn[IndexDwn]):int(locs_up[IndexUp])] >= Threshold)[0][0]
        #     idx_n = np.where(data[int(locs_dwn[IndexDwn]):int(locs_up[IndexUp])] < Threshold)[0]
        #     idx_n = idx_n[::-1][0]
        #     a = int(locs_dwn[IndexDwn]) + idx_n
        #
        #     Crosingpos[0, i] = (Threshold - data[int(a)]) * (b - a) / (data[int(b)] - data[int(a)]) + a
        #
        #     # if showplot is True or showplot is 1:
        #     A = np.append(A, Threshold)
        #
        #     # Move to next window:
        #     IndexDwn = IndexDwn + 1
        #     IndexUp = IndexUp + 1

        # Position calculation loop: New Method
        for i in range(0,LengthMin-1):
            Idx_dwn = locs_dwn[i]
            Idx = np.where(locs_up>locs_dwn[i])[0][0]
            Idx_up = locs_up[Idx]
            Thesshold = (data[Idx_dwn]+data[Idx_up])/2
            b = np.where(data[Idx_dwn:Idx_up] >= Thesshold)[0][0] + Idx_dwn
            a = b-1
            Crosingpos[0, i] = (Thesshold - data[int(a)]) * (b - a) / (data[int(b)] - data[int(a)]) + a
            A = np.append(A, Thesshold)
        print('out of the loop')

    # ==========================================================================
    # Position loss compensation
    # ==========================================================================
    # Un-corrected position and time
    Data_Time = Crosingpos[0][:] * 1 / sampling_frequency
    Data_Pos = Crosingpos[1][:] * AngularIncrement

    # Relative-distances method for slit-loss compensation:
    Distances = np.diff(Crosingpos[0][0:Crosingpos.size - 1])

    # Method 2: Considering average of several previous periods
    previous_periods = 4
    cnt = 0
    DistancesAVG = []

    for i in range(previous_periods,len(Distances)):
        DistancesAVG.append(np.mean(Distances[i-previous_periods:i]))

    RelDistr = np.divide(Distances[previous_periods:len(Distances)], DistancesAVG)

    # Method 1: Only consider previous transition
    #RelDistr = np.divide(Distances[1:Distances.size], Distances[0:Distances.size - 1])

    # Search of compensation points:
    PointsCompensation = np.where(RelDistr >= rdcp[0])[0]

    for b in np.arange(0, PointsCompensation.size):

        if RelDistr[PointsCompensation[b]] >= rdcp[2]:
            # These are the references (metallic disk) or 3 slit loses
            Data_Pos[(PointsCompensation[b] + 1 + previous_periods):Data_Pos.size] = Data_Pos[(
                PointsCompensation[b] + 1 + previous_periods):Data_Pos.size] + 3 * AngularIncrement

        elif RelDistr[PointsCompensation[b]] >= rdcp[1]:
            # These are 2 slit loses
            Data_Pos[(PointsCompensation[b] + 1 + previous_periods):Data_Pos.size] = Data_Pos[(
                PointsCompensation[b] + 1 + previous_periods):Data_Pos.size] + 2 * AngularIncrement

        elif RelDistr[PointsCompensation[b]] >= rdcp[0]:
            # These are 1 slit losses
            Data_Pos[(PointsCompensation[b] + 1 + previous_periods):Data_Pos.size] = Data_Pos[(
                PointsCompensation[b] + 1 + previous_periods):Data_Pos.size] + 1 * AngularIncrement

    # ==========================================================================
    # Alignment to First reference and Storage
    # ==========================================================================

    if StartTime > References_Timming[0] / 1000:
        # This is the OUT
        Rtiming = References_Timming[1]
        Offset = np.where(((StartTime + len(data)/sampling_frequency) - Data_Time[0:Data_Time.size - 1]) < (Rtiming / 1000))[0][0]
    else:
        # This is the IN
        Rtiming = References_Timming[0]
        Offset = np.where(Data_Time[0:Data_Time.size - 1] + StartTime > (Rtiming / 1000))[0][0]

    try:
        _IndexRef1 = Offset + np.where(RelDistr[Offset:LengthMin - Offset] > rdcp[1])[0]
        IndexRef1 = _IndexRef1[0]
        Data_Pos = Data_Pos - Data_Pos[IndexRef1]
    except:
        IndexRef1 = 0
        print('Disk Reference not found!')

    Data = np.ndarray((2, Data_Pos.size - 1))

    if INOUT == 'OUT':
        Data[0] = 1e3 * ((StartTime + len(data)/sampling_frequency) - Data_Time[0:Data_Time.size - 1])
    else:
        Data[0] = 1e3*(Data_Time[0:Data_Time.size - 1] + StartTime)

    Data[1] = Data_Pos[0:Data_Pos.size - 1]


    # ==========================================================================
    # Plotting script
    # ==========================================================================
    # if showplot is True or showplot is 1:
    #     fig = plt.figure(figsize=(11, 5))
    #     ax1 = fig.add_subplot(111)
    #     mplt.make_it_nice(ax1)
    #     plt.axhspan(0, threshold_reference / max_data, color='black', alpha=0.1)
    #     plt.axvspan(1e3 * StartTime + 1e3 * (data.size * 1 / 4) / sampling_frequency,
    #                 1e3 * StartTime + 1e3 * (data.size * 3 / 4) / sampling_frequency, color='black', alpha=0.1)
    #     plt.plot(1e3 * StartTime + 1e3 * np.arange(0, data.size) * 1 / sampling_frequency, data, linewidth=0.5)
    #     plt.plot(1e3 * StartTime + 1e3 * locs_up * 1 / sampling_frequency, pck_up, '.', MarkerSize=1.5)
    #     plt.plot(1e3 * StartTime + 1e3 * locs_dwn * 1 / sampling_frequency, pck_dwn, '.', MarkerSize=1.5)
    #     plt.plot(1e3 * StartTime + 1e3 * Crosingpos[0][0:A.size] * 1 / sampling_frequency, A, linewidth=0.5)
    #     ax1.set_title('Optical position sensor processing', loc='left')
    #     ax1.set_xlabel('Time (um)')
    #     ax1.set_ylabel('Normalized amplitude of signal (A.U.)')
    #     plt.show(block=False)
    # # plt.plot(1e3*StartTime+1e3*IndexRef1*1/sampling_frequency + StartTime, data[IndexRef1], 'x')
    # #        plt.plot(1e3*StartTime+1e3*np.arange(1,Distances.size)*1/sampling_frequency + StartTime, RelDistr, '.')


    if return_processing is True:
        if INOUT == 'OUT':
            return [1e3 * (StartTime + len(data)/sampling_frequency) - 1e3 * np.arange(0, data.size) * 1 / sampling_frequency, data,
                    1e3 * (StartTime + len(data)/sampling_frequency) - 1e3 * locs_up * 1 / sampling_frequency, pck_up,
                    1e3 * (StartTime + len(data)/sampling_frequency) - 1e3 * locs_dwn * 1 / sampling_frequency, pck_dwn,
                    1e3 * (StartTime + len(data)/sampling_frequency) - 1e3 * Crosingpos[0][0:A.size] * 1 / sampling_frequency, A,
                    1 / max_data,
                    1e3 * (StartTime + len(data)/sampling_frequency) - 1e3 * Crosingpos[0][IndexRef1] * (1 / sampling_frequency),
                    Data]
        else:
            return [1e3 * StartTime + 1e3 * np.arange(0, data.size) * 1 / sampling_frequency, data,
                    1e3 * StartTime + 1e3 * locs_up * 1 / sampling_frequency, pck_up,
                    1e3 * StartTime + 1e3 * locs_dwn * 1 / sampling_frequency, pck_dwn,
                    1e3 * StartTime + 1e3 * Crosingpos[0][0:A.size] * 1 / sampling_frequency, A,
                    1 / max_data,
                    1e3 * StartTime + 1e3 * Crosingpos[0][IndexRef1] * (1 / sampling_frequency),
                    Data]
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
    #parameter_file = utils.resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read('data/parameters.cfg')
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
        indexvalmax = np.where(filtered_data == valmax)[0][0]
        indexleft = indexvalmax - np.int((margin / 2) * sampling_frequency)
        indexright = indexvalmax + np.int((margin / 2) * sampling_frequency)
        filtered_data_short = filtered_data[indexleft:indexright]
        # -----
        # Method 1
        #pcks = utils.peakdet(filtered_data_short, valmax / 4)[0]
        #pcks = np.transpose(pcks)

        # Method 2 (faster?)
        pcks = find_peaks(filtered_data_short, prominence = valmax/4)[0]
        locs = pcks + indexleft

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

class ProcessRawDataV2(QtCore.QThread):

    notifyProgress = QtCore.pyqtSignal(int)
    notifyState = QtCore.pyqtSignal(str)
    notifyFile = QtCore.pyqtSignal(str)

    def __init__(self, raw_data_folder, destination_folder, verbose=False, parent=None):

        self.raw_data_folder = raw_data_folder
        self.destination_folder = destination_folder
        self.verbose = verbose
        super(ProcessRawDataV2, self).__init__(parent)

    def run(self):

        # ==========================================================================
        # Variables and parameters definiton
        # ==========================================================================
        angular_position_SA_in = []
        angular_position_SB_in = []
        eccentricity_in = []
        occlusion_position_in = []
        oc_in = []
        data_valid_in = []
        speed_SA_in = []
        speed_SB_in = []
        time_SA_in = []
        time_SB_in = []

        angular_position_SA_out = []
        angular_position_SB_out = []
        eccentricity_out = []
        occlusion_position_out = []
        oc_out = []
        data_valid_out = []
        speed_SA_out = []
        speed_SB_out = []
        time_SA_out = []
        time_SB_out = []

        laser_position = []
        scan_number = []

        # We use a parameter file
        #parameter_file = utils.resource_path('data/parameters.cfg')
        config = configparser.RawConfigParser()
        config.read('data/parameters.cfg')
        sampling_frequency = eval(config.get('OPS processing parameters', 'sampling_frequency'))
        process_occlusions = eval(config.get('OPS processing parameters','Process_Occlusions'))
        compensate_eccentricity = eval(config.get('OPS processing parameters','Compensate_Eccentricity'))
        tank_centre = eval(config.get('Geometry','stages_position_at_tank_center'))

        print('------- Processing Calibration -------')
        self.notifyState.emit('Processing Calibration...')
        # ==========================================================================
        # Main processing loop
        # ==========================================================================

        i = 0

        tdms_files = utils.tdms_list_from_folder_sorted(self.raw_data_folder)

        for tdms_file in tqdm(tdms_files):

            if self.verbose is True:
                print(tdms_file)

            self.notifyProgress.emit(int(i * 100 / len(tdms_files)))
            #time.sleep(0.1)

            self.notifyFile.emit(tdms_file)
            #time.sleep(0.1)

            # Laser position and scan number extraction from file name and saving in list
            _laser_position, _scan_number = utils.find_scan_info(tdms_file)
            scan_number.append(int(_scan_number))
            laser_position.append(float(_laser_position))
            start = time.time()
            data__s_a_in, data__s_b_in, data__s_a_out, data__s_b_out, data__p_d_in, data__p_d_out, time__in, time__out = utils.extract_from_tdms(tdms_file)
            end = time.time()
            print('Loadtime')
            print(end-start)

            start= time.time()
            for s in range(0,2):
                try:
                    if s == 0:
                        _data_SA = data__s_a_in
                        _data_SB = data__s_b_in
                        _data_PD = data__p_d_in
                        StartTime = time__in[0]
                        scantype = 'IN'
                        IN = True
                    else:
                        _data_SA = data__s_a_out
                        _data_SB = data__s_b_out
                        _data_PD = data__p_d_out
                        StartTime = time__out[0]
                        scantype = 'OUT'
                        IN = False

                    Data_SA = process_position(_data_SA, 'data/parameters.cfg', StartTime, showplot=0, INOUT= scantype)
                    Data_SB_O = process_position(_data_SB, 'data/parameters.cfg', StartTime, showplot=0, INOUT= scantype)
                    Data_SB_R = utils.resample(Data_SB_O, Data_SA)

                    # Eccentricity from OPS processing and saving in list
                    _eccentricity = np.subtract(Data_SA[1], Data_SB_R[1]) / 2

                    # Decide Eccentricity compensation or not
                    # ---------------------------------------
                    if compensate_eccentricity is True:
                        Data_SA[1] = np.subtract(Data_SA[1], _eccentricity)
                        Data_SB    = [Data_SA[0], np.subtract(Data_SB_R[1], -_eccentricity)]
                    else:
                        Data_SB = Data_SB_O
                    # ---------------------------------------

                    # OPS speed processing
                    _speed_SA = np.divide(np.diff(Data_SA[1]), np.diff(Data_SA[0]))
                    _speed_SB = np.divide(np.diff(Data_SB[1]), np.diff(Data_SB[0]))

                    # Finding of occlusions and saving into a list
                    if process_occlusions is True:

                        _time_PD = StartTime + np.arange(0, _data_PD.size) * 1 / sampling_frequency
                        _time_PD = 1e3*_time_PD

                        occlusions = find_occlusions(_data_PD, IN)

                        # -- New Method: Slightly faster --
                        finterp = interp1d(Data_SA[0],Data_SA[1])
                        occ1 = finterp(_time_PD[int(occlusions[0])])
                        occ2 = finterp(_time_PD[int(occlusions[1])])
                        # -----------------

                        _occlusion = (occ2 - occ1) / 2 + occ1
                        _oc = [occ1, occ2]

                    else:
                        _occlusion = StartTime + 0.02

                    if s==0:
                        eccentricity_in.append(_eccentricity)
                        angular_position_SA_in.append(Data_SA[1])
                        angular_position_SB_in.append(Data_SB[1])
                        time_SA_in.append(Data_SA[0])
                        time_SB_in.append(Data_SB[0])
                        speed_SA_in.append(_speed_SA)
                        speed_SB_in.append(_speed_SB)
                        occlusion_position_in.append(_occlusion)
                        oc_in.append(_oc)
                        data_valid_in.append(1)
                    else:
                        eccentricity_out.append(_eccentricity)
                        angular_position_SA_out.append(Data_SA[1])
                        angular_position_SB_out.append(Data_SB[1])
                        time_SA_out.append(Data_SA[0])
                        time_SB_out.append(Data_SB[0])
                        speed_SA_out.append(_speed_SA)
                        speed_SB_out.append(_speed_SB)
                        occlusion_position_out.append(_occlusion)
                        oc_out.append(_oc)
                        data_valid_out.append(1)
                except:

                    if s == 0:
                        eccentricity_in.append([0,1])
                        angular_position_SA_in.append([0,1])
                        angular_position_SB_in.append([0,1])
                        time_SA_in.append([0,1])
                        time_SB_in.append([0,1])
                        speed_SA_in.append([0,1])
                        speed_SB_in.append([0,1])
                        occlusion_position_in.append(0)
                        oc_in.append([0,0])
                        data_valid_in.append(0)
                        self.notifyState.emit("Error in file IN:" + tdms_file)
                        self.notifyProgress.emit("Error in file IN:" + tdms_file)
                        print("Error in file IN:" + tdms_file)
                    else:
                        eccentricity_out.append([0,1])
                        angular_position_SA_out.append([0,1])
                        angular_position_SB_out.append([0,1])
                        time_SA_out.append([0,1])
                        time_SB_out.append([0,1])
                        speed_SA_out.append([0,1])
                        speed_SB_out.append([0,1])
                        occlusion_position_out.append(0)
                        oc_out.append(_oc)
                        data_valid_out.append(0)
                        self.notifyState.emit("Error in file OUT:" + tdms_file)
                        self.notifyProgress.emit("Error in file OUT:" + tdms_file)
                        print("Error in file OUT:" + tdms_file)

            i += 1
            end = time.time()
            print('Processtime')
            print(end-start)

        # Before saving --> Normalize positions wrt tank center
        laser_position = tank_centre - np.asarray(laser_position)

        # ==========================================================================
        # Matfile Saving
        # ==========================================================================
        sio.savemat(self.destination_folder + '/PROCESSED_IN.mat',
                    {'angular_position_SA': angular_position_SA_in,
                     'angular_position_SB': angular_position_SB_in,
                     'eccentricity': eccentricity_in,
                     'laser_position': laser_position,
                     'occlusion_position': occlusion_position_in,
                     'oc': oc_in,
                     'data_valid': data_valid_in,
                     'scan_number': scan_number,
                     'speed_SA': speed_SA_in,
                     'speed_SB': speed_SB_in,
                     'time_SA': time_SA_in,
                     'time_SB': time_SB_in},
                    do_compression=True)

        sio.savemat(self.destination_folder + '/PROCESSED_OUT.mat',
                    {'angular_position_SA': angular_position_SA_out,
                     'angular_position_SB': angular_position_SB_out,
                     'eccentricity': eccentricity_out,
                     'laser_position': laser_position,
                     'occlusion_position': occlusion_position_out,
                     'oc': oc_out,
                     'data_valid': data_valid_out,
                     'scan_number': scan_number,
                     'speed_SA': speed_SA_out,
                     'speed_SB': speed_SB_out,
                     'time_SA': time_SA_out,
                     'time_SB': time_SB_out},
                    do_compression=True)

        self.notifyState.emit('Calibration Processed!')
        #time.sleep(0.1)


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

                #parameter_file = utils.resource_path('data/parameters.cfg')
                config = configparser.RawConfigParser()
                config.read('data/parameters.cfg')
                positions_for_fit = eval(config.get('OPS processing parameters', 'positions_for_fit'))
                positions_for_analysis = eval(config.get('OPS processing parameters', 'positions_for_analysis'))
                tank_center = eval(config.get('Geometry', 'stages_position_at_tank_center'))

                if self.reference_file is not None:
                    fit_file = sio.loadmat(self.reference_file, struct_as_record=False, squeeze_me=True)
                    origin_file = self.reference_file

                # IN

                filename = 'PROCESSED_IN.mat'

                data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
                occlusion_position = data['occlusion_position']
                laser_position = data['laser_position']
                try:
                    data_valid = data['data_valid']
                except:
                    data_valid = np.ones(laser_position.size)

                laser_position=laser_position[np.where(data_valid == 1)]
                occlusion_position = occlusion_position[np.where(data_valid == 1)]

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

                try:
                    data_valid = data['data_valid']
                except:
                    data_valid = np.ones(laser_position.size)

                laser_position = laser_position[np.where(data_valid == 1)]
                occlusion_position = occlusion_position[np.where(data_valid == 1)]

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