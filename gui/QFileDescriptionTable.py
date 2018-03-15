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

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QPushButton, QTableWidget, QAbstractItemView, QHeaderView, QVBoxLayout


class QFileDescriptionTable(QWidget):

    def __init__(self, parent=None):
        '''
        Table that allow to explore all the scans from a calibration
        :param parent:
        '''

        super(QFileDescriptionTable, self).__init__(parent)

        self.main_widget = QWidget(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.main_layout = QVBoxLayout(self.main_widget)

        #self.dump_button = QPushButton('Dump this scan')
        #self.set_parameters_button = QPushButton('Set processing Parameters')
        self.save_and_update = QPushButton('Save and update validity')
        self.see_raw_button = QPushButton('Open Selected File')

        #self.dump_button.setFixedWidth(278)
        #self.set_parameters_button.setFixedWidth(278)
        self.save_and_update.setFixedWidth(278)
        self.see_raw_button.setFixedWidth(278)

        self.table = QTableWidget()
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.horizontalHeader().setFont(QtGui.QFont('Arial', 7))

        self.table.setFixedWidth(278)

        self.main_layout.addWidget(self.table)
        self.main_layout.addWidget(self.save_and_update)
        self.main_layout.addWidget(self.see_raw_button)
        #self.main_layout.addWidget(self.dump_button)
        #self.main_layout.addWidget(self.set_parameters_button)


        self.setLayout(self.main_layout)

        self.selection_change = pyqtSignal()