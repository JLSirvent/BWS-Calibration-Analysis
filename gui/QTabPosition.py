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

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

from lib import prairie
from gui.mplCanvas import mplCanvas


class QTabPosition(QWidget):

    def __init__(self, parent=None):

        super(QTabPosition, self).__init__(parent=None)

        self.main_widget = QWidget(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        main_layout = QVBoxLayout(self.main_widget)
        self.ax1 = ecc_plot(self.main_widget, width=9, height=6, dpi=100)
        self.navi_toolbar = NavigationToolbar(self.ax1, self)
        main_layout.addWidget(self.navi_toolbar)
        main_layout.addWidget(self.ax1)

        self.positions_IN = 0
        self.positions_OUT = 0

        self.time_IN = 0
        self.time_OUT = 0

    def set_positions_IN(self, positions_IN):
        self.positions_IN = positions_IN

    def set_positions_OUT(self, positions_OUT):
        self.positions_OUT = positions_OUT

    def set_time_IN(self, time_IN):
        self.time_IN = time_IN

    def set_time_OUT(self, time_OUT):
        self.time_OUT = time_OUT

    def actualise_ax(self):
        self.ax1.positions_IN = self.positions_IN
        self.ax1.positions_OUT = self.positions_OUT
        self.ax1.time_IN = self.time_IN
        self.ax1.time_OUT = self.time_OUT
        self.ax1.compute_initial_figure()


class ecc_plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):

        self.positions_IN = 0
        self.positions_OUT = 0

        self.time_IN = 0
        self.time_OUT = 0

        super(ecc_plot, self).__init__(parent, width, height, dpi)

    def compute_initial_figure(self):

        ax1 = self.fig.add_subplot(2, 1, 1)
        ax1.set_title('Position error and time compensation - IN', loc='left')
        ax1.set_xlabel('Angular position (rad)')
        ax1.set_ylabel('Position error (rad)')
        ax1.plot(self.positions_IN, self.time_IN)
        prairie.style(ax1)
        # print(self.positions_IN)

        ax2 = self.fig.add_subplot(2, 1, 2)
        ax2.set_title('Position error and time compensation - OUT', loc='left')
        ax2.set_xlabel('Angular position [rad]')
        ax2.set_ylabel('Position error [rad]')
        ax2.plot(self.positions_OUT, self.time_OUT)
        prairie.style(ax2)

        self.fig.tight_layout()
