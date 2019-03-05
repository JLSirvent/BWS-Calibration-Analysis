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

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget,QPushButton, QCheckBox, QLabel, QHBoxLayout, QTabWidget, QVBoxLayout, QFileDialog, QApplication

from gui import QMultipleFolderSelection
from gui import QTabMultipleCalibrationPlot

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

        self.PlotTab = QTabMultipleCalibrationPlot.QTabMultipleCalibrationPlot()

        self.folder_selection = QMultipleFolderSelection.QMultipleFolderSelection(parent=self)
        self.folder_selection.setFixedHeight(400)

        self.multipleanalysistab = QTabWidget()
        self.multipleanalysistab.addTab(self.PlotTab, 'Comparision analysis')

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

        self.PlotTab.set_folder(self.folder_selection.folder_selection.calibration_list, fittype[0], fittype[1], fittype[2])

def main():
    app = QApplication(sys.argv)
    ex = QMultipleCalibrationAnalysis()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()








