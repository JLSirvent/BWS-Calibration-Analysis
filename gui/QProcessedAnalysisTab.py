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


import os
import sys
import time
import shutil
import numpy as np
import configparser
import scipy.io as sio

from matplotlib import pyplot as plt

from numpy import arange
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QTableWidgetItem, QFileDialog, QVBoxLayout, QHBoxLayout,QMessageBox

from lib import utils
from lib import ops_processing as ops
from gui import QTabWidgetPlotting
from gui import QFileDescriptionTable
from gui import QCalibrationInformation
from gui import Calibration


def cut(off, data):
    return data[off:data.size-off]

class Warning_Dialog(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'BWS-Calibration Application'
        self.left = 500
        self.top = 500
        self.width = 320
        self.height = 200
        self.user_choice = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        buttonReply = QMessageBox.question(self, 'BWS-Calibration Application', "There is existing data available. Do you want to overwrite it?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if buttonReply == QMessageBox.Yes:
            self.user_choice = True
        else:
            self.user_choice = False

        self.show()

class QProcessedAnalysisTab(QWidget):

    def __init__(self, parent=None):

        super(QProcessedAnalysisTab, self).__init__(parent)

        self.parent = parent

        # Window properties
        self.setWindowTitle('OPS Processing')

        self.actual_index = 0
        self.actual_PROCESSED_folder = ""
        self.actual_TDMS_folder = ""
        self.tdms_file_list = 0

        self.TabWidgetPlotting = QTabWidgetPlotting.QTabWidgetPlotting()
        self.FileDescriptionTable = QFileDescriptionTable.QFileDescriptionTable()
        self.CalibrationInformation = QCalibrationInformation.QCalibrationInformation(parent=self)
        self.mainLayout = QVBoxLayout

        self.FileDescriptionTable.save_and_update.clicked.connect(self.save_and_update)
        self.FileDescriptionTable.see_raw_button.clicked.connect(self.test_tdms)

        # We use a parameter file
        parameter_file = utils.resource_path('data/parameters.cfg')
        config = configparser.RawConfigParser()
        config.read(parameter_file)
        self.directory = eval(config.get('Application parameters', 'CalibrationsDirectory'))
        # --

        # Actions
        folder_list = os.listdir(self.directory)

        self.CalibrationInformation.scanner_selection_cb.addItem('Select Scanner:')
        self.CalibrationInformation.scanner_selection_cb.addItems(folder_list)

        self.CalibrationInformation.scanner_selection_cb.currentIndexChanged.connect(self.update_calibration_list)

        self.CalibrationInformation.calibration_selection_cb.setEnabled(False)
        self.CalibrationInformation.calibration_selection_cb.currentIndexChanged.connect(self.set_PROCESSED_folder_v2)

        self.CalibrationInformation.setparam_button.clicked.connect(self.show_parameters_window)

        self.CalibrationInformation.testparam_button.setEnabled(False)
        self.CalibrationInformation.testparam_button.clicked.connect(self.test_tdms)

        self.CalibrationInformation.processcalibration_button.setEnabled(False)
        self.CalibrationInformation.processcalibration_button.clicked.connect(self.onStart)

        self.CalibrationInformation.import_button.setEnabled(False)
        self.CalibrationInformation.import_button.clicked.connect(self.actualise_all)

        self.CalibrationInformation.processed_data_selection.label_select_folder.selectionChanged.connect(self.set_PROCESSED_folder)
        self.CalibrationInformation.tdms_data_selection.label_select_folder.selectionChanged.connect(self.set_TDMS_folder)
        self.CalibrationInformation.processed_data_selection.button_select_folder.pressed.connect(self.actualise_all)

        self.FileDescriptionTable.table.itemClicked.connect(self.ClickOnItem)


        self.mainLayout = QVBoxLayout()

        self.secondLayout = QHBoxLayout()
        self.secondLayout.addWidget(self.CalibrationInformation, 0, QtCore.Qt.AlignTop)
        self.secondLayout.addWidget(self.TabWidgetPlotting)
        self.secondLayout.addWidget(self.FileDescriptionTable, 0, QtCore.Qt.AlignRight)

        self.mainLayout.addLayout(self.secondLayout)

        self.calibration = 0

        #######################
        #
        # self.CalibrationInformation.set_PROCESSED_folder(self.actual_PROCESSED_folder)
        # self.actual_PROCESSED_folder = self.actual_PROCESSED_folder
        # self.actual_index = 0
        # self.calibration = Calibration.Calibration(self.actual_PROCESSED_folder)
        #
        # self.CalibrationInformation.set_TDMS_folder(self.actual_TDMS_folder)
        # self.actual_TDMS_folder = self.actual_TDMS_folder
        # self.actual_index = 0
        # self.tdms_file_list = utils.tdms_list_from_folder(self.actual_TDMS_folder)

        ########################~

        self.setLayout(self.mainLayout)

        # Window properties
        self.resize(100, 50)


    def onStart(self):

        if self.CalibrationInformation.import_button.isEnabled():
            choice = Warning_Dialog().user_choice
        else:
            choice = True

        if choice:
            #####make security ## ########

            test = utils.tdms_list_from_folder(self.actual_TDMS_folder)

            if type(test) is int:
                self.parent.LogDialog.add('Specified TDMS folder does not contain .tdms files', 'error')

            elif type(utils.extract_from_tdms(self.actual_TDMS_folder + '/' + test[0][0])[0]) is int:
                self.parent.LogDialog.add(
                    'TDMS file not loaded because of a key error - try to set [LabView output] in the parameters file',
                    'error')

            elif not os.path.exists(self.actual_destination_folder) or self.actual_destination_folder == '...':
                self.parent.LogDialog.add(
                    'Please specify a destination folder',
                    'error')

            else:

                self.done = False

                self.myLongTask = utils.CreateRawDataFolder(self.actual_TDMS_folder, self.actual_destination_folder, self)
                self.myLongTask.notifyProgress.connect(self.onProgress)
                self.myLongTask.notifyState.connect(self.onState)
                self.myLongTask.notifyFile.connect(self.onFile)
                self.CalibrationInformation.processcalibration_button.setEnabled(False)
                self.myLongTask.start()

                self.parent.LogDialog.add('Starting ' + self.actual_TDMS_folder + ' conversion', 'info')

    def RAW_IN(self):

        self.myLongTask = ops.ProcessRawData(self.actual_destination_folder + '/RAW_DATA/RAW_IN', self.actual_destination_folder)
        self.myLongTask.notifyProgress.connect(self.onProgress)
        self.myLongTask.notifyState.connect(self.onState)
        self.myLongTask.notifyFile.connect(self.onFile)
        self.CalibrationInformation.processcalibration_button.setEnabled(False)
        self.myLongTask.start()

    def RAW_OUT(self):

        self.myLongTask = ops.ProcessRawData(self.actual_destination_folder + '/RAW_DATA/RAW_OUT', self.actual_destination_folder)
        self.myLongTask.notifyProgress.connect(self.onProgress)
        self.myLongTask.notifyState.connect(self.onState)
        self.myLongTask.notifyFile.connect(self.onFile)
        self.CalibrationInformation.processcalibration_button.setEnabled(False)
        self.myLongTask.start()

    def onProgress(self, i):
        self.CalibrationInformation.progressBar.setValue(i)
        if i == 99:
            #self.Process.setDisabled(False)
            self.CalibrationInformation.progressBar.reset()

    def onState(self, state):
        print(state)
        self.CalibrationInformation.label_progression.setText(state)
        if state == 'done convert':
            self.CalibrationInformation.processcalibration_button.setEnabled(True)
            self.CalibrationInformation.progressBar.reset()
            self.RAW_IN()

        elif state == 'done IN':
            self.CalibrationInformation.processcalibration_button.setEnabled(True)
            self.CalibrationInformation.progressBar.reset()
            self.RAW_OUT()


        elif state == 'done OUT':
            self.CalibrationInformation.processcalibration_button.setEnabled(True)
            utils.create_processed_data_folder(self.actual_TDMS_folder, destination_folder=self.actual_destination_folder, force_overwrite='y')
            self.CalibrationInformation.progressBar.reset()


    def onFile(self, file):
        self.CalibrationInformation.label_file.setText(file)

    def show_parameters_window(self):
        os.system('Notepad ' + utils.resource_path('data/parameters.cfg'))

    def test_tdms(self):

        test = utils.tdms_list_from_folder_sorted(self.actual_TDMS_folder)
        filepath = test[self.actual_index]

        print(self.actual_index)
        print(test[self.actual_index])

        data__s_a_in, data__s_b_in, data__s_a_out, data__s_b_out, data__p_d_in, data__p_d_out, time__in, time__out = utils.extract_from_tdms(filepath)


        if type(data__s_a_in) is not int:

            self.actualise_single_QTab(self.TabWidgetPlotting.tab_OPS_processing,
                                       data__s_a_in, data__s_b_in, data__s_a_out, data__s_b_out,
                                       t1=time__in, t2=time__out, pd1=data__p_d_in, pd2=data__p_d_out)

            # We use a parameter file
            parameter_file = utils.resource_path('data/parameters.cfg')
            config = configparser.RawConfigParser()
            config.read(parameter_file)
            # --

            # Process Positions
            Data_SA_in = ops.process_position(data__s_a_in, utils.resource_path('data/parameters.cfg'), time__in[0], showplot=0, filename=" ", INOUT= 'IN')
            Data_SB_in = ops.process_position(data__s_b_in, utils.resource_path('data/parameters.cfg'), time__in[0], showplot=0, filename=" ", INOUT= 'IN')
            Data_SA_out = ops.process_position(data__s_a_out, utils.resource_path('data/parameters.cfg'), time__out[0], showplot=0, filename=" ", INOUT= 'OUT')
            Data_SB_out = ops.process_position(data__s_b_out, utils.resource_path('data/parameters.cfg'), time__out[0], showplot=0, filename=" ", INOUT= 'OUT')

            Data_SB_R_in = utils.resample(Data_SB_in, Data_SA_in)
            Data_SB_R_out = utils.resample(Data_SB_out, Data_SA_out)

            # Eccentricity from OPS processing and saving in list
            _eccentricity_in = np.subtract(Data_SA_in[1], Data_SB_R_in[1]) / 2
            _eccentricity_out = np.subtract(Data_SA_out[1], Data_SB_R_out[1]) / 2

            # OPS speed processing and smoothing
            _speed_SA_in = np.divide(np.diff(Data_SA_in[1]), np.diff(Data_SA_in[0]))
            _speed_SB_in = np.divide(np.diff(Data_SB_in[1]), np.diff(Data_SB_in[0]))

            _speed_SA_out = np.divide(np.diff(Data_SA_out[1]), np.diff(Data_SA_out[0]))
            _speed_SB_out = np.divide(np.diff(Data_SB_out[1]), np.diff(Data_SB_out[0]))

            N = 8
            _speed_SA_in = np.convolve(_speed_SA_in,np.ones((N,)) / N, mode='valid')
            _speed_SB_in = np.convolve(_speed_SB_in, np.ones((N,)) / N, mode='valid')
            _speed_SA_out = np.convolve(_speed_SA_out, np.ones((N,)) / N, mode='valid')
            _speed_SB_out = np.convolve(_speed_SB_out, np.ones((N,)) / N, mode='valid')


            self.actualise_single_QTab(self.TabWidgetPlotting.tab_RDS,
                                        np.array([Data_SA_in[0], Data_SA_in[0]]),
                                        np.array([Data_SA_out[0],Data_SA_out[0]]),
                                        np.array([Data_SB_in[0], Data_SB_in[0]]),
                                        np.array([Data_SB_out[0], Data_SA_out[0]]))

            self.actualise_single_QTab(self.TabWidgetPlotting.tab_position,
                                       x1=Data_SA_in[0],
                                       y1=Data_SA_in[1],
                                       x2=Data_SA_out[0],
                                       y2=Data_SA_out[1],
                                       x1_2=Data_SB_in[0],
                                       y1_2=Data_SB_in[1],
                                       x2_2=Data_SB_out[0],
                                       y2_2=Data_SB_out[1])

            self.actualise_single_QTab(self.TabWidgetPlotting.tab_speed,
                                       x1=cut(2, Data_SA_in[0][0:len(_speed_SA_in)]),
                                       y1=cut(2, 1e3*_speed_SA_in),
                                       x2=cut(2, Data_SA_out[0][0:len(_speed_SA_out)]),
                                       y2=cut(2, 1e3*-_speed_SA_out),
                                       x1_2=cut(2, Data_SB_in[0][0:len(_speed_SB_in)]),
                                       y1_2=cut(2, 1e3*_speed_SB_in),
                                       x2_2=cut(2, Data_SB_out[0][0:len(_speed_SB_out)]),
                                       y2_2=cut(2, -1e3*_speed_SB_out))

            self.actualise_single_QTab(self.TabWidgetPlotting.tab_eccentricity,
                                             x1=Data_SA_in[1],
                                             y1=1e6*_eccentricity_in,
                                             x2=Data_SA_out[1],
                                             y2=1e6*_eccentricity_out,
                                             x1_2= [0, 0],
                                             y1_2= [0, 0],
                                             x2_2= [0, 0],
                                             y2_2= [0, 0])

            self.parent.LogDialog.add(filepath + ' processed', 'info')
            self.TabWidgetPlotting.setCurrentWidget(self.TabWidgetPlotting.tab_OPS_processing)
        else:
            if data__s_a_in == -1:
                self.parent.LogDialog.add('TDMS file not loaded because of a key error - try to set [LabView output] in the parameters file', 'error')

            elif data__s_a_in == -2:
                self.parent.LogDialog.add('One of the range specified is out of data scope - try to set [LabView output] in the parameters file', 'error')

    def update_calibration_list(self,i):
        try:
            full_directory = self.directory + self.CalibrationInformation.scanner_selection_cb.currentText() + '/RawData'
            self.CalibrationInformation.calibration_selection_cb.clear()
            if os.path.exists(full_directory):
                folder_list = os.listdir(full_directory)
                self.CalibrationInformation.calibration_selection_cb.addItem('Select Calibration:')
                self.CalibrationInformation.calibration_selection_cb.addItems(folder_list)
                self.CalibrationInformation.calibration_selection_cb.setEnabled(True)
            else:
                self.CalibrationInformation.calibration_selection_cb.setEnabled(False)
        except:
            print('Error when indexing processed calibrations folders')

    def set_PROCESSED_folder_v2(self):
        try:
            self.full_directory_processed = self.directory + self.CalibrationInformation.scanner_selection_cb.currentText() + '/ProcessedData/' + self.CalibrationInformation.calibration_selection_cb.currentText() + ' PROCESSED'
            self.actual_PROCESSED_folder = self.full_directory_processed
            self.actual_destination_folder = self.directory + self.CalibrationInformation.scanner_selection_cb.currentText() + '/ProcessedData'

            if os.path.exists(self.full_directory_processed):
                self.CalibrationInformation.import_button.setEnabled(True)
            else:
                self.CalibrationInformation.import_button.setEnabled(False)

            full_directory_tdms = self.directory + self.CalibrationInformation.scanner_selection_cb.currentText() + '/RawData/' + self.CalibrationInformation.calibration_selection_cb.currentText()
            self.actual_TDMS_folder = full_directory_tdms

            if os.path.exists(full_directory_tdms):
                self.CalibrationInformation.testparam_button.setEnabled(True)
                self.CalibrationInformation.processcalibration_button.setEnabled(True)
            else:
                self.CalibrationInformation.testparam_button.setEnabled(False)
                self.CalibrationInformation.processcalibration_button.setEnabled(False)

        except:
            print('Error when defining Processed or TDMS folder: Check that both folders for the same calibration exists!')

    def ClickOnItem(self, item):
        self.actual_index = item.row()

        if self.FileDescriptionTable.table.item(item.row(), 0).checkState() == QtCore.Qt.Checked:
            self.calibration.data_valid[item.row()] = 1
        else:
            self.calibration.data_valid[item.row()] = 0

        try:
            self.actualise_not_folder_dependant_plot()
        except:
            pass


    def save_and_update(self):
        sio.savemat(self.full_directory_processed + '/PROCESSED_IN.mat',

                    {'angular_position_SA': self.calibration.angular_position_SA_IN,
                     'angular_position_SB': self.calibration.angular_position_SB_IN,
                     'eccentricity': self.calibration.eccentricity_IN,
                     'laser_position': self.calibration.laser_position_IN,
                     'occlusion_position': self.calibration.occlusion_IN,
                     'oc': self.calibration.oc_IN,
                     'data_valid': self.calibration.data_valid,
                     'scan_number': self.calibration.scan_number_IN,
                     'speed_SA': self.calibration.speed_IN_SA,
                     'speed_SB': self.calibration.speed_IN_SB,
                     'time_SA': self.calibration.time_IN_SA,
                     'time_SB': self.calibration.time_IN_SB},

                    do_compression=True)

        # OUT POSITIONS CORRECTION:
        # -------------------------
        #self.calibration.occlusion_OUT = np.pi / 2 - self.calibration.occlusion_OUT
        #self.calibration.angular_position_SA_OUT = np.pi / 2 - self.calibration.angular_position_SA_OUT
        #self.calibration.angular_position_SB_OUT = np.pi / 2 - self.calibration.angular_position_SB_OUT

        sio.savemat(self.full_directory_processed + '/PROCESSED_OUT.mat',

                    {'angular_position_SA': self.calibration.angular_position_SA_OUT,
                     'angular_position_SB': self.calibration.angular_position_SB_OUT,
                     'eccentricity': self.calibration.eccentricity_OUT,
                     'laser_position': self.calibration.laser_position_OUT,
                     'occlusion_position': self.calibration.occlusion_OUT,
                     'oc': self.calibration.oc_OUT,
                     'data_valid': self.calibration.data_valid,
                     'scan_number': self.calibration.scan_number_OUT,
                     'speed_SA': self.calibration.speed_OUT_SA,
                     'speed_SB': self.calibration.speed_OUT_SB,
                     'time_SA': self.calibration.time_OUT_SA,
                     'time_SB': self.calibration.time_OUT_SB},

                    do_compression=True)

        self.actualise_all()

    def actualise_all(self):
        info_set_bool = self.CalibrationInformation.set_PROCESSED_folder(self.actual_PROCESSED_folder)

        if info_set_bool == -1:
            self.parent.LogDialog.add('PROCESSED info not found in this folder', 'error')

        else:

            self.calibration = Calibration.Calibration(self.actual_PROCESSED_folder)

            self.tdms_file_list = utils.tdms_list_from_folder(self.actual_TDMS_folder)

            self.actualise_file_table()

            # OUT POSITIONS CORRECTION:
            # -------------------------
            #self.calibration.occlusion_OUT = np.pi/2 - self.calibration.occlusion_OUT
            #self.calibration.angular_position_SA_OUT = np.pi/2 - self.calibration.angular_position_SA_OUT
            #self.calibration.angular_position_SB_OUT = np.pi/2 - self.calibration.angular_position_SB_OUT

            Idx = np.where(self.calibration.data_valid == 1)
            print('fine index found')

            # SET BOUNDARIES OF CALIBRATION:
            # ------------------------------
            try:
                SIndex = 0
                Idxin  = np.where((self.calibration.angular_position_SA_IN[SIndex][0:self.calibration.angular_position_SA_IN[SIndex].size - 20] > np.min(self.calibration.occlusion_IN[Idx])) & (self.calibration.angular_position_SA_IN[SIndex][0:self.calibration.angular_position_SA_IN[SIndex].size - 20] < np.max(self.calibration.occlusion_IN[Idx])))
                Idxout = np.where((self.calibration.angular_position_SA_OUT[SIndex][0:self.calibration.angular_position_SA_OUT[SIndex].size - 20] > np.min(self.calibration.occlusion_OUT[Idx])) & (self.calibration.angular_position_SA_OUT[SIndex][0:self.calibration.angular_position_SA_OUT[SIndex].size - 20]  < np.max(self.calibration.occlusion_OUT[Idx])))
                Boundin =  [self.calibration.time_IN_SA[SIndex][np.min(Idxin)], self.calibration.time_IN_SA[SIndex][np.max(Idxin)]]
                Boundout = [self.calibration.time_OUT_SA[SIndex][np.min(Idxout)], self.calibration.time_OUT_SA[SIndex][np.max(Idxout)]]
            except:
                print('Error determining calibration boundaries')
                Boundin= [0,0]
                Boundout =[0,0]

            print('fine index found2')

            if self.CalibrationInformation.chkCalibrations.isChecked():
                # CALIBRATION IN
                # --------------
                self.actualise_single_QTab(self.TabWidgetPlotting.tab_calibration_IN,
                                           self.calibration.occlusion_IN[Idx],
                                           self.calibration.laser_position_IN[Idx],
                                           self.calibration.occlusion_OUT[Idx],
                                           self.calibration.laser_position_OUT[Idx])

            if self.CalibrationInformation.chkPositions.isChecked():
                # POSITIONS
                # ---------
                self.actualise_multiple_Qtab(self.TabWidgetPlotting.tab_positions,
                                                 x1=self.calibration.time_IN_SA[Idx],
                                                 y1=self.calibration.angular_position_SA_IN[Idx],
                                                 b1=Boundin,
                                                 x2=self.calibration.time_OUT_SA[Idx],
                                                 y2=self.calibration.angular_position_SA_OUT[Idx],
                                                 b2=Boundout)

            if self.CalibrationInformation.chkSpeeds.isChecked():
                # SPEEDS
                # ------
                self.actualise_multiple_Qtab(self.TabWidgetPlotting.tab_speeds,
                                                 x1=self.calibration.time_IN_SA[Idx],
                                                 y1=1e3*self.calibration.speed_IN_SA[Idx],
                                                 b1=Boundin,
                                                 x2=self.calibration.time_OUT_SA[Idx],
                                                 y2=-1e3*self.calibration.speed_OUT_SA[Idx],
                                                 b2=Boundout)

            if self.CalibrationInformation.chkEccentricities.isChecked():
                # ECCENTRICITIES
                # --------------
                Boundin = [np.min(self.calibration.occlusion_IN[Idx]), np.max(self.calibration.occlusion_IN[Idx])]
                self.actualise_multiple_Qtab(self.TabWidgetPlotting.tab_eccentricities,
                                                 x1=self.calibration.angular_position_SA_IN[Idx],
                                                 y1=self.calibration.eccentricity_IN[Idx],
                                                 b1=Boundin,
                                                 x2=self.calibration.angular_position_SA_OUT[Idx],
                                                 y2=-self.calibration.eccentricity_OUT[Idx],
                                                 b2=Boundin)

            if self.CalibrationInformation.chkFPC.isChecked():

                # FIXED POINT CALIBRATION (FPC)
                # ----------------------------
                self.actualise_single_QTab(self.TabWidgetPlotting.tab_fpc,
                                                x1 = self.calibration.time_IN_SA[Idx],
                                                y1 = self.calibration.angular_position_SA_IN[Idx],
                                                x2 = self.calibration.time_OUT_SA[Idx],
                                                y2 = self.calibration.angular_position_SA_OUT[Idx],
                                                x1_2 = self.calibration.time_IN_SB[Idx],
                                                y1_2 = self.calibration.angular_position_SB_IN[Idx],
                                                x2_2 = self.calibration.time_OUT_SB[Idx],
                                                y2_2 = self.calibration.angular_position_SB_OUT[Idx],
                                                t1 = self.calibration.occlusion_IN[Idx],
                                                t2 = self.calibration.occlusion_OUT[Idx])

            if self.CalibrationInformation.chkRDS.isChecked():
                # RELATIVE DISTANCE SIGNATURE PLOT (RDS)
                # ----------------------------
                self.actualise_single_QTab(self.TabWidgetPlotting.tab_RDS,
                                           self.calibration.time_IN_SA[Idx],
                                           self.calibration.time_OUT_SA[Idx],
                                           self.calibration.time_IN_SB[Idx],
                                           self.calibration.time_OUT_SB[Idx])


            self.FileDescriptionTable.table.setHorizontalHeaderLabels(['Valid',
                                                                       'Laser pos\n [mm]',
                                                                       'Scan\nnumber', 'occlusion\nIN [rad]',
                                                                       'occlusion\nOUT [rad]'])

            self.TabWidgetPlotting.setCurrentWidget(self.TabWidgetPlotting.tab_calibration_IN)

            self.TabWidgetPlotting.tab_OPS_processing.reset()

            self.parent.LogDialog.add('PROCESSED data imported', 'info')

    def actualise_not_folder_dependant_plot(self):
        SelectedIndex = np.count_nonzero(self.calibration.data_valid[0:self.actual_index])
        self.TabWidgetPlotting.tab_calibration_IN.set_focus(SelectedIndex)
        #self.TabWidgetPlotting.tab_calibration_OUT.set_focus(SelectedIndex)


    def actualise_multiple_Qtab(self, QTab, x1, y1, x2, y2, b1, b2):
        QTab.set_x_IN(x1)
        QTab.set_y_IN(y1)
        QTab.set_B_IN(b1)
        QTab.set_x_OUT(x2)
        QTab.set_y_OUT(y2)
        QTab.set_B_OUT(b2)
        QTab.actualise_ax()

    def actualise_single_QTab(self, QTab, x1, y1, x2, y2, x1_2=None, y1_2=None, x2_2=None, y2_2=None, t1=None, t2=None, pd1=None, pd2=None):

        QTab.set_x_IN_A(x1)
        QTab.set_y_IN_A(y1)
        QTab.set_x_OUT_A(x2)
        QTab.set_y_OUT_A(y2)

        if x1_2 is not None:
            QTab.set_x_IN_B(x1_2)
            QTab.set_y_IN_B(y1_2)
            QTab.set_x_OUT_B(x2_2)
            QTab.set_y_OUT_B(y2_2)

        if t1 is not None:
            QTab.set_t1(t1)
            QTab.set_t2(t2)

        if pd1 is not None:
            QTab.set_pd1(pd1)
            QTab.set_pd2(pd2)

        QTab.actualise_ax()

    def actualise_file_table(self):

        folder = self.actual_PROCESSED_folder

        parameter_file = utils.resource_path('data/parameters.cfg')
        config = configparser.RawConfigParser()
        config.read(parameter_file)
        tank_center = eval(config.get('Geometry', 'stages_position_at_tank_center'))

        laser_position = self.calibration.laser_position_IN
        scan_number = self.calibration.scan_number_IN
        occlusion_IN = self.calibration.occlusion_IN
        occlusion_OUT = self.calibration.occlusion_IN
        data_valid = self.calibration.data_valid

        self.FileDescriptionTable.table.setRowCount(laser_position.size)
        self.FileDescriptionTable.table.setColumnCount(5)

        self.FileDescriptionTable.table.horizontalHeader().resizeSection(0, 40)
        self.FileDescriptionTable.table.horizontalHeader().resizeSection(1, 55)
        self.FileDescriptionTable.table.horizontalHeader().resizeSection(2, 40)
        self.FileDescriptionTable.table.horizontalHeader().resizeSection(3, 55)
        self.FileDescriptionTable.table.horizontalHeader().resizeSection(4, 55)

        font2 = QtGui.QFont()
        font2.setPointSize(7)

        # self.FileDescriptionTable.table.setFont(font2)

        font = QtGui.QFont()
        font.setPointSize(8)

        for i in arange(0, laser_position.size):

            ChkItem = QTableWidgetItem()
            ChkItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)

            if data_valid[i] == 1:
                ChkItem.setCheckState(QtCore.Qt.Checked)
            else:
                ChkItem.setCheckState(QtCore.Qt.Unchecked)

            self.FileDescriptionTable.table.setItem(i, 0, ChkItem)
            #self.FileDescriptionTable.table.setItem(i, 1, QTableWidgetItem(str(laser_position[i])))
            self.FileDescriptionTable.table.setItem(i, 1, QTableWidgetItem(str( - laser_position[i] + tank_center )))
            self.FileDescriptionTable.table.setItem(i, 2, QTableWidgetItem(str(scan_number[i])))
            self.FileDescriptionTable.table.setItem(i, 3, QTableWidgetItem(str(occlusion_IN[i])))
            self.FileDescriptionTable.table.setItem(i, 4, QTableWidgetItem(str(occlusion_OUT[i])))

            self.FileDescriptionTable.table.item(i, 0).setTextAlignment(QtCore.Qt.AlignCenter)
            #self.FileDescriptionTable.table.item(i, 1).setTextAlignment(QtCore.Qt.AlignCenter)
            self.FileDescriptionTable.table.item(i, 1).setTextAlignment(QtCore.Qt.AlignCenter)
            self.FileDescriptionTable.table.item(i, 2).setTextAlignment(QtCore.Qt.AlignCenter)
            self.FileDescriptionTable.table.item(i, 3).setTextAlignment(QtCore.Qt.AlignCenter)
            self.FileDescriptionTable.table.item(i, 4).setTextAlignment(QtCore.Qt.AlignCenter)

            self.FileDescriptionTable.table.item(i, 0).setFont(font)
            #self.FileDescriptionTable.table.item(i, 1).setFont(font)
            self.FileDescriptionTable.table.item(i, 1).setFont(font)
            self.FileDescriptionTable.table.item(i, 2).setFont(font)
            self.FileDescriptionTable.table.item(i, 3).setFont(font)
            self.FileDescriptionTable.table.item(i, 4).setFont(font)
        print('fine table update')

    def set_PROCESSED_folder(self, file=None):

        if file is None:
            file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if file is not '':
            print(file)
            self.parent.LogDialog.add('Selected file : ' + file, 'info')

            info_set_bool = self.CalibrationInformation.set_PROCESSED_folder(file)

            #if info_set_bool == -1:
            #    self.parent.LogDialog.add('PROCESSED info not found in this folder', 'warning')

            #else:
            print(file)
            self.actual_PROCESSED_folder = file
            self.actual_index = 0

            if self.actual_PROCESSED_folder.find(self.actual_TDMS_folder.split('/')[::-1][0]) == -1:
                self.parent.LogDialog.add('TDMS folder name and PROCESSED folder name do not match', 'warning')

            self.calibration = Calibration.Calibration(self.actual_PROCESSED_folder)

    def set_TDMS_folder(self, file=None):

        if file is None:
            file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if file is not '':

            self.parent.LogDialog.add('Selected file : ' + file, 'info')

            self.actual_TDMS_folder = file
            self.tdms_file_list = utils.tdms_list_from_folder(file)
            self.CalibrationInformation.set_TDMS_folder(file)

            if self.actual_PROCESSED_folder.find(self.actual_TDMS_folder.split('/')[::-1][0]) == -1:
                self.parent.LogDialog.add('TDMS folder name and PROCESSED folder name do not match', 'warning')

            else:
                self.parent.LogDialog.add('TDMS folder name and PROCESSED folder name are matching', 'info')

    def show_parameters_window(self):
        self.parent.LogDialog.add('Opening ' + utils.resource_path('data/parameters.cfg') + ' ...', 'info')
        time.sleep(2)
        os.system('Notepad ' + utils.resource_path('data/parameters.cfg'))


def main():
    app = QApplication(sys.argv)
    ex = QProcessedAnalysisTab()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()








