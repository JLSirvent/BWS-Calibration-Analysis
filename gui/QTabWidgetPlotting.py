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

import sys

from gui.QTab import QTab
from gui.QTabEccentricities import QTabEccentricities
from gui.QTabSpeeds_Positions import QTabSpeeds_Positions
from gui.QTabCalibration import QTabCalibration
from gui.QTabOPSProcessing import QTabOPSProcessing
from gui.QTabRDS import QTabRDS
from gui.QTabFPC import QTabFPC
from PyQt5.QtWidgets import QTabWidget, QApplication


class QTabWidgetPlotting(QTabWidget):

    def __init__(self, parent=None):

        super(QTabWidgetPlotting, self).__init__(parent)

        self.tab_calibration_IN = QTabCalibration('IN')
        self.tab_calibration_OUT = QTabCalibration('OUT')
        self.tab_speeds = QTabSpeeds_Positions('Speed ','Time [ms]','Angular speed [rad/s]',8)
        self.tab_positions = QTabSpeeds_Positions('Position ', 'Time [ms]', 'Angular Position [rad]', 1)
        self.tab_eccentricities = QTabEccentricities()
        self.tab_fpc = QTabFPC()


        self.tab_position = QTab('Disk position',
                                 'Time (s)',
                                 'Angular position (rad)')

        self.tab_speed = QTab('Disk speed',
                              'Time (s)',
                              'Angular speed (rad/s)')

        self.tab_eccentricity = QTab('Position error and eccentricity compensation',
                                     'Angular position (rad)',
                                     'Position error (urad)')


        self.tab_OPS_processing = QTabOPSProcessing()

        self.tab_RDS = QTabRDS()

        self.addTab(self.tab_calibration_IN, "Calibration - IN")
        self.addTab(self.tab_calibration_OUT, "Calibration - OUT")
        self.addTab(self.tab_speeds,"Speeds")
        self.addTab(self.tab_positions,"Positions")
        self.addTab(self.tab_eccentricities,"Eccentricities")
        self.addTab(self.tab_fpc,'FPC')

        self.addTab(self.tab_position, "Disk position")
        self.addTab(self.tab_speed, "Speed")
        self.addTab(self.tab_eccentricity, "Eccentricity")
        self.addTab(self.tab_OPS_processing, "OPS Processing")
        self.addTab(self.tab_RDS, "RDS plot")


        # self.setFixedWidth(800)
        # self.setFixedHeight(800)

def main():
    app = QApplication(sys.argv)
    ex = QTabWidgetPlotting()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

