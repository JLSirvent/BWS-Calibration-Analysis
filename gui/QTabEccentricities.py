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


class QTabEccentricities(QWidget):

    def __init__(self, parent=None):

        super(QTabEccentricities, self).__init__(parent=None)

        self.main_widget = QStackedWidget(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        main_layout = QVBoxLayout(self.main_widget)
        self.plot = plot(self.main_widget, width=6.5, height=6, dpi=100)
        self.navi_toolbar = NavigationToolbar(self.plot, self)
        main_layout.addWidget(self.navi_toolbar)
        main_layout.addWidget(self.plot)

        self.positions_in = [0, 1]
        self.eccentricities_in = [0, 1]
        self.positions_out = [0, 1]
        self.eccentricities_out = [0, 1]
        self.bound_in = [0, 1]
        self.bound_out = [0, 1]

        self.focus = 0
        self.setLayout(main_layout)

    def set_x_IN(self, x_IN):
        self.positions_in = x_IN

    def set_y_IN(self, y_IN):
        self.eccentricities_in = y_IN

    def set_x_OUT(self, x_OUT):
        self.positions_out = x_OUT

    def set_y_OUT(self, y_OUT):
        self.eccentricities_out = y_OUT

    def set_B_OUT(self, B_OUT):
        self.bound_out = B_OUT

    def set_B_IN(self, B_IN):
        self.bound_in = B_IN

    def actualise_ax(self):
        self.plot.fig.clear()
        self.plot.positions_in = self.positions_in
        self.plot.eccentricities_in = self.eccentricities_in
        self.plot.positions_out = self.positions_out
        self.plot.eccentricities_out = self.eccentricities_out
        self.plot.bound_in = self.bound_in
        self.plot.bound_out = self.bound_out
        self.plot.compute_initial_figure()
        self.plot.draw()

    def wait(self):
        pass


class plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):

        self.positions_in = [0,1]
        self.eccentricities_in = [0,1]
        self.positions_out = [0,1]
        self.eccentricities_out = [0,1]
        self.bound_in = [0, 1]
        self.bound_out = [0, 1]

        self.ax1 = 0

        self.foc_marker = 0

        self.color = 0

        self.focus = 0

        super(plot, self).__init__(parent, width, height, dpi)

    def compute_initial_figure(self):
        self.fig.clear()

        ax1 = self.fig.add_subplot(221)
        ax1.set_title('Eccentricity Error IN', loc='left')
        ax1.set_xlabel('Angular position [rad]')
        ax1.set_ylabel('Position error [mrad]')

        ax2 = self.fig.add_subplot(222, sharex=ax1)
        ax2.set_title('Error after compensation IN', loc='left')
        ax2.set_xlabel('Angular position [rad]')
        ax2.set_ylabel('Position error [mrad]')

        ax3 = self.fig.add_subplot(223, sharex=ax1, sharey=ax1)
        ax3.set_title('Eccentricity Error OUT', loc='left')
        ax3.set_xlabel('Angular position [rad]')
        ax3.set_ylabel('Position error [\u03BCrad]')

        ax4 = self.fig.add_subplot(224, sharex=ax1, sharey=ax2)
        ax4.set_title('Error after compensation OUT', loc='left')
        ax4.set_xlabel('Angular position [rad]')
        ax4.set_ylabel('Position error [\u03BCrad]')
        self.fig.tight_layout()

        try:

            for i in range(1, 3):
                if i == 1:
                    ax_all = ax1
                    ax_res = ax2
                    bound = self.bound_in
                    eccentricity = self.eccentricities_in
                    angular_position_SA = self.positions_in
                else:
                    ax_all = ax3
                    ax_res = ax4
                    bound = self.bound_out
                    eccentricity = -self.eccentricities_out
                    angular_position_SA = self.positions_out

                off = 50
                values = range(len(eccentricity) + 1)
                jet = cm = plt.get_cmap('jet')
                cNorm = colors.Normalize(vmin=0, vmax=values[-1])
                scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

                ref_ecc = eccentricity[0]
                ref_ecc = ref_ecc[off:ref_ecc.size - off]
                ref_pos = angular_position_SA[0]
                ref_pos = ref_pos[off:ref_pos.size - off]
                ecc_all = []

                def theor_ecc(x, a, b, c):
                    return a * np.sin(x + b) + c

                try:
                    popt, pcov = curve_fit(theor_ecc, ref_pos, ref_ecc, bounds=([-100, -100, -100], [100, 100, 100]))
                except:
                    popt = [0, 0, 0, 0]
                    pcov = [0, 0, 0, 0]

                for ecc, pos in zip(eccentricity, angular_position_SA):
                    ecc = ecc[off:ecc.size - off]
                    pos = pos[off:pos.size - off]
                    ecc = utils.resample(np.array([pos, ecc]), np.array([ref_pos, ref_ecc]))
                    ecc_all.append(ecc[1])

                [ref_ecc, ref_pos] = [eccentricity[0], angular_position_SA[0]]

                deff = []
                residuals_mean = []

                ax_all.plot(ref_pos, 1e3 * theor_ecc(ref_pos, popt[0], popt[1], popt[2]), linewidth=0.5, color='black')
                ax_all.axvspan(bound[0], bound[1], color='red', alpha=0.1)

                cnt = 1
                for ecc, pos in zip(eccentricity, angular_position_SA):
                    colorVal = scalarMap.to_rgba(values[cnt])
                    ecc = ecc[off:ecc.size - off]
                    pos = pos[off:pos.size - off]
                    ax_all.plot(pos, 1e3 * ecc, linewidth=0.8, color=colorVal)
                    cnt = cnt + 1
                #

                # #ax_all.legend(['Eccentricity global fit', 'Eccentricity profiles (' + str(eccentricity.size) + ')'])
                prairie.style(ax_all)
                #

                cnt = 1
                for ecc, pos in zip(eccentricity, angular_position_SA):
                    colorVal = scalarMap.to_rgba(values[cnt])
                    ecc = ecc[off:ecc.size - off]
                    pos = pos[off:pos.size - off]
                    residuals = ecc - theor_ecc(pos, popt[0], popt[1], popt[2])
                    ax_res.plot(pos, 1e6 * residuals, linewidth=0.2, color=colorVal)
                    residuals_mean.append(np.mean(residuals))
                    cnt = cnt + 1

                ax_res.axvspan(bound[0], bound[1], color='red', alpha=0.1)

                #ax_res.legend(['Residuals profiles (' + str(eccentricity.size) + ')'])
                prairie.style(ax_res)

            #plt.tight_layout()

        except:
            print("Error Eccentricities!")