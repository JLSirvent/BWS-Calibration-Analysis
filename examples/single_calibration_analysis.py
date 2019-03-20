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


from lib import diagnostic_tools as dt



# BWS PROTOTYPE SN64 (PSB_PXBWSRA005_CR000002)
# -------------------------------------------
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PSB_PXBWSRA005_CR000002\ProcessedData\SN64__2017_12_13__14_28_Short PROCESSED'
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PSB_PXBWSRA005_CR000002\ProcessedData\SN64__2017_12_13__14_49_Short PROCESSED'
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PSB_PXBWSRA005_CR000002\ProcessedData\SN64__2017_12_14__15_53 PROCESSED'
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PSB_PXBWSRA005_CR000002\ProcessedData\SN64__2017_12_19__14_39 PROCESSED'
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PSB_PXBWSRA005_CR000002\ProcessedData\SN64__2017_12_19__14_51 PROCESSED'
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PSB_PXBWSRA005_CR000002\ProcessedData\SN64__2017_12_19__15_57 PROCESSED'
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PSB_PXBWSRA005_CR000002\ProcessedData\SN64__2018_01_16__16_23 PROCESSED'
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PSB_PXBWSRA005_CR000002\ProcessedData\SN64__2018_01_17__15_03 PROCESSED'


# BWS PROTOTYPE SN65 (PSB-PXBWSRA005-CR000001)
# -------------------------------------------

# BWS PROTOTYPE PS SN128 (PS_PXBWSRB011_CR000001)
# -----------------------------------------------

# For PS Minimum systematics
# Slits per Turn --> 29386
# Out correction --> 4.5 Positions

#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PS_PXBWSRB011_CR000001\ProcessedData\S128__2018_01_12__09_53 PROCESSED'
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PS_PXBWSRB011_CR000001\ProcessedData\S128__2018_01_12__10_31 PROCESSED'
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PS_PXBWSRB011_CR000001\ProcessedData\S128__2018_01_12__16_44 PROCESSED'
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PS_PXBWSRB011_CR000001\ProcessedData\S128__2018_01_12__17_01 PROCESSED'
#PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PS_PXBWSRB011_CR000001\ProcessedData\S128__2018_01_12__17_14 PROCESSED'

PROCESSED_folder = 'G:\Projects\BWS_Calibrations\Calibrations\PSB_PXBWSRA005-CR000010\ProcessedData\S074__2019_03_08__10_47 PROCESSED'

ParametersCurve = []

# Complete calibration plot
#dt.plot_calibration(folder_name=PROCESSED_folder, in_or_out='IN', complete_residuals_curve=False)
#dt.plot_calibration_INOUT(folder_name=PROCESSED_folder,complete_residuals_curve=False, remove_sytematics=False, N = 1, impose_parameters=False, parameters = ParametersCurve, inout_independent=True)

# Plot distance between peaks
dt.plot_peaks_distance(folder_name=PROCESSED_folder)

# All position profile plot (may be long)
#dt.plot_all_positions(folder_name=PROCESSED_folder, in_or_out='IN')

# All eccentricity profiles plot (may be long)
#dt.plot_all_eccentricity(folder_name=PROCESSED_folder, in_or_out='OUT')

#dt.plot_all_eccentricityV2(folder_name=PROCESSED_folder)

# All speed profiles plot (may be long)
#dt.plot_all_speed(folder_name=PROCESSED_folder, in_or_out='IN')
#dt.plot_all_speedV2(folder_name=PROCESSED_folder)

# Relative distance signature plot (may be long)
#dt.plot_RDS(folder_name=PROCESSED_folder, in_or_out='OUT')

# References detection in time VS scan number
#dt.plot_all_referencedetections(folder_name=PROCESSED_folder, in_or_out='OUT', timems = 340)
