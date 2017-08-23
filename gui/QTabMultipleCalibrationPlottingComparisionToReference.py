from __future__ import unicode_literals

import os
import numpy as np
import scipy.io as sio

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

from lib import prairie
from lib import diagnostic_tools as dt
from gui.mplCanvas import mplCanvas


class QTabMultipleCalibrationPlottingComparisionToReference(QWidget):

    def __init__(self, parent=None):

        super(QTabMultipleCalibrationPlottingComparisionToReference, self).__init__(parent=None)

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

    def set_folder(self, folders, in_or_out):
        self.folders = folders
        self.in_or_out = in_or_out
        self.plot.folders = folders
        self.plot.in_or_out = in_or_out
        self.plot.compute_initial_figure()
        self.plot.draw()


class plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):

        self.folders = []

        self.ax1 = 0

        self.in_or_out = 'IN'

        super(plot, self).__init__(parent, width, height, dpi)

    def compute_initial_figure(self):

        self.fig.clear()

        day_max = 31

        legends = []

        ax1 = self.fig.add_subplot(2, 1, 1)
        ax2 = self.fig.add_subplot(2, 1, 2)
        labels = []
        dates = []
        colors = []
        mu = []
        sigma = []
        ranges_0 = []
        ranges_1 = []

        for folder in self.folders:

            if os.path.exists(folder + '/calibration_results.mat'):

                date = float(folder.split('/')[::-1][0].split('__')[1].split('_')[2])
                plot_legend = folder.split('/')[::-1][0].split('__')[1].split('_')[1] + '/' + \
                              folder.split('/')[::-1][0].split('__')[1].split('_')[2]

                color = int(folder.split('/')[::-1][0].split('__')[1].split('_')[2])

                if int(folder.split('/')[::-1][0].split('__')[2].split('_')[0]) <= 12:
                    plot_legend += ' a.m.'
                else:
                    plot_legend += ' p.m.'
                    date += 0.5
                    color += 0.5

                labels.append(plot_legend)
                data = sio.loadmat(folder + '/calibration_results.mat', struct_as_record=False, squeeze_me=True)
                dates.append(2 * date)
                acolor = np.zeros(3)
                acolor[1] = (day_max - color) / day_max
                acolor[2] = 0.75
                acolor[0] = 0.2
                colors.append(acolor)

                if self.in_or_out is 'IN':

                    residuals = np.asarray(data['residuals_IN_origin'])
                    range_0 = 1e3*(np.mean(residuals) - 4 * np.std(residuals))
                    ranges_0.append(range_0)
                    range_1 = 1e3*(np.mean(residuals) + 4 * np.std(residuals))
                    ranges_1.append(range_1)

                    ax1.plot(data['laser_position_IN'], 1e3 * data['residuals_IN_origin'], '.', color=acolor)
                    m = dt.make_histogram(1e3 * data['residuals_IN_origin'], [range_0, range_1], 'um', axe=ax2, color=acolor)

                elif self.in_or_out is 'OUT':

                    residuals = np.asarray(data['residuals_OUT_origin'])
                    range_0 = 1e3 * (np.mean(residuals) - 4 * np.std(residuals))
                    ranges_0.append(range_0)
                    range_1 = 1e3 * (np.mean(residuals) + 4 * np.std(residuals))
                    ranges_1.append(range_1)

                    ax1.plot(data['laser_position_OUT'], 1e3 * data['residuals_OUT_origin'], '.', color=acolor)
                    m = dt.make_histogram(1e3 * data['residuals_OUT_origin'], [range_0, range_1], 'um', axe=ax2,
                                          color=acolor)
                mu.append(m)

        if len(ranges_0) > 0:
            ax1.set_ylim([np.min(np.asarray(ranges_0)), np.max(np.asarray(ranges_1))])
            ax2.set_xlim([np.min(np.asarray(ranges_0)), np.max(np.asarray(ranges_1))])
        else:
            ax1.set_ylim([-100, 100])

        ax1.set_xlim([-60, 60])

        if len(self.folders) > 1:

            texts = ax2.get_legend().get_texts()
            for text in texts:
                legends.append(text._text)

            legends = np.asarray([label + '  ' + legend for label, legend in zip(labels, legends)])

            ax2.legend(legends, bbox_to_anchor=(1.05, 1.90), loc=2, borderpad=1)

            prairie.style(ax1)
            prairie.style(ax2)

            ax1.set_title('Wire position error overs scans', loc='left')
            ax1.set_ylabel('Error (\u03BCm)')
            ax1.set_xlabel('Laser position (mm)')
            ax2.set_title('Wire position error histogram', loc='left')
            ax2.set_ylabel('Occurence')
            ax2.set_xlabel('Error (\u03BCm)')

            prairie.style(ax1)
            prairie.style(ax2)

            self.fig.tight_layout()
            self.fig.subplots_adjust(right=0.7)