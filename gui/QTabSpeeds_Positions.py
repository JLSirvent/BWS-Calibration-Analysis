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
from scipy.optimize import curve_fit
from PyQt5.QtWidgets import QStackedWidget, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib import cm as cmx
from matplotlib import pyplot as plt
from matplotlib import colors as colors

from lib import utils
from lib import prairie
from gui.mplCanvas import mplCanvas
from lib import diagnostic_tools as dt

class QTabSpeeds_Positions(QWidget):

    def __init__(self, title, xlabel, ylabel, N, parent=None):

        super(QTabSpeeds_Positions, self).__init__(parent=None)

        self.main_widget = QStackedWidget(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        main_layout = QVBoxLayout(self.main_widget)
        self.plot = plot(self.main_widget, width=6.5, height=6, dpi=100)
        self.navi_toolbar = NavigationToolbar(self.plot, self)
        main_layout.addWidget(self.navi_toolbar)
        main_layout.addWidget(self.plot)

        self.times_in = [0, 1]
        self.speeds_in = [0, 1]
        self.times_out = [0, 1]
        self.speeds_out = [0, 1]
        self.bound_in = [0, 1]
        self.bound_out = [0, 1]

        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.N = N

        self.plot.title = self.title
        self.plot.xlabel = self.xlabel
        self.plot.ylabel = self.ylabel
        self.plot.N = self.N

        self.focus = 0
        self.setLayout(main_layout)

    def set_x_IN(self, x_IN):
        self.times_in = x_IN

    def set_y_IN(self, y_IN):
        self.speeds_in = y_IN

    def set_B_IN(self, B_IN):
        self.bound_in = B_IN

    def set_x_OUT(self, x_OUT):
        self.times_out = x_OUT

    def set_y_OUT(self, y_OUT):
        self.speeds_out = y_OUT

    def set_B_OUT(self, B_OUT):
         self.bound_out = B_OUT

    def actualise_ax(self):
        self.plot.fig.clear()
        self.plot.times_in = self.times_in
        self.plot.speeds_in = self.speeds_in
        self.plot.times_out = self.times_out
        self.plot.speeds_out = self.speeds_out
        self.plot.bound_in = self.bound_in
        self.plot.bound_out = self.bound_out
        self.plot.title = self.title
        self.plot.xlabel = self.xlabel
        self.plot.ylabel = self.ylabel
        self.plot.N = self.N
        self.plot.compute_initial_figure()
        self.plot.draw()

    def wait(self):
        pass


class plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):

        self.times_in = [0, 1]
        self.speeds_in = [0, 1]
        self.times_out = [0, 1]
        self.speeds_out = [0, 1]
        self.bound_in = [0, 1]
        self.bound_out = [0, 1]

        self.title = ''
        self.xlabel = ''
        self.ylabel = ''
        self.N = 1

        self.ax1 = 0

        self.foc_marker = 0

        self.color = 0

        self.focus = 0

        super(plot, self).__init__(parent, width, height, dpi)

    def compute_initial_figure(self):
        self.fig.clear()
        ax1 = self.fig.add_subplot(121)
        ax1.set_ylabel(self.ylabel)
        ax1.set_xlabel(self.xlabel)
        ax1.set_title(self.title + 'IN - Sensor A', loc='left')

        ax2 = self.fig.add_subplot(122)
        ax2.set_ylabel(self.ylabel)
        ax2.set_xlabel(self.xlabel)
        ax2.set_title(self.title + 'OUT - Sensor A', loc='left')

        self.fig.tight_layout()

        try:

            for i in range(1, 3):
                if i == 1:
                    title = 'IN'
                    ax_all = ax1
                    boundy = self.bound_in
                    times = self.times_in
                    speeds = self.speeds_in
                else:
                    title = 'OUT'
                    ax_all = ax2
                    boundy = self.bound_out
                    times = self.times_out
                    speeds = self.speeds_out

                ax_all.axvspan(boundy[0], boundy[1], color='red', alpha=0.1)

                off = 0
                values = range(len(speeds) + 1)
                jet = cm = plt.get_cmap('jet')
                cNorm = colors.Normalize(vmin=0, vmax=values[-1])
                scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

                cnt = 1

                for tim, spe in zip(times, speeds):
                    colorVal = scalarMap.to_rgba(values[cnt])
                    spe = np.convolve(spe, np.ones((self.N,)) / self.N, mode='valid')
                    tim = tim[off:spe.size - off]
                    spe = spe[off:spe.size - off]
                    ax_all.plot(tim, spe, linewidth=0.8, color=colorVal)
                    cnt = cnt + 1


                prairie.style(ax_all)


        except:
            print("Error Speeds_Positions!")