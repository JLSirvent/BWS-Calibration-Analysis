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
import configparser

from lib import utils
from numpy import arange
from PyQt5 import QtGui, QtCore
from gui import QFolderSelectionWidget
from PyQt5.QtWidgets import QWidget, QLineEdit, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QFileDialog, QApplication, QComboBox, QGroupBox, QListWidget, QRadioButton


def cut(off, data):
    return data[off:data.size - off]


class QMultipleFolderSelection(QWidget):
    def __init__(self, parent=None):
        '''
        QWidget to do a multiple folder selection
        :param parent:
        '''

        super(QMultipleFolderSelection, self).__init__(parent)

        self.parent = parent

        self.folder_selection = QFolderSelectionFrom()

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.folder_selection)

        self.setFixedWidth(250)
        self.setFixedHeight(250)

        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.mainLayout)

    def set_actual_folder(self, file=None):

        if file is None:
            file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if file is not '':
            self.folder_selection.set_actual_folder(file)

    def append_folder_to(self):
        self.folder_selection.ProcessButton.setEnabled(True)
        self.folder_to.append(self.actual_selected_folder_from)

    def append_all_folder_to(self):
        self.folder_to.subfolder_list = self.folder_selection.subfolder_list
        self.folder_to.actualise()
        self.folder_to.append(self.actual_selected_folder_from)

    def retire_folder_to(self):
        self.folder_to.retire_actual()

    def set_actual_selected_folder(self, index):
        actual_index = index.row()
        self.actual_selected_folder_from = self.folder_selection.subfolder_list[actual_index]

    def get_folder_list(self):
        return self.folder_to.subfolder_list

class QFolderSelectionFrom(QWidget):

    def __init__(self, parent=None):
        super(QFolderSelectionFrom, self).__init__(parent)

        self.parent = parent

        self.mainLayout = QVBoxLayout()

        self.actual_folder = ''
        self.subfolder_list = ''
        self.actual_calibration_folder = ''
        self.calibration_list = []

        # ADDING COMBO BOX WITH AVAILABLE SCANNERS
        # ---------------------------------------------
        # We use a parameter file
        #parameter_file = utils.resource_path()
        config = configparser.RawConfigParser()
        config.read('data/parameters.cfg')
        self.directory = eval(config.get('Application parameters', 'CalibrationsDirectory'))

        # Actions
        folder_list = []
        for name in os.listdir(self.directory):
            if os.path.isdir(os.path.join(self.directory, name)):
                folder_list.append(name)

        self.scanner_selection_cb = QComboBox()
        self.scanner_selection_cb.addItem('Select Scanner:')
        self.scanner_selection_cb.addItems(folder_list)
        self.scanner_selection_cb.currentIndexChanged.connect(self.set_actual_scanner_folder)

        self.calibration_selection_cb = QComboBox()
        self.calibration_selection_cb.setEnabled(False)
        self.calibration_selection_cb.currentIndexChanged.connect(self.set_actual_calibration_folder)

        self.addButton = QPushButton('Add Calibration')
        self.addButton.setEnabled(False)

        self.addButton.clicked.connect(self.add_calibration_to_list)

        self.clearButton = QPushButton('Clear List')
        self.clearButton.clicked.connect(self.clear_calibration_list)

        self.calibration_list_widget = QListWidget()
        self.calibration_list_widget.resize(300,120)


        self.radio_polynomial = QRadioButton('Polynomial')
        self.radio_polynomial.setChecked(True)
        self.polynomial_order_lbl = QLabel('Order:')
        self.polynomial_order_lbl.setFixedWidth(35)

        self.polynomial_order = QLineEdit('5')
        self.polynomial_order.setFixedWidth(25)
        self.radio_sinusoidal = QRadioButton('Sinusoidal')

        self.radio_independent=QRadioButton('Individual Fits')
        self.radio_global = QRadioButton('Global Fit')
        self.radio_independent.setChecked(True)

        self.ProcessButton = QPushButton('PROCESS analysis')
        self.ProcessButton.setEnabled(False)

        self.radio_polynomial.toggled.connect(self.typeSelection)
        # ---------------------------------------------

        self.fit_type2_box = QGroupBox('Behavior')
        self.fit_type2_box_layout = QHBoxLayout(self)
        self.fit_type2_box_layout.addWidget(self.radio_independent)
        self.fit_type2_box_layout.addWidget(self.radio_global)
        self.fit_type2_box.setLayout(self.fit_type2_box_layout)

        self.fit_type1_box = QGroupBox('Type')
        self.fit_type1_box_layout = QVBoxLayout(self)
        self.fit_type1_box_layout1 = QHBoxLayout(self)
        self.fit_type1_box_layout1.addWidget(self.radio_polynomial)
        self.fit_type1_box_layout1.addWidget(self.radio_sinusoidal)
        self.fit_type1_box_layout2 = QHBoxLayout(self)
        self.fit_type1_box_layout2.setAlignment(QtCore.Qt.AlignLeft)
        self.fit_type1_box_layout2.addWidget(self.polynomial_order_lbl)
        self.fit_type1_box_layout2.addWidget(self.polynomial_order)
        self.fit_type1_box_layout.addLayout(self.fit_type1_box_layout1)
        self.fit_type1_box_layout.addLayout(self.fit_type1_box_layout2)
        self.fit_type1_box.setLayout(self.fit_type1_box_layout)

        self.fit_type0_box = QGroupBox('Fit Options')
        self.fit_type0_box_layout = QVBoxLayout(self)
        self.fit_type0_box_layout.addWidget(self.fit_type1_box)
        self.fit_type0_box_layout.addWidget(self.fit_type2_box)
        self.fit_type0_box.setLayout(self.fit_type0_box_layout)

        self.select_box = QGroupBox('Calibrations Selection')
        self.select_box_layout = QVBoxLayout(self)
        #self.select_box_layout.addStretch(1)
        self.select_box_layout.addWidget(self.scanner_selection_cb)
        self.select_box_layout.addWidget(self.calibration_selection_cb)

        self.select_box_layout2 = QHBoxLayout(self)
        self.select_box_layout2.addWidget(self.addButton)
        self.select_box_layout2.addWidget(self.clearButton)

        self.select_box_layout.addLayout(self.select_box_layout2)
        self.select_box_layout.addWidget(self.calibration_list_widget)
        self.select_box_layout.addWidget(self.fit_type0_box)
        self.select_box_layout.addWidget(self.ProcessButton)

        self.select_box.setLayout(self.select_box_layout)
        self.mainLayout.addWidget(self.select_box)

        self.setLayout(self.mainLayout)
        #self.setFixedHeight(600)

    def typeSelection(self):
        self.polynomial_order.setEnabled(self.radio_polynomial.isChecked())
        self.polynomial_order_lbl.setEnabled(self.radio_polynomial.isChecked())

    def set_actual_scanner_folder(self):
        try:
            full_directory = self.directory + self.scanner_selection_cb.currentText() + '/ProcessedData'
            self.calibration_selection_cb.clear()
            if os.path.exists(full_directory):
                folder_list = os.listdir(full_directory)
                self.calibration_selection_cb.addItem('Select Calibration:')
                for folder in folder_list:
                    self.calibration_selection_cb.addItem(folder.split(' ')[0])
                self.calibration_selection_cb.setEnabled(True)
        except:
            print('Error set_actual_scanner_folder')

    def set_actual_calibration_folder(self):

        if self.calibration_selection_cb.currentIndex() == 0:
            self.addButton.setEnabled(False)
        else:
            self.addButton.setEnabled(True)

        try:
            full_directory = self.directory + self.scanner_selection_cb.currentText() + '/ProcessedData/' + self.calibration_selection_cb.currentText() + ' PROCESSED'
            if os.path.exists(full_directory):
                self.actual_calibration_folder = full_directory
        except:
            print('Error set_actual_calibration_folder')

    def add_calibration_to_list(self):
        self.calibration_list.append(self.actual_calibration_folder)
        self.update_calibration_list()
        self.ProcessButton.setEnabled(True)

    def clear_calibration_list(self):
        self.calibration_list = []
        self.update_calibration_list()
        self.ProcessButton.setEnabled(False)

    def update_calibration_list(self):
        self.calibration_list_widget.clear()
        for calibration in self.calibration_list:
            CalSplit = calibration.split('/ProcessedData/')
            self.calibration_list_widget.addItem(CalSplit[1].split(' PROCESSED')[0])

def main():
    app = QApplication(sys.argv)
    ex = QMultipleFolderSelection()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()








