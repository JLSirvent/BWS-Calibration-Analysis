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

        self.CalibCoeff = []

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
        self.CalibCoeff = self.plot.compute_initial_figure()
        self.plot.draw()
        #self.plot.fig.savefig('Stuff.png')

    def wait(self):
        pass


class plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):

        self.x_IN_A = np.ones(200)
        self.x_OUT_A = np.ones(200)
        self.y_IN_A = np.ones(200)
        self.y_OUT_A = np.ones(200)

        self.in_or_out = 'IN'

        self.foc_marker = [0,0]

        self.ax1 = 0

        self.color = 0

        self.focus = 0

        self.idx = 0

        super(plot, self).__init__(parent, width, height, dpi)

    def compute_initial_figure(self):
        self.fig.clear()
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax1.set_title('BWS Angular to Projected Motion', loc='left')
        self.ax1.set_xlabel('Angular position [rad]')
        self.ax1.set_ylabel('Laser position [mm]')

        ax2 = self.fig.add_subplot(2, 2, 4)
        ax2.set_title('Wire position error histogram', loc='left')
        ax2.set_xlabel('Wire position error [\u03BCm]')
        ax2.set_ylabel('Occurrence')

        ax3 = self.fig.add_subplot(2, 2, 3)
        ax3.set_title('Wire position error', loc='left')
        ax3.set_ylabel('Wire position error [\u03BCm]')
        ax3.set_xlabel('Laser position [mm]')

        self.fig.tight_layout()
        Parameters = []
        try:
            if len(self.y_IN_A)!= 200:
                for i in range(0,2):

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

                    parameter_file = 'data/parameters.cfg'
                    config = configparser.RawConfigParser()
                    config.read(parameter_file)
                    positions_for_fit = eval(config.get('OPS processing parameters', 'positions_for_fit'))

                    # Trimm Vectors for only region of interest
                    Idx = np.where((laser_position>=positions_for_fit[0]) & (laser_position<=positions_for_fit[1]))
                    laser_position = laser_position[Idx]
                    occlusion_position = occlusion_position[Idx]

                    self.idxs = np.argsort(laser_position)
                    occlusion_position = occlusion_position[self.idxs]
                    laser_position = laser_position[self.idxs]
                    self.focus = np.where(self.idxs == self.focus)[0]

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

                    occlusion_position_mean = np.asarray(occlusion_position_mean)

                    popt, pcov = curve_fit(utils.theoretical_laser_position, occlusion_position_mean,
                                           unique_laser_position, bounds=([-5, 80, 100], [5, 500, 500]))

                    theorical_laser_position_mean = utils.theoretical_laser_position(occlusion_position_mean, popt[0], popt[1],
                                                                                     popt[2])
                    theoretical_laser_position = utils.theoretical_laser_position(occlusion_position, popt[0], popt[1], popt[2])
                    param = popt

                    xfit = np.arange(np.min(occlusion_position),np.max(occlusion_position),(np.max(occlusion_position)-np.min(occlusion_position))/1000)
                    fit_poly = np.polyfit(occlusion_position, laser_position, 5)
                    fit_func = np.poly1d(fit_poly)
                    yfit = fit_func(xfit)

                    print(self.in_or_out)
                    print(fit_poly)

                    param2=fit_poly[:]

                    #residuals = laser_position - theoretical_laser_position
                    residuals = laser_position - fit_func(occlusion_position)

                    plt.figure(figsize=(6.5, 7.5))
                    prairie.use()

                    residuals = 1e3 * residuals

                    ResidMean = np.mean(residuals)
                    ResidSTD = np.std(residuals)

                    Lim_minus = ResidMean - 10*ResidSTD
                    Lim_plus = ResidMean + 10*ResidSTD

                    dt.make_histogram(residuals, [Lim_minus, Lim_plus], '\u03BCm', axe=ax2, color=self.color)
                    prairie.style(ax2)

                    residuals_smooth = savgol_filter(np.asarray(residuals),9, 2)
                    ax3.plot(laser_position, residuals, '.', color=self.color, markersize=6, alpha = 0.6)
                    ax3.plot(laser_position, residuals_smooth, color=self.color)
                    #ax3.set_ylim([-50, 50])
                    prairie.style(ax3)

                    equation = "{:3.2f}".format(param[1]) + '-' + "{:3.2f}".format(
                        param[2]) + '*' + 'cos(\u03C0-(x + ' + "{:3.2f}".format(
                        param[0]) + '))'
                    LegendText = 'Fit ' + self.in_or_out + ': ' + equation

                    print('\n'+ self.in_or_out + ' SCANS')
                    print('*************')
                    print('Calculated Rotation_Offset: ' + "{:3.5f}".format(param[1]))
                    print('Calculated Fork_Length: ' + "{:3.5f}".format(param[2]))
                    print('Calculated Fork_Phase: ' + "{:3.5f}".format(param[0]))

                    Parameters.append(param2)
                    self.ax1.plot(occlusion_position_mean, theorical_laser_position_mean, linewidth=0.5, color=self.color, label = LegendText)
                    self.ax1.plot(occlusion_position, laser_position, '.', color=self.color, markersize=6, alpha = 0.6)
                    self.foc_marker[i], = self.ax1.plot(occlusion_position[self.focus], laser_position[self.focus], 'o', color= self.color, fillstyle='none', markersize=10)

                    prairie.style(self.ax1)

                self.ax1.legend(loc='upper right')
                ax2.legend(loc='upper right')
        except:
            print('Error Calibration!')

        return Parameters

    def refocus(self, index):
        self.foc_marker[0].remove()
        self.foc_marker[1].remove()

        self.focus = np.where(self.idxs == index)[0]
        self.foc_marker[0],=self.ax1.plot(self.x_IN_A[self.focus], self.y_IN_A[self.focus], 'o',
                      color='blue', fillstyle='none', markersize=10)
        self.foc_marker[1],=self.ax1.plot(self.x_OUT_A[self.focus], self.y_OUT_A[self.focus], 'o',
                      color='red', fillstyle='none', markersize=10)
        self.draw()

