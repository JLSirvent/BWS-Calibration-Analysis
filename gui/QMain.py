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

import sys

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QWidget, QApplication
from PyQt5 import QtGui, QtCore

from lib import utils
from gui import QLogDialog
from gui import QProcessedAnalysisTab
from gui import QTabFileProcessing
from gui import QMultipleCalibrationAnalysis
from gui import QTabSingleScanAnalysis


class QMain(QWidget):

    def __init__(self, parent=None):
        '''
        Main Widget of the window to display all the tab
        :param parent:
        '''

        super(QMain, self).__init__(parent)

        self.setWindowTitle('OPS Processing')

        self.mainLayout = QVBoxLayout()

        self.header = QHBoxLayout()

        self.Title = QLabel('BWS protoype analysis tool')
        f = QtGui.QFont('Arial', 20, QtGui.QFont.Bold)
        f.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.Title.setFont(QtGui.QFont('Arial', 20, QtGui.QFont.Bold))
        self.Title.setContentsMargins(10, 10, 10, 10)

        self.CERN_logo = QLabel()

        self.CERN_logo_image = QtGui.QPixmap(utils.resource_path("images/cern_logo.jpg"))

        self.CERN_logo_image = self.CERN_logo_image.scaledToHeight(60, QtCore.Qt.SmoothTransformation)

        self.CERN_logo.setPixmap(self.CERN_logo_image)

        self.header.addWidget(self.Title)
        self.header.addWidget(self.CERN_logo, 0, QtCore.Qt.AlignRight)

        self.global_tab = QTabWidget()
        self.ProcessedAnalysisisTab = QProcessedAnalysisTab.QProcessedAnalysisTab(self)
        self.TabFileProcessing = QTabFileProcessing.QTabFileProcessing(self)
        self.MultipleCalibrationAnalysis = QMultipleCalibrationAnalysis.QMultipleCalibrationAnalysis(self)
        self.SingleScanAnalysis = QTabSingleScanAnalysis.QTabSingleScanAnalysis(self)

        self.LogDialog = QLogDialog.QLogDialog()

        self.global_tab.addTab(self.ProcessedAnalysisisTab, "Single calibration analysis")
        self.global_tab.addTab(self.MultipleCalibrationAnalysis, "Multiple calibration analysis")
        self.global_tab.addTab(self.SingleScanAnalysis, "Scan raw data analysis")
        self.global_tab.addTab(self.TabFileProcessing, "Calibration processing")
        self.mainLayout.addLayout(self.header)
        self.mainLayout.addWidget(self.global_tab)
        self.mainLayout.addWidget(self.LogDialog)

        self.setLayout(self.mainLayout)

        # Window properties
        self.setWindowTitle('OPS Processing')
        self.setMinimumSize(1200, 900)

    def closeEvent(self, event):
        print("Closing the app")
        self.deleteLater()

def main():
    app = QApplication(sys.argv)
    ex = QMain()
    ex.move(100, 100)
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()








