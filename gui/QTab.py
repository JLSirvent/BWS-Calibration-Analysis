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
        #self.fig.tight_layout()

        ax1.plot(self.x_IN_A, self.y_IN_A, color='#004466', linewidth=1)

        try:
            ax1.plot(self.x_IN_B, self.y_IN_B, color='#018BCF', linewidth=1)
        except:
            pass

        ax1.set_xlim([min(self.x_IN_A), max(self.x_IN_A)])
        ax1.legend(['Sensor A', 'Sensor B'])
        prairie.style(ax1)

        ax2 = self.fig.add_subplot(1, 2, 2)
        ax2.set_title(self.title, loc='left')
        ax2.set_xlabel(self.xlabel)
        ax2.set_ylabel(self.ylabel)
        ax2.plot(self.x_OUT_A, self.y_OUT_A, color='#6E160E', linewidth=1)

        try:
            ax2.plot(self.x_OUT_B, self.y_OUT_B, color='#CF2A1B', linewidth=1)
        except:
            pass

        ax2.set_xlim([min(self.x_OUT_A), max(self.x_OUT_A)])
        ax2.legend(['Sensor A', 'Sensor B'])
        prairie.style(ax2)

