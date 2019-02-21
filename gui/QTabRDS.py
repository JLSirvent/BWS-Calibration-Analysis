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
import configparser

from PyQt5 import QtCore
from matplotlib import patches as mpatches
from PyQt5.QtWidgets import QStackedWidget, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

from lib import utils
from lib import prairie
from gui.mplCanvas import mplCanvas


class QTabRDS(QWidget):

    def __init__(self, parent=None):

        super(QTabRDS, self).__init__(parent=None)

        self.main_widget = QStackedWidget(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)


        main_layout = QVBoxLayout(self.main_widget)
        self.plot = plot(self.main_widget, width=6.5, height=6, dpi=100)
        self.navi_toolbar = NavigationToolbar(self.plot, self)
        main_layout.addWidget(self.navi_toolbar)
        main_layout.addWidget(self.plot)

        self.x_IN_A = np.ones((200, 200))
        self.x_OUT_A = np.ones((200, 200))
        self.y_IN_A = np.ones((200, 200))
        self.y_OUT_A = np.ones((200, 200))

        self.focus = 0
        self.setLayout(main_layout)

    def set_x_IN_A(self, x_IN_A):
        self.x_IN_A = x_IN_A

    def set_y_IN_A(self, y_IN_A):
        self.y_IN_A = y_IN_A

    def set_x_OUT_A(self, x_OUT_A):
        self.x_OUT_A = x_OUT_A

    def set_y_OUT_A(self, y_OUT_A):
        self.y_OUT_A = y_OUT_A

    def set_focus(self, index):
        self.focus = index

    def actualise_ax(self):
        self.plot.fig.clear()
        self.plot.x_IN_A = self.x_IN_A
        self.plot.x_OUT_A = self.x_OUT_A
        self.plot.y_IN_A = self.y_IN_A
        self.plot.y_OUT_A = self.y_OUT_A
        self.plot.focus = self.focus
        self.plot.compute_initial_figure()
        self.plot.draw()

    def wait(self):
        pass


class plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):

        self.x_IN_A = np.ones((200, 200))
        self.x_OUT_A = np.ones((200, 200))
        self.y_IN_A = np.ones((200, 200))
        self.y_OUT_A = np.ones((200, 200))

        self.ax1 = 0

        self.foc_marker = 0

        self.color = 0

        self.focus = 0

        super(plot, self).__init__(parent, width, height, dpi)

    def compute_initial_figure(self):
        try:
            parameter_file = utils.resource_path('data/parameters.cfg')
            config = configparser.RawConfigParser()
            config.read(parameter_file)
            rdcp = eval(config.get('OPS processing parameters', 'relative_distance_correction_prameters'))

            self.fig.clear()

            color_A = '#018BCF'
            color_B = self.color = '#CF2A1B'

            time_SA = self.x_IN_A
            time_SB = self.x_OUT_A

            offset=0

            ax1 = self.fig.add_subplot(2, 1, 1)
            ax1.axhspan(rdcp[1], rdcp[0], color='black', alpha=0.1)

            for i in np.arange(0, time_SA.shape[0]-1):
                distances_A = np.diff(time_SA[i])[offset:time_SA[i].size - 1 - offset]
                rel_distances_A = np.divide(distances_A[1::], distances_A[0:distances_A.size - 1])
                distances_B = np.diff(time_SB[i])[offset:time_SB[i].size - 1 - offset]
                rel_distances_B = np.divide(distances_B[1::], distances_B[0:distances_B.size - 1])

                xtimeA = 1e3 * time_SA[i][offset:time_SA[i].size - 2 - offset]
                xtimeB = 1e3 * time_SB[i][offset:time_SB[i].size - 2 - offset]

                ax1.plot(xtimeA,rel_distances_A, '.',
                         color=color_A)
                ax1.plot(xtimeB,rel_distances_B, '.',
                         color=color_B)

            ax1.set_xlabel('Time (ms)')
            ax1.set_ylabel('Relative distance')
            ax1.set_title('RDS plot - IN', loc='left')
            ax1.set_ylim(0,5)
            red_patch = mpatches.Patch(color=color_A, label='Sensor A')
            blue_patch = mpatches.Patch(color=color_B, label='Sensor B')
            ax1.legend(handles=[blue_patch, red_patch])
            prairie.style(ax1)

            time_SA = self.y_IN_A
            time_SB = self.y_OUT_A

            ax2 = self.fig.add_subplot(2, 1, 2)
            ax2.axhspan(rdcp[1], rdcp[0], color='black', alpha=0.1)

            for i in np.arange(0, time_SA.shape[0]-1):
                distances_A = np.diff(time_SA[i])[offset:time_SA[i].size - 1 - offset]
                rel_distances_A = np.divide(distances_A[1::], distances_A[0:distances_A.size - 1])
                distances_B = np.diff(time_SB[i])[offset:time_SB[i].size - 1 - offset]
                rel_distances_B = np.divide(distances_B[1::], distances_B[0:distances_B.size - 1])

                xtimeA = 1e3 * time_SA[i][offset:time_SA[i].size - 2 - offset]
                xtimeB = 1e3 * time_SB[i][offset:time_SB[i].size - 2 - offset]

                ax2.plot(xtimeA, rel_distances_A, '.', color=color_A)
                ax2.plot(xtimeB, rel_distances_B, '.', color=color_B)

                #ax2.plot(rel_distances_A, '.', color=color_A)
                #ax2.plot(rel_distances_B, '.', color=color_B)

            ax2.set_xlabel('Time (ms)')
            ax2.set_ylabel('Relative distance')
            ax2.set_title('RDS plot - OUT', loc='left')
            ax2.set_ylim(0,5)
            red_patch = mpatches.Patch(color=color_A, label='Sensor A')
            blue_patch = mpatches.Patch(color=color_B, label='Sensor B')
            ax2.legend(handles=[blue_patch, red_patch])
            prairie.style(ax2)

            self.fig.tight_layout()

        except:
            print("Error RDS!")