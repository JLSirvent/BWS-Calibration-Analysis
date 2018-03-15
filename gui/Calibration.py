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


import scipy.io as sio
import numpy as np


class Calibration:

    def __init__(self, folder=None):
        '''
        Calibration is an object containing calibration results. More convenient for data manipulation and access
        '''

        self.calibration_folder = folder

        if folder is not None:

            data = sio.loadmat(folder + '/PROCESSED_IN.mat', struct_as_record=False, squeeze_me=True)
            self.eccentricity_IN = data['eccentricity']
            self.angular_position_SA_IN = data['angular_position_SA']
            self.angular_position_SB_IN = data['angular_position_SB']
            self.time_IN_SA = data['time_SA']
            self.time_IN_SB = data['time_SB']
            self.speed_IN_SA = data['speed_SA']
            self.speed_IN_SB = data['speed_SB']
            self.occlusion_IN = data['occlusion_position']
            self.laser_position_IN = data['laser_position']
            self.scan_number_IN = data['scan_number']

            try:
                self.data_valid_IN = data['data_valid']
            except:
                self.data_valid_IN = np.ones(data['laser_position'].size)

            data = sio.loadmat(folder + '/PROCESSED_OUT.mat', struct_as_record=False, squeeze_me=True)
            self.eccentricity_OUT = data['eccentricity']
            self.angular_position_SA_OUT = data['angular_position_SA']
            self.angular_position_SB_OUT = data['angular_position_SB']
            self.time_OUT_SA = data['time_SA']
            self.time_OUT_SB = data['time_SB']
            self.speed_OUT_SA = data['speed_SA']
            self.speed_OUT_SB = data['speed_SB']
            self.occlusion_OUT = data['occlusion_position']
            self.laser_position_OUT = data['laser_position']
            self.scan_number_OUT = data['scan_number']

            try:
                self.data_valid_OUT = data['data_valid']
            except:
                self.data_valid_OUT = np.ones(data['laser_position'].size)

            print('fine importation')

            self.data_valid=np.zeros(data['laser_position'].size)
            self.data_valid[np.where((self.data_valid_IN == 1)&(self.data_valid_IN == 1))] = 1

        else:

            self.eccentricity_IN = 0
            self.angular_position_SA_IN = 0
            self.angular_position_SB_IN = 0
            self.time_IN_SA = 0
            self.time_IN_SB = 0
            self.speed_IN_SA = 0
            self.speed_IN_SB = 0
            self.occlusion_IN = 0
            self.laser_position_IN = 0
            self.eccentricity_OUT = 0
            self.angular_position_SA_OUT = 0
            self.angular_position_SB_OUT = 0
            self.time_OUT_SA = 0
            self.time_OUT_SB = 0
            self.speed_OUT_SA = 0
            self.speed_OUT_SB = 0
            self.occlusion_OUT = 0
            self.laser_position_OUT = 0
            self.data_valid = 0


