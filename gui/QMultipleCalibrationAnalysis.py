#   --------------------------------------------------------------------------
# Copyright (c) <2019> <Jose Luis Sirvent>
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
import numpy as np
from matplotlib import pyplot as plt

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget,QPushButton, QCheckBox, QLabel, QHBoxLayout, QTabWidget, QVBoxLayout, QFileDialog, QApplication

from gui import Calibration
from gui import QMultipleFolderSelection, QTabMultipleCalibrationPlot, QTabSpeeds_Positions

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
        self.calibration = []

        self.PlotTab = QTabMultipleCalibrationPlot.QTabMultipleCalibrationPlot()
        self.plot_positions = QTabSpeeds_Positions.QTabSpeeds_Positions('Position ', 'Time [ms]', 'Angular Position [rad]', 1)
        self.plot_speeds =  QTabSpeeds_Positions.QTabSpeeds_Positions('Speed ', 'Time [ms]', 'Angular speed [rad/s]', 10)

        self.folder_selection = QMultipleFolderSelection.QMultipleFolderSelection(parent=self)
        self.folder_selection.setFixedHeight(400)

        self.multipleanalysistab = QTabWidget()
        self.multipleanalysistab.addTab(self.PlotTab, 'Calibration Comparison')
        self.multipleanalysistab.addTab(self.plot_positions, 'Position Profiles')
        self.multipleanalysistab.addTab(self.plot_speeds, 'Speed Profiles')

        self.super_layout = QHBoxLayout()
        self.super_layout.addWidget(self.folder_selection, 0, QtCore.Qt.AlignTop)
        self.super_layout.addWidget(self.multipleanalysistab)

        self.setLayout(self.super_layout)

        self.folder_selection.folder_selection.ProcessButton.clicked.connect(self.Update_Comparison)

    def Update_Comparison(self):

        fittype = [0,0,0]

        if self.folder_selection.folder_selection.radio_polynomial.isChecked():
            fittype[0] = 0
        else:
            fittype[0] = 1

        fittype[1] = int(float(self.folder_selection.folder_selection.polynomial_order.text()))

        if self.folder_selection.folder_selection.radio_independent.isChecked():
            fittype[2] = 0
        else:
            fittype[2] = 1

        Speeds = [[],[]]
        Positions = [[],[]]
        Times = [[],[]]
        Calib_x = [[],[]]
        Calib_y = [[],[]]
        Labels = []

        for folder in self.folder_selection.folder_selection.calibration_list:
            tmp = folder.split(' ')[0]
            tmp = tmp.split('/')[-1]
            Labels.append(tmp)

            self.calibration = Calibration.Calibration(folder)

            # Retrieve Motion info
            Speeds[0].append(1e3*self.calibration.speed_IN_SA[1])
            Speeds[1].append(-1e3*self.calibration.speed_OUT_SA[1])
            Positions[0].append(self.calibration.angular_position_SA_IN[1])
            Positions[1].append(self.calibration.angular_position_SA_OUT[1])
            Times[0].append(self.calibration.time_IN_SA[1])
            Times[1].append(self.calibration.time_OUT_SA[1])

            # Retrieve Calibration data
            Idx = np.where(self.calibration.data_valid == 1)
            Calib_x[0].append(self.calibration.occlusion_IN[Idx])
            Calib_x[1].append(self.calibration.occlusion_OUT[Idx])
            Calib_y[0].append(self.calibration.laser_position_IN[Idx])
            Calib_y[1].append(self.calibration.laser_position_OUT[Idx])

        self.PlotTab.set_folder(Calib_x,Calib_y,Labels, fittype[0], fittype[1], fittype[2])

        self.actualise_multiple_Qtab(self.plot_positions,
                                     x1=Times[0][:],
                                     y1=Positions[0][:],
                                     b1=[0,0],
                                     x2=Times[1][:],
                                     y2=Positions[1][:],
                                     b2=[0,0],
                                     legends =Labels)

        self.actualise_multiple_Qtab(self.plot_speeds,
                                     x1=Times[0][:],
                                     y1=Speeds[0][:],
                                     b1=[0,0],
                                     x2=Times[1][:],
                                     y2=Speeds[1][:],
                                     b2=[0,0],
                                     legends=Labels)


    def actualise_multiple_Qtab(self, QTab, x1, y1, x2, y2, b1, b2, legends):
        QTab.set_x_IN(x1)
        QTab.set_y_IN(y1)
        QTab.set_B_IN(b1)
        QTab.set_x_OUT(x2)
        QTab.set_y_OUT(y2)
        QTab.set_B_OUT(b2)
        QTab.set_legends(legends)
        QTab.actualise_ax()


def main():
    app = QApplication(sys.argv)
    ex = QMultipleCalibrationAnalysis()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()








