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

import numpy as np
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

from lib import prairie
from gui.mplCanvas import mplCanvas

PLOT_WIDTH = 7.5
PLOT_HEIGHT = 8


class QTab(QWidget):

    def __init__(self, title, xlabel, ylabel, parent=None):

        super(QTab, self).__init__(parent=None)

        self.main_widget = QWidget(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        main_layout = QVBoxLayout(self.main_widget)
        self.plot = plot(self.main_widget, width=PLOT_WIDTH, height=PLOT_HEIGHT, dpi=100)

        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel

        self.plot.title = self.title
        self.plot.xlabel = self.xlabel
        self.plot.ylabel = self.ylabel

        self.navi_toolbar = NavigationToolbar(self.plot, self)
        main_layout.addWidget(self.navi_toolbar)
        main_layout.addWidget(self.plot)

        self.x_IN_A = [0, 1]
        self.x_OUT_A = [0, 1]
        self.y_IN_A = [0, 1]
        self.y_OUT_A = [0, 1]
        self.x_IN_B = [0, 1]
        self.x_OUT_B = [0, 1]
        self.y_IN_B = [0, 1]
        self.y_OUT_B = [0, 1]
        self.occ_time = [0,0]

        self.setLayout(main_layout)

    def set_x_IN_A(self, x1):
        self.x_IN_A = x1

    def set_y_IN_A(self, y1):
        self.y_IN_A = y1

    def set_x_OUT_A(self, x2):
        self.x_OUT_A = x2

    def set_y_OUT_A(self, y2):
        self.y_OUT_A = y2
        
    def set_x_IN_B(self, x1):
        self.x_IN_B = x1

    def set_y_IN_B(self, y1):
        self.y_IN_B = y1

    def set_x_OUT_B(self, x2):
        self.x_OUT_B = x2

    def set_y_OUT_B(self, y2):
        self.y_OUT_B = y2

    def set_occ_time(self,occ_time):
        self.occ_time = occ_time

    def actualise_ax(self):
        self.plot.fig.clear()
        self.plot.x_IN_A = self.x_IN_A
        self.plot.x_OUT_A = self.x_OUT_A
        self.plot.y_IN_A = self.y_IN_A
        self.plot.y_OUT_A = self.y_OUT_A
        self.plot.x_IN_B = self.x_IN_B
        self.plot.x_OUT_B = self.x_OUT_B
        self.plot.y_IN_B = self.y_IN_B
        self.plot.y_OUT_B = self.y_OUT_B
        self.plot.occ_time = self.occ_time
        self.plot.title = self.title
        self.plot.xlabel = self.xlabel
        self.plot.ylabel = self.ylabel
        self.plot.compute_initial_figure()
        self.plot.draw()

class plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):

        self.x_IN_A = [0, 1]
        self.x_OUT_A = [0, 1]
        self.y_IN_A = [0, 1]
        self.y_OUT_A = [0, 1]
        
        self.x_IN_B = [0, 1]
        self.x_OUT_B = [0, 1]
        self.y_IN_B = [0, 1]
        self.y_OUT_B = [0, 1]
        self.occ_time = [0, 0]

        self.title = ''
        self.xlabel = ''
        self.ylabel = ''

        super(plot, self).__init__(parent, width, height, dpi)

    def compute_initial_figure(self):

        self.fig.clear()
        ax1 = self.fig.add_subplot(1, 2, 1)
        ax1.set_title(self.title, loc='left')
        ax1.set_xlabel(self.xlabel)
        ax1.set_ylabel(self.ylabel)

        ax2 = self.fig.add_subplot(1, 2, 2)
        ax2.set_title(self.title, loc='left')
        ax2.set_xlabel(self.xlabel)
        ax2.set_ylabel(self.ylabel)

        self.fig.tight_layout()

        if self.occ_time != [0, 0]:
            Idx = np.where(self.x_IN_A > self.occ_time[0])[0][0]
            ax1.axvline(self.x_IN_A[Idx], color='red', linestyle = '--', alpha = 0.6, label='Laser Cross:\n{:.2f}'.format(self.y_IN_A[Idx]))
            ax1.axhline(self.y_IN_A[Idx], color='red', linestyle = '--', alpha = 0.6)
            Idx = np.where(self.x_OUT_A < self.occ_time[1])[0][0]
            ax2.axvline(self.x_OUT_A[Idx], color='red', linestyle = '--', alpha = 0.6,label='Laser Cross:\n{:.2f}'.format(self.y_OUT_A[Idx]))
            ax2.axhline(self.y_OUT_A[Idx], color='red',linestyle = '--', alpha = 0.6)

        ax1.plot(self.x_IN_A, self.y_IN_A, color='#004466', linewidth=1, label='Sensor A')
        try:
            ax1.plot(self.x_IN_B, self.y_IN_B, color='#018BCF', linewidth=1, label='Sensor B')
        except:
            pass
        ax1.set_xlim([min(self.x_IN_A), max(self.x_IN_A)])


        ax2.plot(self.x_OUT_A, self.y_OUT_A, color='#6E160E', linewidth=1, label='Sensor A')
        try:
            ax2.plot(self.x_OUT_B, self.y_OUT_B, color='#CF2A1B', linewidth=1, label='Sensor B')
        except:
            pass
        ax2.set_xlim([min(self.x_OUT_A), max(self.x_OUT_A)])

        maxy = np.max([np.max(self.y_IN_A),np.max(self.y_OUT_A)])
        miny = np.min([np.min(self.y_IN_A),np.min(self.y_OUT_A)])

        margin = 0.05
        maxy = maxy + maxy*margin
        miny = miny - np.abs(miny*margin)

        ax2.legend(loc = 'upper right')
        ax1.legend(loc = 'upper left')
        ax1.set_ylim(miny,maxy)
        ax2.set_ylim(miny,maxy)
        prairie.style(ax1)
        prairie.style(ax2)

