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
import glob
import sys
import time
import shutil
import numpy as np
import configparser
import scipy.io as sio
import scipy.signal as signal
import PyQt5.QtCore as QtCore

from os import walk
from tqdm import tqdm
from nptdms import TdmsFile
from scipy.interpolate import interp1d
from numpy import NaN, Inf, arange, isscalar, asarray, array

from lib import utils


def butter_lowpass(cutoff, fs, order=5):
    """
    Matlab butter style filter design
    """
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order=5):
    """
    Low pass filtering of data using butter filter
    """
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = signal.filtfilt(b, a, data)
    return y


def peakdet(v, delta, x=None):
    """
    Peak detection algorithm based on pseudo-prominence criteria

    Converted from MATLAB script at http://billauer.co.il/peakdet.html

    Returns two arrays

    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.

    Credits : Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    This function is released to the public domain; Any use is allowed.
    """
    maxtab = []
    mintab = []

    if x is None:
        x = arange(len(v))

    v = asarray(v)

    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')

    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')

    if delta <= 0:
        sys.exit('Input argument delta must be positive')

    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN

    lookformax = True

    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]

        if lookformax:
            if this < mx - delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn + delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return array(maxtab), array(mintab)


def open_mat(matfile):
    """
    Load a mat file and return its strucuture into a dictionnary
    """

    mat = h5py.File('data/' + matfile)
    arrays = {}

    for k, v in mat.items():
        arrays[k] = np.array(v)

    return arrays

def tdms_list_from_folder_sorted(TDMS_folder):
    newname = TDMS_folder.split('file:///', 2)

    if len(newname) == 2:
        TDMS_folder = TDMS_folder.split('file:///', 2)[1]

    if not os.path.exists(TDMS_folder):
        return -1

    tdms_files = glob.glob(TDMS_folder + '/*.tdms')
    tdms_files.sort(key=os.path.getmtime)

    if len(tdms_files) < 1:
        tdms_files =  -1

    return tdms_files


def tdms_list_from_folder(TDMS_folder):
    newname = TDMS_folder.split('file:///', 2)

    if len(newname) == 2:
        TDMS_folder = TDMS_folder.split('file:///', 2)[1]

    if not os.path.exists(TDMS_folder):
        return -1

    tdms_files = []

    for (dir_path, dir_names, file_names) in walk(TDMS_folder):
        for files in file_names:
            if files.endswith(('.tdms', '.TDMS')):
                tdms_files.append(files)

    if len(tdms_files) < 1:
        tdms_files = -1
        dir_path = -1

        return -1
    print()
    return tdms_files, dir_path

def mat_list_from_folder_sorted(mat_folder):

    new_name = mat_folder.split('file:///', 2)

    if len(new_name) == 2:
        mat_folder = mat_folder.split('file:///', 2)[1]

    mat_files = glob.glob(mat_folder + '/*.mat')
    mat_files.sort(key=os.path.getmtime)

    return mat_files

def mat_list_from_folder(mat_folder):
    new_name = mat_folder.split('file:///', 2)

    if len(new_name) == 2:
        mat_folder = mat_folder.split('file:///', 2)[1]

    mat_files = []

    for (dir_path, dir_names, file_names) in walk(mat_folder):
        for files in file_names:
            if files.endswith(('.mat', '.Mat')):
                mat_files.append(files)

    return mat_files, dir_path

class CreateRawDataFolder(QtCore.QThread):
    """
    Creation of a folder containing the raw data saved as .mat files. Raw data
    are saved in data/RAW_DATA and separated in respect to IN and OUT scans.

    The .mat file contains:
        - data_SA : Raw data comming from disk sensor A
        - data_SB : Raw data comming from disk sensor B
        - data_PD : Raw data comming from the photodiode
        - time_PD : Global time (range from 0 to size of data_PD)

    IN and OUT scans are separated following the parameters described in:
        data/parameters.mat

    """

    notifyProgress = QtCore.pyqtSignal(int)
    notifyState = QtCore.pyqtSignal(str)
    notifyFile = QtCore.pyqtSignal(str)

    def __init__(self, TDMS_folder, destination_folder, parent = None):
        self.TDMS_folder = TDMS_folder
        self.destination_folder = destination_folder
        super(CreateRawDataFolder, self).__init__(parent)

    def run(self):

        parameter_file = utils.resource_path('data/parameters.cfg')
        config = configparser.RawConfigParser()
        config.read(parameter_file)
        tdms_minimum_size = eval(config.get('OPS processing parameters', 'tdms_minimum_size'))
        fatigue_test = config.get('OPS processing parameters', 'fatigue_test')
        offset_center = eval(config.get('Geometry', 'stages_position_at_tank_center'))
        newname = self.TDMS_folder.split('file:///', 2)

        if len(newname) == 2:
            TDMS_folder = self.TDMS_folder.split('file:///', 2)[1]

        print('------- TDMS Conversion -------')

        self.notifyState.emit('TDMS conversion')
        time.sleep(0.3)

        if os.path.exists(self.destination_folder + '/RAW_DATA'):
            shutil.rmtree(self.destination_folder + '/RAW_DATA')
            time.sleep(3)
        os.makedirs(self.destination_folder + '/RAW_DATA')
        os.makedirs(self.destination_folder + '/RAW_DATA/RAW_IN')
        os.makedirs(self.destination_folder + '/RAW_DATA/RAW_OUT')

        speed = 133

        false = 0

        #tdms_files, dir_path = tdms_list_from_folder(self.TDMS_folder)
        tdms_files = tdms_list_from_folder_sorted(self.TDMS_folder)

        # log.log_new_raw_data_extraction(self.TDMS_folder, speed)

        i=0

        for tdms_file in tqdm(tdms_files):

            self.notifyProgress.emit(int(i*100 / len(tdms_files)))
            time.sleep(0.1)
            self.notifyFile.emit(tdms_file)
            time.sleep(0.1)

            # We take only file that are well saved - parameter to be found in config file
            #if os.path.getsize(dir_path + '/' + tdms_file) >= tdms_minimum_size:
            if os.path.getsize(tdms_file) >= tdms_minimum_size:

                if fatigue_test == 'yes':
                    laser_position = offset_center
                    scan_number = int(eval(tdms_file.split('__', 2)[1]))

                else:
                    laser_position, scan_number = find_scan_info(tdms_file)
                    if laser_position == -1:
                        laser_position = offset_center
                        scan_number = int(eval(tdms_file.split('__', 2)[1]))

                #data__s_a_in, data__s_b_in, data__s_a_out, data__s_b_out, data__p_d_in, data__p_d_out, time__in, time__out = utils.extract_from_tdms(dir_path + '/' + tdms_file)
                data__s_a_in, data__s_b_in, data__s_a_out, data__s_b_out, data__p_d_in, data__p_d_out, time__in, time__out = utils.extract_from_tdms(tdms_file)


                if type(data__s_a_in) is not int:

                    sio.savemat(self.destination_folder + '/RAW_DATA/RAW_IN/SCAN__P'
                                + str(laser_position)
                                + '__S' + str(scan_number)
                                + '____IN.mat',

                                dict(data_SA=data__s_a_in, data_SB=data__s_b_in, data_PD=data__p_d_in, speed=speed, INorOUT='IN'))

                    sio.savemat(self.destination_folder + '/RAW_DATA/RAW_OUT/SCAN__P'
                                + str(laser_position)
                                + '__S' + str(scan_number)
                                + '____OUT.mat',

                                dict(data_SA=data__s_a_out, data_SB=data__s_b_out, data_PD=data__p_d_out, speed=speed, INorOUT='OUT'))
            else:
                false = false + 1

            if false > 15:
                self.parent().parent.LogDialog.add('High number of files identified as defective - Please check tdms_minimum_size_ in [LabView output] parameters', 'error')

            i += 1

        self.notifyState.emit('done convert')
        time.sleep(0.1)


def resample(data_B, data_A):
    """
    Resample data_B ([timeB][dataB]) wrt data_A time ([timeA][dataB])
    and return resampled_data_B([timeA][resampleddataB]))
    """
    data_SB_interp = interp1d(data_B[0], data_B[1], bounds_error=False, fill_value=0)
    data_B_R = np.ones((2, data_A[0].size))
    data_B_R[1] = data_SB_interp(data_A[0])
    data_B_R[0] = np.copy(data_A[0])

    return data_B_R


def find_scan_info(filename,  position = '__P', scan = '__S', date = '____'):
    """
    Find laser position and scan number by looking at the file name
    """
    try:
        file = filename.split(position, 2)

        file = file[1].split(scan, 2)
        laser_position = file[0]

        file = file[1].split(date, 2)
        scan_number = file[0]
    except IndexError:
        laser_position = -1
        scan_number = -1

    return laser_position, scan_number


def create_processed_data_folder(raw_data_folder, destination_folder=None, force_overwrite='n'):

    if destination_folder is not None:
        # print('ola')
        # time.sleep(5)
        filename = os.path.basename(raw_data_folder)
        filename = filename.split('TDMS', 2)[0]

        folder_name = destination_folder + '/' + filename + ' PROCESSED'
        # print('ola')
        # time.sleep(5)

        if os.path.exists(folder_name):

            if force_overwrite is 'y':
                shutil.rmtree(folder_name)
                time.sleep(3)

            elif force_overwrite is 'n':
                overwrite = input(
                    'You are about to overwrite data from' + filename + 'previous processing. Do you want to continue ? [y/n]')
                if overwrite is 'y':
                    shutil.rmtree(folder_name)
                    time.sleep(3)

        os.makedirs(folder_name)

        if os.path.exists(destination_folder + '/PROCESSED_IN.mat'):
            shutil.move(destination_folder + '/PROCESSED_IN.mat', folder_name)
        else:
            print('PROCESSED_IN.mat does not exists in data')

        if os.path.exists(destination_folder + '/PROCESSED_OUT.mat'):
            shutil.move(destination_folder + '/PROCESSED_OUT.mat', folder_name)
        else:
            print('PROCESSED_OUT.mat does not exists in data')

        if os.path.exists(destination_folder + '/RAW_DATA'):
            shutil.rmtree(destination_folder + '/RAW_DATA')

    else:
        filename = os.path.basename(raw_data_folder)
        filename = filename.split('TDMS', 2)[0]

        folder_name = '../data/' + filename + ' PROCESSED'

        if os.path.exists(folder_name):

            if force_overwrite is 'y':
                shutil.rmtree(folder_name)
                time.sleep(3)

            elif force_overwrite is 'n':
                overwrite = input(
                    'You are about to overwrite data from' + filename + 'previous processing. Do you want to continue ? [y/n]')
                if overwrite is 'y':
                    shutil.rmtree(folder_name)
                    time.sleep(3)

        os.makedirs(folder_name)

        if os.path.exists('data/PROCESSED_IN.mat'):
            shutil.move('data/PROCESSED_IN.mat', folder_name)
        else:
            print('PROCESSED_IN.mat does not exists in data')

        if os.path.exists('data/PROCESSED_OUT.mat'):
            shutil.move('data/PROCESSED_OUT.mat', folder_name)
        else:
            print('PROCESSED_OUT.mat does not exists in data')

        if os.path.exists('data/RAW_DATA'):
            shutil.rmtree('data/RAW_DATA')


def create_results_file_from_calibration(folder_name, center_IN, center_OUT, sigma_IN, sigma_OUT, f_parameters_IN,
                                         f_parameters_OUT, residuals_IN, residuals_OUT, residuals_IN_origin,
                                         residuals_OUT_origin, laser_position_IN, laser_position_OUT,
                                         origin_file, residuals_IN_origin_mean, residuals_OUT_origin_mean,
                                         laser_position_IN_mean, laser_position_OUT_mean, residuals_IN_mean,
                                         residuals_OUT_mean):

    saving_name = folder_name + '/calibration_results.mat'

    sio.savemat(saving_name,

                dict(center_IN=center_IN,
                     center_OUT=center_OUT,
                     sigma_IN=sigma_IN,
                     sigma_OUT=sigma_OUT,
                     f_parameters_IN=f_parameters_IN,
                     f_parameters_OUT=f_parameters_OUT,
                     residuals_IN=residuals_IN,
                     residuals_OUT=residuals_OUT,
                     residuals_IN_origin=residuals_IN_origin,
                     residuals_OUT_origin=residuals_OUT_origin,
                     laser_position_IN=laser_position_IN,
                     laser_position_OUT=laser_position_OUT,
                     f='b - c * np.cos(np.pi - x + a)',
                     origin_file=origin_file,
                     residuals_OUT_mean=residuals_OUT_mean,
                     residuals_IN_origin_mean=residuals_IN_origin_mean,
                     residuals_OUT_origin_mean=residuals_OUT_origin_mean,
                     laser_position_IN_mean=laser_position_IN_mean,
                     laser_position_OUT_mean=laser_position_OUT_mean))


def theoretical_laser_position(x, a, b, c):
    """
    theoretical angular position of the wire in respect to the laser position
    """
    return b - c * np.cos(np.pi - x + a);


def inverse_theoretical_laser_position(y, a, b, c):
    """
     theoretical angular position of the wire in respect to the laser position
     """
    return np.pi + a - np.arccos((b - y) / c)


def python_lines(folder):
    py_files = []

    number_of_lines = 0

    for (dir_path, dir_names, file_names) in walk(folder):
        for files in file_names:
            if files.endswith('.py'):
                py_files.append(dir_path + '/' + files)

    for py_file in py_files:
        f = open(py_file, 'r')
        lines = f.readlines()
        number_of_lines += len(lines)

    return number_of_lines


def reformate_path(path):
    """On certain editors (e.g. Spyder on Windows) a copy-paste of the path from the explorer includes a 'file:///'
    attribute before the real path. This function removes this extra piece
    Args:
        path: original path

    Returns:
        Reformatted path
    """

    _path = path.split('file:///', 2)

    if len(_path) == 2:
        new_path = path.split('file:///', 2)[1]
    else:
        new_path = path

    return new_path


def extract_from_tdms(path):
    file = reformate_path(path)
    tdms_file = TdmsFile(file)

    parameter_file = resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)

    sampling_frequency = eval(config.get('OPS processing parameters', 'sampling_frequency'))

    data__s_a_name = eval(config.get('LabView output', 'data_SA'))
    data__s_b_name = eval(config.get('LabView output', 'data_SB'))
    data__p_d_name = eval(config.get('LabView output', 'data_PD'))
    automatic_ranging_name = eval(config.get('LabView output', 'automatic_ranging'))

    range_time_in = eval(config.get('OPS processing parameters', 'IN_range'))
    range_time_out = eval(config.get('OPS processing parameters', 'OUT_range'))



    if len(data__s_a_name) == 2:

        try:

            auto_range = tdms_file.object('Picoscope Data', automatic_ranging_name).data/sampling_frequency

            try:

                if range_time_in is 'auto':
                    range_time_in = np.asarray([auto_range[0], auto_range[1]])
                    range_in = np.arange(0, (range_time_in[1] - range_time_in[0]) * sampling_frequency - 1).astype(int)
                else:
                    glo_range_in = auto_range[1] - auto_range[0]
                    diff_range_in = np.abs((range_time_in[1] - auto_range[1]))
                    range_in = np.arange((range_time_in[0] - auto_range[0]) * sampling_frequency,
                                         (glo_range_in - diff_range_in) * sampling_frequency).astype(int) - 1

                if range_time_out is 'auto':
                    range_time_out = np.asarray([auto_range[2], auto_range[3]])
                    range_out = np.arange(0, (range_time_out[1] - range_time_out[0]) * sampling_frequency - 1).astype(
                        int)
                else:
                    glo_range_out = auto_range[3] - auto_range[2]
                    diff_range_out = np.abs((range_time_out[1] - auto_range[3]))
                    range_out = np.arange((range_time_out[0] - auto_range[2]) * sampling_frequency,
                                          (glo_range_out - diff_range_out) * sampling_frequency).astype(int) - 1

                data__s_a_in = tdms_file.object('Picoscope Data', data__s_a_name[0]).data[range_in]
                data__s_a_out = tdms_file.object('Picoscope Data', data__s_a_name[1]).data[range_out]
                data__s_b_in = tdms_file.object('Picoscope Data', data__s_b_name[0]).data[range_in]
                data__s_b_out = tdms_file.object('Picoscope Data', data__s_b_name[1]).data[range_out]
                data__p_d_in = tdms_file.object('Picoscope Data', data__p_d_name[0]).data[range_in]
                data__p_d_out = tdms_file.object('Picoscope Data', data__p_d_name[1]).data[range_out]
                time__in = (np.arange(0, data__s_a_in.size, 1)) / sampling_frequency + range_time_in[0]
                time__out = (np.arange(0, data__s_a_out.size, 1)) / sampling_frequency + range_time_out[0]

            except KeyError:
                data__s_a_in = -1
                data__s_a_out = -1
                data__s_b_in = -1
                data__s_b_out = -1
                data__p_d_in = -1
                data__p_d_out = -1
                time__in = -1
                time__out = -1

            except IndexError:
                data__s_a_in = -2
                data__s_a_out = -2
                data__s_b_in = -2
                data__s_b_out = -2
                data__p_d_in = -2
                data__p_d_out = -2
                time__in = -2
                time__out = -2

        except KeyError:
            data__s_a_in = -1
            data__s_a_out = -1
            data__s_b_in = -1
            data__s_b_out = -1
            data__p_d_in = -1
            data__p_d_out = -1
            time__in = -1
            time__out = -1

    else:

        try:
            if range_time_in is 'auto':
                range_time_in = [0, 0.090]

            if range_time_out is 'auto':
                range_time_out = [0.330, 0.480]

            range_in = np.arange(range_time_in[0]*sampling_frequency, range_time_in[1]*sampling_frequency).astype(int)
            range_out = np.arange(range_time_out[0] * sampling_frequency, range_time_out[1] * sampling_frequency).astype(int)
            data__s_a_in = tdms_file.object('Picoscope Data', data__s_a_name).data[range_in]
            data__s_a_out = tdms_file.object('Picoscope Data', data__s_a_name).data[range_out]
            data__s_b_in = tdms_file.object('Picoscope Data', data__s_b_name).data[range_in]
            data__s_b_out = tdms_file.object('Picoscope Data', data__s_b_name).data[range_out]
            data__p_d_in = tdms_file.object('Picoscope Data', data__p_d_name).data[range_in]
            data__p_d_out = tdms_file.object('Picoscope Data', data__p_d_name).data[range_out]
            time__in = range_in/sampling_frequency
            time__out = range_out/sampling_frequency

        except KeyError:
            data__s_a_in = -1
            data__s_a_out = -1
            data__s_b_in = -1
            data__s_b_out = -1
            data__p_d_in = -1
            data__p_d_out = -1
            time__in = -1
            time__out = -1

    return data__s_a_in, data__s_b_in, data__s_a_out, data__s_b_out, data__p_d_in, data__p_d_out, time__in, time__out


def get_info_from_PROCESSED(path):

    speed = None
    number_of_scans = None
    first_position = None
    last_position = None
    step_size = None
    scan_per_position = None

    parameter_file = resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    tank_center = eval(config.get('Geometry', 'stages_position_at_tank_center'))

    if not os.path.exists(path + '/PROCESSED_IN.mat'):
        return -1

    else:
        data = sio.loadmat(path + '/PROCESSED_IN.mat', struct_as_record=False, squeeze_me=True)
        laser_position = data['laser_position']
        laser_position = - laser_position + tank_center
        number_of_scans = laser_position.size
        first_position = np.max(laser_position)
        last_position = np.min(laser_position)
        speed = np.round(np.max(data['speed_SA'][0]))
        scan_per_position = np.where(laser_position == laser_position[0])[0].size
        step_size = np.abs(np.mean(np.diff(np.unique(laser_position))))

    return speed, number_of_scans, first_position, last_position, step_size, scan_per_position


def raise_dialog_error(text):
    pass


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("..")

    return os.path.join(base_path, relative_path)


