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
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

from lib import utils
from lib import prairie
from gui.mplCanvas import mplCanvas
from lib import ops_processing as ops


PLOT_WIDTH = 7
PLOT_HEIGHT = 8


class QTabOPSProcessing(QWidget):

    def __init__(self, parent=None):

        super(QTabOPSProcessing, self).__init__(parent=None)

        self.main_widget = QStackedWidget(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        main_layout = QVBoxLayout(self.main_widget)
        self.plot = plot(self.main_widget, width=PLOT_WIDTH, height=PLOT_HEIGHT, dpi=100)
        self.navi_toolbar = NavigationToolbar(self.plot, self)
        main_layout.addWidget(self.navi_toolbar)
        main_layout.addWidget(self.plot)

        self.x_IN_A = np.ones(200)
        self.x_OUT_A = np.ones(200)
        self.y_IN_A = np.ones(200)
        self.y_OUT_A = np.ones(200)
        self.x_IN_B = np.ones(200)
        self.x_OUT_B = np.ones(200)
        self.y_IN_B = np.ones(200)
        self.y_OUT_B = np.ones(200)
        self.t1 = np.ones(200)
        self.t2 = np.ones(200)
        self.pd1 = np.ones(200)
        self.pd2 = np.ones(200)

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

    def set_t1(self, t1):
        self.t1 = t1

    def set_t2(self, t2):
        self.t2 = t2

    def set_pd1(self, pd1):
        self.pd1 = pd1

    def set_pd2(self, pd2):
        self.pd2 = pd2

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
        self.plot.t1 = self.t1
        self.plot.t2 = self.t2
        self.plot.pd1 = self.pd1
        self.plot.pd2 = self.pd2
        self.plot.compute_initial_figure()
        self.plot.draw()

    def reset(self):
        self.plot.fig.clear()
        self.plot.x_IN_A = np.ones(200)
        self.plot.x_OUT_A = np.ones(200)
        self.plot.y_IN_A = np.ones(200)
        self.plot.y_OUT_A = np.ones(200)
        self.plot.x_IN_B = np.ones(200)
        self.plot.x_OUT_B = np.ones(200)
        self.plot.y_IN_B = np.ones(200)
        self.plot.y_OUT_B = np.ones(200)
        self.plot.t1 = np.ones(200)
        self.plot.t2 = np.ones(200)
        self.plot.pd1 = np.ones(200)
        self.plot.pd2 = np.ones(200)
        self.plot.compute_initial_figure()
        self.plot.draw()


class plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):

        self.x_IN_A = np.ones(200)
        self.x_OUT_A = np.ones(200)
        self.y_IN_A = np.ones(200)
        self.y_OUT_A = np.ones(200)
        self.x_IN_B = np.ones(200)
        self.x_OUT_B = np.ones(200)
        self.y_IN_B = np.ones(200)
        self.y_OUT_B = np.ones(200)

        self.t1 = np.ones(200)
        self.t2 = np.ones(200)

        self.pd1 = np.ones(200)
        self.pd2 = np.ones(200)


        self.ax1 = 0

        self.in_or_out = 'IN'

        self.foc_marker = 0

        self.color = 0

        self.focus = 0

        super(plot, self).__init__(parent, width, height, dpi)

    def compute_initial_figure(self):

        self.fig.clear()
        ax1 = self.fig.add_subplot(321)
        ax1.set_title('OPS processing SA - IN', loc='left')
        ax1.set_xlabel('Time [ms]')
        ax1.set_ylabel('Normalized amplitude [a.u]')

        ax2 = self.fig.add_subplot(323)  # , sharex=ax1)
        ax2.set_title('OPS processing SB - IN', loc='left')
        ax2.set_xlabel('Time [ms]')
        ax2.set_ylabel('Normalized amplitude [a.u]')

        ax3 = self.fig.add_subplot(322)
        ax3.set_title('OPS processing SA - OUT', loc='left')
        ax3.set_xlabel('Time [ms]')
        ax3.set_ylabel('Normalized amplitude [a.u]')

        ax4 = self.fig.add_subplot(324)  # , sharex = ax3)
        ax4.set_title('OPS processing SB - OUT', loc='left')
        ax4.set_xlabel('Time [ms]')
        ax4.set_ylabel('Normalized amplitude [a.u]')

        ax5 = self.fig.add_subplot(325)  # ,sharex=ax1)
        ax5.set_title('Processing Laser - IN', loc='left')
        ax5.set_xlabel('Time [ms]')
        ax5.set_ylabel('Normalized amplitude [a.u]')

        ax6 = self.fig.add_subplot(326)  # , sharex=ax3)
        ax6.set_title('Processing Laser - OUT', loc='left')
        ax6.set_xlabel('Time [ms]')
        ax6.set_ylabel('Normalized amplitude [a.u]')
        self.fig.tight_layout()

        color_IN = '#018BCF'
        color_OUT = '#CF2A1B'
        black = [0.3, 0.3, 0.3]

        parameter_file = 'data/parameters.cfg'
        Dec = 10

        if len(self.x_IN_A) != 200:

            # SENSOR A IN
            # -----------
            try:
                P = ops.process_position(self.x_IN_A,  parameter_file, self.t1[0], return_processing=True, INOUT='IN')
                ax1.axhspan(0, P[8], color='black', alpha=0.05)
                ax1.plot( P[0][::Dec], P[1][::Dec], linewidth=0.5)
                ax1.plot( P[2], P[3], '.', markersize=2)
                ax1.plot( P[4], P[5], '.', markersize=2)
                ax1.plot( P[6], P[7], '-', linewidth=0.5, color=black)
                # Added by Jose --> Visually identify references detection
                refX = P[9]
                ax1.axvline(x=refX, color = 'red')
                # ----
            except:
                ax1.plot(1e3*self.t1[::Dec], self.x_IN_A[::Dec], linewidth=0.5)
                print('Error processing Sensor A_IN')
            ax1.legend(['OPS data', 'Maxs', 'Mins', 'Threshold', 'Reference'])
            prairie.style(ax1)

            # SENSOR B IN
            # -----------
            try:
                P = ops.process_position(self.y_IN_A, parameter_file, self.t1[0], return_processing=True, INOUT='IN')
                ax2.axhspan(0, P[8], color='black', alpha=0.05)
                ax2.plot( P[0][::Dec], P[1][::Dec], linewidth=0.5)
                ax2.plot( P[2], P[3], '.', markersize=2)
                ax2.plot( P[4], P[5], '.', markersize=2)
                ax2.plot( P[6], P[7], '-', linewidth=0.5, color=black)
                # Added by Jose --> Visually identify references detection
                refX = P[9]
                ax2.axvline(x=refX, color = 'red')
                # ----
            except:
                ax2.plot(1e3*self.t1, self.y_IN_A, linewidth=0.5)
                print('Error processing Sensor B_IN')
            prairie.style(ax2)

            # SENSOR A OUT
            # ------------
            try:
                P = ops.process_position(self.x_OUT_A, parameter_file, self.t2[0], return_processing=True, INOUT='OUT')
                ax3.axhspan(0, P[8], color='black', alpha=0.05)
                ax3.plot( P[0][::Dec], P[1][::Dec], linewidth=0.5)
                ax3.plot( P[2], P[3], '.', markersize=2)
                ax3.plot( P[4], P[5], '.', markersize=2)
                ax3.plot( P[6], P[7], '-', linewidth=0.5, color=black)
                # Added by Jose --> Visually identify references detection
                refX = P[9]
                ax3.axvline(x=refX, color = 'red')
                # ----
            except:
                ax3.plot(1e3*self.t2[::Dec], self.x_OUT_A[::Dec], linewidth=0.5)
                print('Error processing Sensor A_OUT')
            prairie.style(ax3)

            # SENSOR B OUT
            # ------------
            try:
                P = ops.process_position(self.y_OUT_A, parameter_file, self.t2[0], return_processing=True, INOUT='OUT')
                ax4.axhspan(0, P[8], color='black', alpha=0.05)
                ax4.plot( P[0][::Dec], P[1][::Dec], linewidth=0.5)
                ax4.plot( P[2], P[3], '.', markersize=2)
                ax4.plot( P[4], P[5], '.', markersize=2)
                ax4.plot( P[6], P[7], '-', linewidth=0.5, color=black)
                # Added by Jose --> Visually identify references detection
                refX = P[9]
                ax4.axvline(x=refX, color = 'red')
                # ----
            except:
                ax4.plot(1e3*self.t2, self.y_OUT_A, linewidth=0.5)
                print('Error processing Sensor B_OUT')
            prairie.style(ax4)

            # PHOTODIODE IN
            # -------------
            ax5.plot(1e3 * self.t1[::Dec], self.pd1[::Dec], linewidth=1)
            try:
                occ_IN = ops.find_occlusions(self.pd1, IN=True, StartTime=self.t1[0], return_processing=True)
                ax5.plot(1e3 * occ_IN[2][::Dec], occ_IN[3][::Dec], linewidth=1)
                ax5.axvline(x = 1e3*occ_IN[0][0], color = 'red')
                ax5.axvline(x = 1e3*occ_IN[0][1], color = 'red')
                ax5.legend(['PD data Raw', 'PD data Filt.' ,'Detected occlusions'])
            except:
                print('Error detecting Occlusions IN')
            prairie.style(ax5)

            # PHOTODIODE OUT
            # --------------
            ax6.plot(1e3 * self.t2[::Dec], self.pd2[::Dec], linewidth=1)
            try:
                occ_OUT = ops.find_occlusions(self.pd2, IN=False, StartTime=self.t2[0], return_processing=True)
                ax6.plot(1e3 * occ_OUT[2][::Dec], occ_OUT[3][::Dec], linewidth=1)
                ax6.axvline(x = 1e3*occ_OUT[0][0], color = 'red')
                ax6.axvline(x = 1e3*occ_OUT[0][1], color = 'red')
            except:
                print('Error detecting Occlusions OUT')
            prairie.style(ax6)

            self.fig.tight_layout()
