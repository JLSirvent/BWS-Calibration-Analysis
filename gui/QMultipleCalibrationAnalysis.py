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
import scipy.io as sio

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget,QPushButton, QCheckBox, QLabel, QHBoxLayout, QTabWidget, QVBoxLayout, QFileDialog, QApplication


from lib import ops_processing as ops
from gui import QFolderSelectionWidget
from gui import QMultipleFolderSelection
from gui import QTabMultipleCalibrationPlottingComparisionToReference
from gui import QTabMultipleCalibrationGlobalAnalysis
from gui import QTabMultipleResidualsShape


def cut(off, data):
    return data[off:data.size-off]


class QMultipleCalibrationAnalysis(QWidget):

    def __init__(self, parent=None):
        '''
        QWidget containing the Tab for Multiple calibration analysis
        :param parent:
        '''

        super(QMultipleCalibrationAnalysis, self).__init__(parent)

        self.subfolders_to_process = ''
        self.reference_folder = ''

        self.mainWidget = QWidget()

        self.parent = parent

        self.PlotTab_IN = QTabMultipleCalibrationPlottingComparisionToReference.QTabMultipleCalibrationPlottingComparisionToReference()
        self.PlotTab_OUT = QTabMultipleCalibrationPlottingComparisionToReference.QTabMultipleCalibrationPlottingComparisionToReference()
        self.global_histogram_tab = QTabMultipleCalibrationGlobalAnalysis.QTabMultipleCalibrationGlobalAnalysis()
        self.residuals_shape_tab = QTabMultipleResidualsShape.QTabMultipleResidualsShape()

        self.folder_selection = QMultipleFolderSelection.QMultipleFolderSelection()
        self.process_folders = QPushButton('Process')
        self.process_folders.setFixedWidth(250)
        self.plot_comparision = QPushButton('Plot multiple analysis')
        self.plot_comparision.setFixedWidth(250)
        self.mean_fit_option = QCheckBox()
        self.mean_fit_option.setFixedWidth(15)
        self.personal_fit_option = QCheckBox()
        self.personal_fit_option.setFixedWidth(15)

        self.mean_fit_option.stateChanged.connect(self.set_mean_option)
        self.personal_fit_option.stateChanged.connect(self.set_personal_option)

        self.mean_fit_option_layout = QHBoxLayout()
        self.mean_fit_option_label = QLabel('Use mean curve as reference')
        self.mean_fit_option_label.setAlignment(QtCore.Qt.AlignLeft)
        self.mean_fit_option_label.setFixedWidth(150)
        self.mean_fit_option_layout.addWidget(self.mean_fit_option_label, 0, QtCore.Qt.AlignLeft)
        self.mean_fit_option_layout.addWidget(self.mean_fit_option, 0, QtCore.Qt.AlignLeft)

        self.personal_fit_option_layout = QHBoxLayout()
        self.personal_fit_option_label = QLabel('Each calibration use their proper fit')
        self.personal_fit_option_label.setAlignment(QtCore.Qt.AlignLeft)
        self.personal_fit_option_label.setFixedWidth(150)
        self.personal_fit_option_layout.addWidget(self.personal_fit_option_label, 0, QtCore.Qt.AlignLeft)
        self.personal_fit_option_layout.addWidget(self.personal_fit_option, 0, QtCore.Qt.AlignLeft)

        self.fit_folder_selection = QFolderSelectionWidget.QFolderSelectionWidget('Use a specific reference folder :',button=False)
        self.fit_folder_selection.label_select_folder.selectionChanged.connect(self.set_reference_folder)

        self.multipleanalysistab = QTabWidget()
        self.multipleanalysistab.addTab(self.PlotTab_IN, 'Comparision analysis IN')
        self.multipleanalysistab.addTab(self.PlotTab_OUT, 'Comparision analysis OUT')
        self.multipleanalysistab.addTab(self.global_histogram_tab, 'Global histogram')
        self.multipleanalysistab.addTab(self.residuals_shape_tab, 'Residuals shape')

        self.process_folders.clicked.connect(self.onStart)
        self.plot_comparision.clicked.connect(self.plot_comparision_act)

        self.folder_selection_layout = QVBoxLayout()

        self.main_layout = QHBoxLayout()

        self.folder_selection_layout.addWidget(self.folder_selection, 0, QtCore.Qt.AlignTop)
        self.folder_selection_layout.addWidget(self.fit_folder_selection)
        self.folder_selection_layout.addLayout(self.mean_fit_option_layout)
        self.folder_selection_layout.addLayout(self.personal_fit_option_layout)
        self.folder_selection_layout.addWidget(self.process_folders)
        self.folder_selection_layout.addWidget(self.plot_comparision)

        self.mainWidget.setLayout(self.folder_selection_layout)
        self.mainWidget.setFixedWidth(250)
        self.mainWidget.setFixedHeight(500)

        self.super_layout = QHBoxLayout()

        self.super_layout.addWidget(self.mainWidget, 0, QtCore.Qt.AlignTop)
        self.super_layout.addWidget(self.multipleanalysistab)

        self.setLayout(self.super_layout)

    def get_folder_list(self):
        self.subfolders_to_process = self.folder_selection.folder_selection.calibration_list

    def set_reference_folder(self, file=None):

        if file is None:
            file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if file is not '':

            if os.path.exists(file + '/PROCESSED_IN.mat') and os.path.exists(file + '/PROCESSED_OUT.mat'):

                self.parent.LogDialog.add('Selected file : ' + file, 'info')
                self.reference_folder = file
                self.fit_folder_selection.set_folder(file)

            else:
                self.parent.LogDialog.add('PROCESSED data not found in foler ' + file, 'error')

        else:
            self.reference_folder = None

    def onStart(self):

        self.get_folder_list()

        if self.reference_folder is not None:

            if len(self.subfolders_to_process) > 1:

                path = os.path.dirname(self.subfolders_to_process[0])

                if self.mean_fit_option.isChecked() and os.path.exists(path + '/mean_fit.mat'):
                    reference_file = path + '/mean_fit.mat'
                    self.fit_folder_selection.set_folder(reference_file)
                    self.myLongTask = ops.ProcessCalibrationResults(self.subfolders_to_process, reference_file=reference_file)
                    self.myLongTask.notifyProgress.connect(self.onProgress)
                    self.process_folders.setDisabled(True)
                    self.plot_comparision.setDisabled(True)
                    self.myLongTask.start()

                if self.personal_fit_option.isChecked():
                    self.myLongTask = ops.ProcessCalibrationResults(self.subfolders_to_process)
                    self.myLongTask.notifyProgress.connect(self.onProgress)
                    self.process_folders.setDisabled(True)
                    self.plot_comparision.setDisabled(True)
                    self.myLongTask.start()

                elif os.path.exists(self.reference_folder + '/calibration_results.mat'):
                    self.myLongTask = ops.ProcessCalibrationResults(self.subfolders_to_process, reference_folder=self.reference_folder)
                    self.myLongTask.notifyProgress.connect(self.onProgress)
                    self.process_folders.setDisabled(True)
                    self.plot_comparision.setDisabled(True)
                    self.myLongTask.start()

                else:
                    self.parent.LogDialog.add('Reference folder is not recognized as a PROCESSED folder', 'error')

            else:
                self.parent.LogDialog.add('Nothing to process. Please add PROCESSED folders in the list', 'error')

        else:
            self.parent.LogDialog.add('Reference folder is not recognized as a PROCESSED folder', 'error')

    def onProgress(self, progress):

        if progress.find('done') != -1:
            self.parent.LogDialog.add(progress, 'info')
            self.process_folders.setDisabled(False)
            self.plot_comparision.setDisabled(False)
        else:
            self.parent.LogDialog.add(progress, 'process')

    def plot_comparision_act(self):
        self.get_folder_list()

        reference_file = sio.loadmat(self.subfolders_to_process[0] + '/calibration_results.mat', struct_as_record=False, squeeze_me=True)

        try:
            reference = reference_file['origin_file']

            ref_ok = True

            for folder in self.subfolders_to_process:

                if os.path.exists(folder):

                    if os.path.exists(folder + '/calibration_results.mat'):

                        reference_file = sio.loadmat(folder + '/calibration_results.mat',
                                                     struct_as_record=False, squeeze_me=True)
                        new_reference = reference_file['origin_file']

                        if new_reference != reference:
                            self.parent.LogDialog.add(
                                'Selected files do not have the same reference folder/file. Please reprocess them', 'error')
                            ref_ok = False

                    else:

                        self.parent.LogDialog.add(
                            'calibration_results.mat not found - Please use -Process- and try again', 'error')
                        ref_ok = False


            if ref_ok is True:
                self.PlotTab_IN.set_folder(self.subfolders_to_process, 'IN')
                self.PlotTab_OUT.set_folder(self.subfolders_to_process, 'OUT')
                #self.fit_folder_selection.set_folder(new_reference)
                #self.global_histogram_tab.set_folder(self.subfolders_to_process, 'OUT')
                #self.residuals_shape_tab.set_folder(self.subfolders_to_process, 'OUT')

        except KeyError:
            self.parent.LogDialog.add('origin_file Key not found in calibration_results.mat. Tru to reprocess all the files', 'error')

    def set_mean_option(self):

        self.get_folder_list()

        if self.mean_fit_option.isChecked():
            if len(self.subfolders_to_process) > 1:
                path = os.path.dirname(self.subfolders_to_process[0])
                self.fit_folder_selection.set_folder(path + '/mean_fit.mat')
                self.fit_folder_selection.label_select_folder.setDisabled(True)
            else:
                self.parent.LogDialog.add('Folder list is empty, please add PROCESSED folders', 'warning')
        else:
            self.fit_folder_selection.label_select_folder.setDisabled(False)
            self.fit_folder_selection.set_folder(self.reference_folder)

    def set_personal_option(self):

        self.get_folder_list()

        if self.personal_fit_option.isChecked():
            if len(self.subfolders_to_process) > 1:
                path = os.path.dirname(self.subfolders_to_process[0])
                self.fit_folder_selection.set_folder(path + '/mean_fit.mat')
                self.fit_folder_selection.label_select_folder.setDisabled(True)
            else:
                self.parent.LogDialog.add('Folder list is empty, please add PROCESSED folders', 'warning')
        else:
            self.fit_folder_selection.label_select_folder.setDisabled(False)
            self.fit_folder_selection.set_folder(self.reference_folder)


def main():
    app = QApplication(sys.argv)
    ex = QMultipleCalibrationAnalysis()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()








