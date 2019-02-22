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


from __future__ import unicode_literals

from lib import utils
from gui import QFolderSelectionWidget
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QLineEdit, QHBoxLayout, QComboBox, QPushButton, QProgressBar, QCheckBox

import configparser
import os
import numpy as np

from matplotlib import pyplot as plt


class QCalibrationInformation(QWidget):

    def __init__(self, parent=None):
        '''
        QWidget containing some calibration info
        :param parent:
        '''

        super(QCalibrationInformation, self).__init__(parent=None)

        # self.main_widget = QWidget(self)

        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        main_layout = QVBoxLayout()

        self.processed_data_folder = 0
        self.tdms_data_folder = 0

        self.scanner_selection_cb = QComboBox()
        self.calibration_selection_cb = QComboBox()

        self.setparam_button = QPushButton('Set param',self)
        self.testparam_button = QPushButton('Test param', self)
        self.processcalibration_button = QPushButton('PROCESS calibration',self)

        self.import_options_box  = QGroupBox('Import Options')
        self.chkCalibrations = QCheckBox('Calibration Curves')
        self.chkCalibrations.setChecked(1)
        self.chkPositions = QCheckBox('Positions')
        self.chkSpeeds = QCheckBox('Speeds')
        self.chkEccentricities = QCheckBox('Eccentricities')
        self.chkFPC = QCheckBox('Fixed Point Calibration')
        self.chkRDS = QCheckBox('Relative Distance Signature')

        self.import_button = QPushButton('IMPORT calibration',self)

        self.processed_data_selection = QFolderSelectionWidget.QFolderSelectionWidget('PROCESSED folder:')
        self.tdms_data_selection = QFolderSelectionWidget.QFolderSelectionWidget('TDMS folder:', button=False)
        self.parameters_file_selection = QFolderSelectionWidget.QFolderSelectionWidget('Parameters file:', button=False)

        self.import_options_box_layout = QVBoxLayout(self)
        self.import_options_box_layout.addStretch(1)
        self.import_options_box_layout.addWidget(self.chkCalibrations)
        self.import_options_box_layout.addWidget(self.chkPositions)
        self.import_options_box_layout.addWidget(self.chkSpeeds)
        self.import_options_box_layout.addWidget(self.chkEccentricities)
        self.import_options_box_layout.addWidget(self.chkFPC)
        self.import_options_box_layout.addWidget(self.chkRDS)
        self.import_options_box_layout.addWidget(self.import_button)
        self.import_options_box.setLayout(self.import_options_box_layout)

        self.import_box = QGroupBox('Calibration Selection')

        self.import_box_layout = QVBoxLayout(self)
        self.import_box_layout.addStretch(1)
        self.import_box_layout.addWidget(self.scanner_selection_cb)
        self.import_box_layout.addWidget(self.calibration_selection_cb)

        self.import_box_layout2 = QHBoxLayout(self)
        self.import_box_layout2.addWidget(self.setparam_button)
        self.import_box_layout2.addWidget(self.testparam_button)

        self.import_box_layout.addLayout(self.import_box_layout2)

        self.import_box_layout.addWidget(self.processcalibration_button)
        self.import_box_layout.addWidget(self.import_options_box)

        self.import_box.setLayout(self.import_box_layout)

        main_layout.addWidget(self.import_box)

        #main_layout.addWidget(self.processed_data_selection)

        self.labels_layout = QVBoxLayout()
        self.values_layout = QVBoxLayout()

        self.labels = []
        self.values = []

        self.gen_info_box = QGroupBox('General information')
        self.gen_info_layout = QVBoxLayout(self)

        self.labels.append(QLabel('Speed (rad/s):'))
        self.labels.append(QLabel('First position (mm):'))
        self.labels.append(QLabel('Last Position (mm):'))
        self.labels.append(QLabel('Step size (mm):'))
        self.labels.append(QLabel('Scans per positions:'))
        self.labels.append(QLabel('Number of scans:'))

        self.values.append(QLineEdit(''))
        self.values.append(QLineEdit(''))
        self.values.append(QLineEdit(''))
        self.values.append(QLineEdit(''))
        self.values.append(QLineEdit(''))
        self.values.append(QLineEdit(''))

        for label, value in zip(self.labels, self.values):
            label.setFixedSize(100, 25)
            self.labels_layout.addWidget(label)
            value.setFixedSize(50, 25)
            value.setStyleSheet('background-color:white')
            value.setReadOnly(True)
            self.values_layout.addWidget(value)

        self.info_layout = QHBoxLayout()

        self.info_layout.addLayout(self.labels_layout)
        self.info_layout.addLayout(self.values_layout)

        self.gen_info_layout.addLayout(self.info_layout)
        self.gen_info_box.setLayout(self.gen_info_layout)

        main_layout.addWidget(self.gen_info_box)

        # Progress Bar and labels:
        self.label_progression = QLabel('Waiting for processing')
        self.label_file = QLabel('')
        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 100)

        main_layout.addWidget(self.label_progression)
        main_layout.addWidget(self.progressBar)
        main_layout.addWidget(self.label_file)
        # ---

        #self.setFixedHeight(430)
        self.setFixedWidth(250)

        self.setLayout(main_layout)

    def set_PROCESSED_folder(self, file):

        if file is not '':

            self.processed_data_folder = file
            self.processed_data_selection.set_folder(file)

            info = utils.get_info_from_PROCESSED(file)

            if type(info) is int:
                return -1

            else:
                self.values[0].setText(str(info[0]))
                self.values[1].setText(str(info[2]))
                self.values[2].setText(str(info[3]))
                self.values[3].setText(str(info[4]))
                self.values[4].setText(str(info[5]))
                self.values[5].setText(str(info[1]))
                return 0

    def set_PROCESSED_folder_V2(self, calibration):

        N = 10
        spe = np.convolve(1e3*calibration.speed_IN_SA[0], np.ones((N,)) / N, mode='valid')

        self.values[0].setText(str(np.round(np.max(spe))))
        self.values[1].setText(str(np.max(calibration.laser_position_IN)))
        self.values[2].setText(str(np.min(calibration.laser_position_IN)))
        self.values[3].setText(str(np.max(np.abs(np.diff(calibration.laser_position_IN)))))
        self.values[4].setText(str(len(set(calibration.scan_number_IN))))
        self.values[5].setText(str(len(calibration.laser_position_IN)))

    def set_TDMS_folder(self, file):
        self.tdms_data_folder = file
        self.tdms_data_selection.set_folder(file)

