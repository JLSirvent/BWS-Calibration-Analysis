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

        color_IN = '#018BCF'
        color_OUT = '#CF2A1B'
        black = [0.3, 0.3, 0.3]

        parameter_file = utils.resource_path('data/parameters.cfg')

        if len(self.x_IN_A) == 200:

            ax1 = self.fig.add_subplot(221)
            ax1.plot(self.t1, self.x_IN_A, linewidth=0.5)
            prairie.style(ax1)

            ax2 = self.fig.add_subplot(222)
            ax2.plot(self.t1, self.y_IN_A, linewidth=0.5)
            prairie.style(ax2)

            ax3 = self.fig.add_subplot(223, sharex = ax1)
            ax3.plot(self.t2, self.x_OUT_A, linewidth=0.5)
            prairie.style(ax3)

            ax4 = self.fig.add_subplot(224, sharex = ax2)
            ax4.plot(self.t2, self.y_OUT_A, linewidth=0.5)
            prairie.style(ax4)

            self.fig.tight_layout()

        else:
            # SENSOR A IN
            # -----------
            ax1 = self.fig.add_subplot(321)
            try:
                P = ops.process_position(self.x_IN_A,  parameter_file, self.t1[0], return_processing=True, INOUT='IN')
                ax1.axhspan(0, P[8], color='black', alpha=0.05)
                ax1.plot( P[0], P[1], linewidth=0.5)
                ax1.plot( P[2], P[3], '.', markersize=2)
                ax1.plot( P[4], P[5], '.', markersize=2)
                ax1.plot( P[6], P[7], '-', linewidth=0.5, color=black)
                # Added by Jose --> Visually identify references detection
                refX = P[9]
                refY = P[1][np.where(P[0] > P[9])[0][0]]
                ax1.plot( refX, refY, '.', markersize=5, color = '#f93eed')
                # ----
            except:
                ax1.plot(1e3*self.t1, self.x_IN_A, linewidth=0.5)
                print('Error processing Sensor A_IN')
            ax1.set_title('OPS processing SA - IN', loc='left')
            ax1.set_xlabel('Time (ms)')
            ax1.set_ylabel('Normalized amplitude')
            ax1.legend(['OPS data', 'Maxs', 'Mins', 'Threshold'])
            prairie.style(ax1)

            # SENSOR B IN
            # -----------
            ax2 = self.fig.add_subplot(323, sharex=ax1)
            try:
                P = ops.process_position(self.y_IN_A, parameter_file, self.t1[0], return_processing=True, INOUT='IN')
                ax2.axhspan(0, P[8], color='black', alpha=0.05)
                ax2.plot( P[0], P[1], linewidth=0.5)
                ax2.plot( P[2], P[3], '.', markersize=2)
                ax2.plot( P[4], P[5], '.', markersize=2)
                ax2.plot( P[6], P[7], '-', linewidth=0.5, color=black)
                # Added by Jose --> Visually identify references detection
                refX = P[9]
                refY = P[1][np.where(P[0] > P[9])[0][0]]
                ax2.plot( refX, refY, '.', markersize=5, color = '#f93eed')
                # ----
            except:
                ax2.plot(1e3*self.t1, self.y_IN_A, linewidth=0.5)
                print('Error processing Sensor B_IN')

            ax2.set_title('OPS processing SB - IN', loc='left')
            ax2.set_xlabel('Time (ms)')
            ax2.set_ylabel('Normalized amplitude')
            prairie.style(ax2)

            # SENSOR A OUT
            # ------------
            ax3 = self.fig.add_subplot(322)
            try:
                P = ops.process_position(self.x_OUT_A, parameter_file, self.t2[0], return_processing=True, INOUT='OUT')
                ax3.axhspan(0, P[8], color='black', alpha=0.05)
                ax3.plot( P[0], P[1], linewidth=0.5)
                ax3.plot( P[2], P[3], '.', markersize=2)
                ax3.plot( P[4], P[5], '.', markersize=2)
                ax3.plot( P[6], P[7], '-', linewidth=0.5, color=black)
                # Added by Jose --> Visually identify references detection
                refX = P[9]
                refY = P[1][np.where(P[0] > P[9])[0][0]]
                ax3.plot(refX, refY, '.', markersize=5, color = '#f93eed')
                # ----
            except:
                ax3.plot(1e3*self.t2, self.x_OUT_A, linewidth=0.5)
                print('Error processing Sensor A_OUT')
            ax3.set_title('OPS processing SA - OUT', loc='left')
            ax3.set_xlabel('Time (s)')
            ax3.set_ylabel('Normalized amplitude')
            prairie.style(ax3)

            # SENSOR B OUT
            # ------------
            ax4 = self.fig.add_subplot(324, sharex = ax3)
            try:
                P = ops.process_position(self.y_OUT_A, parameter_file, self.t2[0], return_processing=True, INOUT='OUT')
                ax4.axhspan(0, P[8], color='black', alpha=0.05)
                ax4.plot( P[0], P[1], linewidth=0.5)
                ax4.plot( P[2], P[3], '.', markersize=2)
                ax4.plot( P[4], P[5], '.', markersize=2)
                ax4.plot( P[6], P[7], '-', linewidth=0.5, color=black)
                # Added by Jose --> Visually identify references detection
                refX = P[9]
                refY = P[1][np.where(P[0] > P[9])[0][0]]
                ax4.plot( refX, refY, '.', markersize=5, color = '#f93eed')
                # ----
            except:
                ax4.plot(1e3*self.t2, self.y_OUT_A, linewidth=0.5)
                print('Error processing Sensor B_OUT')
            ax4.set_title('OPS processing SB - OUT', loc='left')
            ax4.set_xlabel('Time (ms)')
            ax4.set_ylabel('Normalized amplitude')
            prairie.style(ax4)

            # PHOTODIODE IN
            # -------------
            ax5 = self.fig.add_subplot(325,sharex=ax1)
            ax5.plot(1e3 * self.t1, self.pd1, linewidth=1)
            ax5.set_title('Processing PH - IN', loc='left')
            ax5.set_xlabel('Time (ms)')
            ax5.set_ylabel('a.u.')
            try:
                occ_IN = ops.find_occlusions(self.pd1, IN=True, StartTime=self.t1[0], return_processing=True)
                ax5.plot(1e3 * occ_IN[2], occ_IN[3], linewidth=1)
                ax5.plot(1e3 * occ_IN[0], occ_IN[1], '.', markersize=3, color=black)
                ax5.legend(['PD data', 'Detected occlusions'])
            except:
                print('Error detecting Occlusions IN')
            prairie.style(ax5)

            # PHOTODIODE OUT
            # --------------
            ax6 = self.fig.add_subplot(326, sharex=ax3)
            ax6.plot(1e3 * self.t2, self.pd2, linewidth=1)
            ax6.set_title('Processing PH - OUT', loc='left')
            ax6.set_xlabel('Time (ms)')
            ax6.set_ylabel('a.u.')
            try:
                occ_OUT = ops.find_occlusions(self.pd2, IN=False, StartTime=self.t2[0], return_processing=True)
                ax6.plot(1e3 * occ_OUT[2], occ_OUT[3], linewidth=1)
                ax6.plot(1e3 * occ_OUT[0], occ_OUT[1], '.', markersize=3, color=black)
            except:
                print('Error detecting Occlusions OUT')
            prairie.style(ax6)

            self.fig.tight_layout()
