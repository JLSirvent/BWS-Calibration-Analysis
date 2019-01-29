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
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
from matplotlib import pyplot as plt
from PyQt5.QtWidgets import QStackedWidget, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

from lib import utils
from lib import prairie
from lib import diagnostic_tools as dt
from gui.mplCanvas import mplCanvas

PLOT_WIDTH = 7
PLOT_HEIGHT = 6.5


class QTabCalibration(QWidget):

    def __init__(self, in_or_out, parent=None):

        super(QTabCalibration, self).__init__(parent=None)

        self.main_widget = QStackedWidget(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.in_or_out = in_or_out

        main_layout = QVBoxLayout(self.main_widget)
        self.plot = plot(self.main_widget, width=PLOT_WIDTH, height=PLOT_HEIGHT, dpi=100)
        self.navi_toolbar = NavigationToolbar(self.plot, self)
        main_layout.addWidget(self.navi_toolbar)
        main_layout.addWidget(self.plot)

        self.x_IN_A = np.ones(200)
        self.x_OUT_A = np.ones(200)
        self.y_IN_A = np.ones(200)
        self.y_OUT_A = np.ones(200)

        self.focus = 0
        self.setLayout(main_layout)

    def set_x_IN_A(self, x1):
        self.x_IN_A = x1

    def set_y_IN_A(self, y1):
        self.y_IN_A = y1

    def set_x_OUT_A(self, x2):
        self.x_OUT_A = x2

    def set_y_OUT_A(self, y2):
        self.y_OUT_A = y2

    def set_focus(self, index):
        self.focus = index
        self.plot.refocus(index)

    def actualise_ax(self):
        self.plot.fig.clear()
        self.plot.x_IN_A = self.x_IN_A
        self.plot.x_OUT_A = self.x_OUT_A
        self.plot.y_IN_A = self.y_IN_A
        self.plot.y_OUT_A = self.y_OUT_A
        self.plot.in_or_out = self.in_or_out
        self.plot.focus = self.focus
        self.plot.compute_initial_figure()
        self.plot.draw()

    def wait(self):
        pass


class plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):

        self.x_IN_A = np.ones(200)
        self.x_OUT_A = np.ones(200)
        self.y_IN_A = np.ones(200)
        self.y_OUT_A = np.ones(200)

        self.ax1 = 0

        self.in_or_out = 'IN'

        self.foc_marker = [0,0]

        self.color = 0

        self.focus = 0

        self.idx = 0

        super(plot, self).__init__(parent, width, height, dpi)

    def compute_initial_figure(self):
        try:
            self.fig.clear()
            for i in range(0,2):
                print(i)
                if i == 0:
                    laser_position = self.y_IN_A
                    occlusion_position = self.x_IN_A
                    self.in_or_out = 'IN'
                else:
                    laser_position = self.y_OUT_A
                    occlusion_position = self.x_OUT_A
                    self.in_or_out = 'OUT'

                if self.in_or_out is 'IN':
                    self.color = 'blue'#'#018BCF'
                elif self.in_or_out is 'OUT':
                    self.color = 'red'#'#CF2A1B'

                parameter_file = utils.resource_path('data/parameters.cfg')
                config = configparser.RawConfigParser()
                config.read(parameter_file)
                positions_for_fit = eval(config.get('OPS processing parameters', 'positions_for_fit'))
                positions_for_analysis = eval(config.get('OPS processing parameters', 'positions_for_analysis'))
                tank_center = eval(config.get('Geometry', 'stages_position_at_tank_center'))

                self.idxs = np.argsort(laser_position)
                occlusion_position = occlusion_position[self.idxs]
                laser_position = laser_position[self.idxs]
                self.focus = np.where(self.idxs == self.focus)[0]

                laser_position = -laser_position + tank_center

                # DeleteCorrection
                # CorrectIndex = np.where((laser_position <= 1.5) & (laser_position >= -36.5))
                # laser_position[CorrectIndex] = laser_position[CorrectIndex] - 1
                # ----------------
                if i == 0:
                    self.y_IN_A = laser_position
                    self.x_IN_A = occlusion_position
                else:
                    self.y_OUT_A = laser_position
                    self.x_OUT_A = occlusion_position

                unique_laser_position = np.unique(laser_position)
                occlusion_position_mean = []

                for laser_pos in unique_laser_position:
                    occlusion_position_mean.append(np.mean(occlusion_position[np.where(laser_position == laser_pos)[0]]))

                off1 = [int(positions_for_fit[0] / 100 * unique_laser_position.size),
                        int(positions_for_fit[1] / 100 * unique_laser_position.size)]

                occlusion_position_mean = np.asarray(occlusion_position_mean)
                popt, pcov = curve_fit(utils.theoretical_laser_position, occlusion_position_mean[off1[0]:off1[1]],
                                       unique_laser_position[off1[0]:off1[1]], bounds=([-5, 80, 100], [5, 500, 500]))

                theorical_laser_position_mean = utils.theoretical_laser_position(occlusion_position_mean, popt[0], popt[1],
                                                                                 popt[2])
                theoretical_laser_position = utils.theoretical_laser_position(occlusion_position, popt[0], popt[1], popt[2])
                param = popt

                off2 = [int(positions_for_analysis[0] / 100 * laser_position.size),
                        int(positions_for_analysis[1] / 100 * laser_position.size)]

                laser_position = laser_position[off2[0]:off2[1]]
                theoretical_laser_position = theoretical_laser_position[off2[0]:off2[1]]
                occlusion_position = occlusion_position[off2[0]:off2[1]]
                residuals = laser_position - theoretical_laser_position

                plt.figure(figsize=(6.5, 7.5))
                prairie.use()
                ax2 = self.fig.add_subplot(2, 2, 4)
                residuals = residuals[off2[0]:off2[1]]
                dt.make_histogram(1e3 * residuals, [-300, 300], '\u03BCm', axe=ax2, color=self.color)
                ax2.set_title('Wire position error histogram', loc='left')
                ax2.set_xlabel('Wire position error (\u03BCm)')
                ax2.set_ylabel('Occurrence')
                prairie.style(ax2)

                ax3 = self.fig.add_subplot(2, 2, 3)
                residuals_smooth = savgol_filter(np.asarray(residuals),9, 2)
                ax3.plot(laser_position, 1e3 * residuals, '.', color=self.color, markersize=6, alpha = 0.6)
                print(residuals_smooth.size)
                print(laser_position.size)
                ax3.plot(laser_position, 1e3 * residuals_smooth, color=self.color)
                ax3.set_ylim([-300, 300])
                ax3.set_title('Wire position error', loc='left')
                ax3.set_ylabel('Wire position error (\u03BCm)')
                ax3.set_xlabel('Laser position (mm)')
                prairie.style(ax3)

                equation = "{:3.2f}".format(param[1]) + '-' + "{:3.2f}".format(
                    param[2]) + '*' + 'cos(\u03C0-(x + ' + "{:3.2f}".format(
                    param[0]) + '))'
                LegendText = 'Fit ' + self.in_or_out + ': ' + equation

                print('Calculated Rotation_Offset: ' + "{:3.5f}".format(param[1]))
                print('Calculated Fork_Length: ' + "{:3.5f}".format(param[2]))
                print('Calculated Fork_Phase: ' + "{:3.5f}".format(param[0]))

                self.ax1 = self.fig.add_subplot(2, 1, 1)
                self.ax1.plot(occlusion_position_mean, theorical_laser_position_mean, linewidth=0.5, color=self.color, label = LegendText)
                self.ax1.plot(occlusion_position, laser_position, '.', color=self.color, markersize=6, alpha = 0.6)
                self.foc_marker[i], = self.ax1.plot(occlusion_position[self.focus], laser_position[self.focus], 'o', color= self.color, fillstyle='none', markersize=10)
                self.ax1.set_title('BWS Angular to Projected Motion', loc='left')

                self.ax1.set_xlabel('Angular position at laser crossing (rad)')
                self.ax1.set_ylabel('Laser position (mm)')
                prairie.style(self.ax1)
                self.fig.tight_layout()
            self.ax1.legend()
        except:
            print('Error Calibration!')


    def refocus(self, index):

        #self.ax1.lines.pop(2)
        #self.ax1.lines.pop(4)
        self.foc_marker[0].remove()
        self.foc_marker[1].remove()

        self.focus = np.where(self.idxs == index)[0]
        self.foc_marker[0],=self.ax1.plot(self.x_IN_A[self.focus], self.y_IN_A[self.focus], 'o',
                      color='blue', fillstyle='none', markersize=10)
        self.foc_marker[1],=self.ax1.plot(self.x_OUT_A[self.focus], self.y_OUT_A[self.focus], 'o',
                      color='red', fillstyle='none', markersize=10)
        self.draw()

