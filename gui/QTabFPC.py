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
import matplotlib

from PyQt5 import QtCore
from PyQt5.QtWidgets import QStackedWidget, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

from gui.mplCanvas import mplCanvas


class QTabFPC(QWidget):

    def __init__(self, parent=None):

        super(QTabFPC, self).__init__(parent=None)

        self.main_widget = QStackedWidget(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        main_layout = QVBoxLayout(self.main_widget)
        self.plot = plot(self.main_widget, width=6.5, height=6, dpi=100)
        self.navi_toolbar = NavigationToolbar(self.plot, self)
        main_layout.addWidget(self.navi_toolbar)
        main_layout.addWidget(self.plot)

        self.timeAIN = [0, 1]
        self.timeBIN = [0, 1]
        self.timeAOUT = [0, 1]
        self.timeBOUT = [0, 1]
        self.posAIN = [0, 1]
        self.posBIN = [0, 1]
        self.posAOUT = [0, 1]
        self.posBOUT = [0, 1]
        self.occIN = [0, 1]
        self.occOUT = [0, 1]

        self.focus = 0
        self.setLayout(main_layout)

    def set_x_IN_A(self, timeAIN):
        self.timeAIN = timeAIN

    def set_x_OUT_A(self, timeAOUT):
        self.timeAOUT = timeAOUT

    def set_x_IN_B(self, timeBIN):
        self.timeBIN = timeBIN

    def set_x_OUT_B(self, timeBOUT):
        self.timeBOUT = timeBOUT

    def set_y_IN_A(self, posAIN):
        self.posAIN = posAIN

    def set_y_IN_B(self, posBIN):
        self.posBIN = posBIN

    def set_y_OUT_A(self, posAOUT):
        self.posAOUT = posAOUT

    def set_y_OUT_B(self, posBOUT):
         self.posBOUT = posBOUT

    def set_t1(self, occIN):
         self.occIN = occIN

    def set_t2(self, occOUT):
         self.occOUT = occOUT


    def actualise_ax(self):
        self.plot.fig.clear()

        self.plot.timeAIN = self.timeAIN
        self.plot.timeAOUT = self.timeAOUT
        self.plot.timeBIN = self.timeBIN
        self.plot.timeBOUT = self.timeBOUT

        self.plot.posAIN = self.posAIN
        self.plot.posBIN = self.posBIN
        self.plot.posAOUT = self.posAOUT
        self.plot.posBOUT = self.posBOUT

        self.plot.occIN = self.occIN
        self.plot.occOUT = self.occOUT

        self.plot.compute_initial_figure()
        self.plot.draw()

    def wait(self):
        pass


class plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):

        self.timeAIN = [0, 1]
        self.timeBIN = [0, 1]
        self.timeAOUT = [0, 1]
        self.timeBOUT = [0, 1]
        self.posAIN = [0, 1]
        self.posBIN = [0, 1]
        self.posAOUT = [0, 1]
        self.posBOUT = [0, 1]
        self.occIN = [0,1]
        self.occOUT = [0,1]

        self.ax1 = 0

        self.foc_marker = 0

        self.color = 0

        self.focus = 0

        super(plot, self).__init__(parent, width, height, dpi)

    def compute_initial_figure(self):
        try:

            self.fig.clear()

            ax1 = self.fig.add_subplot(221)
            ax2 = self.fig.add_subplot(222)
            ax3 = self.fig.add_subplot(223)
            ax4 = self.fig.add_subplot(224)

            for i in range(1, 3):
                if i == 1:
                    title = 'IN'
                    ax_time = ax1
                    ax_laser = ax2
                    timeA = self.timeAIN
                    timeB = self.timeBIN
                    PosA  = self.posAIN
                    PosB  = self.posBIN
                    Occ   = self.occIN
                    timems = 30
                else:
                    title = 'OUT'
                    ax_time = ax3
                    ax_laser = ax4
                    timeA = self.timeAOUT
                    timeB = self.timeBOUT
                    PosA  = self.posAOUT
                    PosB  = self.posBOUT
                    Occ   = self.occOUT
                    timems = 340

                pos_at_timeA = []
                pos_at_timeB = []

                for i in range(0, PosA.size):
                    #time_refA.append(timeA[i][np.where(PosA[i] > 0)[0][0]])
                    try:
                        pos_at_timeA.append(PosA[i][(np.where(timeA[i] > timems / 1000)[0][0])])
                    except:
                        print("Error RDS_A")

                for i in range(0, PosB.size):
                    #time_refB.append(timeB[i][np.where(PosB[i] > 0)[0][0]])
                    try:
                        pos_at_timeB.append(PosB[i][(np.where(timeB[i] > timems / 1000)[0][0])])
                    except:
                        print("Error RDS_B")

                #time_refA = np.asarray(time_refA) * 1e3
                #time_refB = np.asarray(time_refB) * 1e3

                ax_time.plot(1e3 * np.asarray(pos_at_timeA) , 'ob')
                ax_time.plot(1e3 * np.asarray(pos_at_timeB) , 'or')
                ax_time.set_title('Position at a given time ' + title + ' ' + str(timems) + 'ms', loc='left')
                ax_time.set_ylabel('Angular Position [mrad]')
                ax_time.set_xlabel('Scan Number')

                y_formatter = matplotlib.ticker.ScalarFormatter(useOffset=False)
                ax_laser.yaxis.set_major_formatter(y_formatter)

                ax_laser.plot(1e3 * Occ, 'ob')
                ax_laser.set_title('Angular position on Laser Crossing '+ title, loc='left')
                ax_laser.set_ylabel('Angular Position [mrad]')
                ax_laser.set_xlabel('Scan Number')

            self.fig.tight_layout()

        except:
            print("Error FPC!")