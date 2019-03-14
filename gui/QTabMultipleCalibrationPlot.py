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

import os
import numpy as np
import configparser
import scipy.io as sio
from scipy.optimize import curve_fit

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

from matplotlib import cm as cmx
from matplotlib import pyplot as plt
from matplotlib import colors as colors

from lib import prairie, utils
from gui import Calibration

from gui.mplCanvas import mplCanvas
from lib import diagnostic_tools as dt


class QTabMultipleCalibrationPlot(QWidget):

    def __init__(self, parent=None):

        super(QTabMultipleCalibrationPlot, self).__init__(parent=None)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.main_widget = QWidget(self)

        self.in_or_out = 'IN'
        self.folders = []

        main_layout = QVBoxLayout(self.main_widget)
        self.plot = plot(self.main_widget, width=6.5, height=6, dpi=100)
        self.navi_toolbar = NavigationToolbar(self.plot, self)
        main_layout.addWidget(self.navi_toolbar)
        main_layout.addWidget(self.plot)

        self.setLayout(main_layout)

    def set_folder(self, folders,fittype0, fittype1, fittype2):
        self.folders = folders
        self.plot.folders = folders
        self.plot.fittype = fittype0
        self.plot.fitorder = fittype1
        self.plot.globalresiduals = fittype2
        self.plot.compute_initial_figure()
        self.plot.draw()


class plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):

        self.folders = []
        self.calibration = 0
        self.fittype = 0
        self.fitorder = 0
        self.globalresiduals = 0
        super(plot, self).__init__(parent, width, height, dpi)

    def compute_initial_figure(self):

        self.fig.clear()

        ax2 = self.fig.add_subplot(2, 2, 3)
        ax2.set_title('Wire position error', loc='left')
        ax2.set_ylabel('Wire position error [\u03BCm]')
        ax2.set_xlabel('Laser position [mm]')

        ax3 = self.fig.add_subplot(2, 2, 4)
        ax3.set_title('Wire position error histogram', loc='left')
        ax3.set_ylabel('Occurrence')
        ax3.set_xlabel('Wire position error [\u03BCm]')

        ax1 = self.fig.add_subplot(2, 1, 1)
        ax1.set_title('BWS Angular to Projected Motion', loc='left')
        ax1.set_ylabel('Laser position [mm]')
        ax1.set_xlabel('Angular Position [rad]')

        #self.fig.tight_layout()

        values = range(len(self.folders) + 1)
        jet = cm = plt.get_cmap('jet')
        cNorm = colors.Normalize(vmin=0, vmax=values[-1])
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

        cnt = 0
        x_all = []
        y_all = []
        x_all1 = []
        y_all1 = []

        #parameter_file = utils.resource_path('data/parameters.cfg')
        config = configparser.RawConfigParser()
        config.read('data/parameters.cfg')
        positions_for_fit = eval(config.get('OPS processing parameters', 'positions_for_fit'))

        for folder in self.folders:
            colorVal = scalarMap.to_rgba(values[cnt])
            self.calibration = Calibration.Calibration(folder)

            #Idx = np.where(sio.loadmat(folder+'/PROCESSED_IN.mat')['data_valid'] == 1)
            Idx = np.where(self.calibration.data_valid == 1)

            tmp = folder.split(' ')[0]
            tmp = tmp.split('/')[-1]
            for i in range(0,2):

                if i == 0:
                    x = self.calibration.occlusion_IN[Idx]#sio.loadmat(folder+'/PROCESSED_IN.mat')['occlusion_position'][Idx]
                    y = self.calibration.laser_position_IN[Idx]#sio.loadmat(folder+'/PROCESSED_IN.mat')['laser_position'][Idx]
                    Label = tmp +' IN'
                if i == 1:
                    x = self.calibration.occlusion_OUT[Idx]#sio.loadmat(folder+'/PROCESSED_OUT.mat')['occlusion_position'][Idx]
                    y =  self.calibration.laser_position_OUT[Idx]#sio.loadmat(folder+'/PROCESSED_OUT.mat')['laser_position'][Idx]
                    Label = tmp+' OUT'

                # Trim vectors for region of interest
                Idx2 = np.where((y>=positions_for_fit[0])&(y<=positions_for_fit[1]))
                x = x[Idx2]
                y = y[Idx2]

                if self.globalresiduals == 1:
                    x_all=np.concatenate((x_all,x),axis=0)
                    y_all=np.concatenate((y_all,y),axis=0)
                    x_all1.append(x)
                    y_all1.append(y)

                FitOrder = 5
                fit_poly = np.polyfit(x,y,FitOrder)
                fit_func = np.poly1d(fit_poly)

                minx = np.min(x)
                maxx = np.max(x)
                step = (maxx - minx) / 100
                xfit = np.arange(minx, maxx, step)

                if self.fittype ==0:
                    fit_poly = np.polyfit(x, y, self.fitorder)
                    fit_func = np.poly1d(fit_poly)
                    yfit = fit_func(xfit)
                else:
                    popt, pcov = curve_fit(utils.theoretical_laser_position, x, y, bounds=([-5, 80, 100], [5, 500, 500]))
                    yfit = utils.theoretical_laser_position(xfit, popt[0], popt[1], popt[2])

                ax1.plot(x,y,'.', label=Label, color = colorVal, markersize=6, alpha = 0.6)
                ax1.plot(xfit,yfit, color = colorVal)

                if self.globalresiduals == 0:

                    if self.fittype == 0:
                        Residuals = 1e3 * (y - fit_func(x))
                    else:
                        Residuals = 1e3*(y - utils.theoretical_laser_position(x, popt[0], popt[1], popt[2]))

                    ax2.plot(y,Residuals,'.', color = colorVal,markersize=6, alpha = 0.6)

                    ResidMean = np.mean(Residuals)
                    ResidSTD = np.std(Residuals)

                    Lim_minus = ResidMean - 10 * ResidSTD
                    Lim_plus = ResidMean + 10 * ResidSTD

                    dt.make_histogram(Residuals, [Lim_minus, Lim_plus], '\u03BCm', axe=ax3, color=colorVal)
            cnt = cnt + 1


        if self.globalresiduals == 1:
            popt, pcov = curve_fit(utils.theoretical_laser_position, x_all[3:], y_all[3:], bounds=([-5, 80, 100], [5, 500, 500]))

            fit_poly = np.polyfit( x_all[3:], y_all[3:], FitOrder)
            fit_func = np.poly1d(fit_poly)

            cnt = 0
            for i in np.arange(0,len(x_all1)):
                colorVal = scalarMap.to_rgba(values[cnt])

                if self.fittype==0:
                    Residuals = 1e3 * (y_all1[i] - fit_func(x_all1[i]))
                else:
                    Residuals = 1e3 * (y_all1[i] - utils.theoretical_laser_position(x_all1[i], popt[0], popt[1], popt[2]))


                ax2.plot(y_all1[i],Residuals,'.', color = colorVal)

                ResidMean = np.mean(Residuals)
                ResidSTD = np.std(Residuals)

                Lim_minus = ResidMean - 10*ResidSTD
                Lim_plus = ResidMean + 10*ResidSTD

                dt.make_histogram(Residuals, [Lim_minus, Lim_plus], '\u03BCm', axe=ax3, color=colorVal)

                if i % 2 != 0: # Only increase color counter after OUT scan
                    cnt = cnt + 1

        ax1.legend()
        ax3.legend()

