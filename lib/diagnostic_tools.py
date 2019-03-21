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


import os
import numpy as np
import configparser
import scipy.io as sio

from math import sqrt

from matplotlib import mlab
from matplotlib import gridspec
from matplotlib import cm as cmx
from matplotlib import pyplot as plt
from matplotlib import colors as colors
from matplotlib import patches as mpatches

from nptdms import TdmsFile
from scipy.stats import norm
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error

from lib import utils
from lib import prairie
from lib import ops_processing as ops


DPI = 200


# Plotting tools ----------------------------------------------------------------------------------


def make_histogram(data, data_range, units, axe=None, color=None, projected=None, zorder=None):
    """
    Make an histogram of data inside a certain data_range and add a gaussian fit in the legend
    
    Args:
        data: data to be analyse
        data_range: data range to be histogramed
        units: units of the data
        axe: axe that will carry the plot
        color: color of the plot
         
        
    Returns: legend giving mean value and sigma of the gaussian fit
    """

    # Data Cleanup
    data = data[(data >= data_range[0]) & (data <= data_range[1])]
    # ----

    binshist = np.linspace(data_range[0], data_range[1], 50)

    data_range = np.asarray(data_range)
    (mu, sigma) = norm.fit(data)
    bins = np.arange(data_range[0], data_range[1], (data_range[1] - data_range[0]) / 500)
    y = mlab.normpdf(bins, mu, sigma)
    lbl = '\u03C3 ' + "{:3.3f}".format(sigma / np.sqrt(2)) + '   \n' + '\u03BC ' + "{:3.3f}".format(
        mu) + '  (' + units + ')'

    if axe is None:
        plt.hist(data, bins=binshist, normed=0, alpha=0.3)
        plt.plot(bins, y, linewidth=2, color='black')
        plt.legend(['\u03C3 : ' + "{:3.3f}".format(sigma/np.sqrt(2)) + ' ' + units + '\n' + '\u03BC: ' + "{:3.3f}".format(mu) + ' ' + units])

    else:

        if color is not None:
            axe.hist(data, bins=binshist, normed=1, alpha=0.3, color=color)
            axe.plot(bins, y, linewidth=2, color=color, label = lbl)
        else:
            axe.hist(data, bins=binshist, normed=1, alpha=0.3)
            axe.plot(bins, y, linewidth=2, color= 'k', label = lbl)

    return ["{:3.2f}".format(mu), "{:3.2f}".format(sigma / np.sqrt(2))]


# Single calibration analysis  ---------------------------------------------------------------------


def plot_calibration(folder_name, in_or_out, save=False, saving_name=None, complete_residuals_curve=False, separate=False):
    """
    Plot the complete calibration figure of a measurement set

    Args:
        folder_name: folder containing PROCESSED_IN and PROCESSED_OUT, the processed data
        in_or_out: 'IN' or 'OUT' analysis
        save: save the figure as png (figure will not be displayed if True)
        saving_name: Name of the png file (without extension)
    """

    if in_or_out is 'IN':
        filename = 'PROCESSED_IN.mat'
        color = '#018BCF'
    elif in_or_out is 'OUT':
        filename = 'PROCESSED_OUT.mat'
        color = '#0EA318'

    parameter_file = utils.resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    positions_for_fit = eval(config.get('OPS processing parameters', 'positions_for_fit'))
    positions_for_analysis = eval(config.get('OPS processing parameters', 'positions_for_analysis'))
    tank_center = eval(config.get('Geometry', 'stages_position_at_tank_center'))

    data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
    occlusion_position = data['occlusion_position']
    laser_position = data['laser_position']
    idxs = np.argsort(laser_position)
    occlusion_position = occlusion_position[idxs]
    laser_position = laser_position[idxs]

    laser_position = -laser_position + tank_center

    if in_or_out is 'OUT':
        occlusion_position = np.pi / 2 - occlusion_position

    unique_laser_position = np.unique(laser_position)
    occlusion_position_mean = []

    for laser_pos in unique_laser_position:
        occlusion_position_mean.append(np.mean(occlusion_position[np.where(laser_position == laser_pos)[0]]))

    occlusion_position_mean = np.asarray(occlusion_position_mean)

    off1 = [int(positions_for_fit[0] / 100 * unique_laser_position.size),
            int(positions_for_fit[1] / 100 * unique_laser_position.size)]

    popt, pcov = curve_fit(utils.theoretical_laser_position, occlusion_position_mean[off1[0]:off1[1]],
                           unique_laser_position[off1[0]:off1[1]],bounds=([-5, 80, 100], [5, 500, 500]))

    # POPT Values:
    # -----------
    # popt[0] = Phase , popt[1] = CenterOffset, popt[2] = ForkLength

    theorical_laser_position_mean = utils.theoretical_laser_position(occlusion_position_mean,popt[0], popt[1], popt[2])
    theoretical_laser_position = utils.theoretical_laser_position(occlusion_position, popt[0], popt[1], popt[2])
    param = popt

    off2 = [int(positions_for_analysis[0] / 100 * laser_position.size),
            int(positions_for_analysis[1] / 100 * laser_position.size)]

    laser_position = laser_position[off2[0]:off2[1]]
    theoretical_laser_position = theoretical_laser_position[off2[0]:off2[1]]
    occlusion_position = occlusion_position[off2[0]:off2[1]]

    residuals = laser_position - theoretical_laser_position

    if complete_residuals_curve is True:
        d = 3
    else:
        d = 2

    if separate is True:
        fig = plt.figure(figsize=(8, 2.5))
        prairie.use()
        gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
        ax3 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
    else:
        fig = plt.figure(figsize=(8, d*2))
        prairie.use()
        ax2 = plt.subplot2grid((d, 2), (1, 1))
        ax3 = plt.subplot2grid((d, 2), (1, 0))
        ax1 = plt.subplot2grid((d, 2), (0, 0), colspan=2)

    residuals = residuals[off2[0]:off2[1]]
    make_histogram(1e3*residuals, [-300, 300], '\u03BCm', axe=ax2, color=color)
    ax2.set_title('Wire position error histogram', loc='left')
    ax2.set_xlabel('Wire position error (\u03BCm)')
    ax2.set_ylabel('Occurrence')
    prairie.style(ax2)

    ax3.plot(laser_position, 1e3*residuals, '.', color=color, markersize=1.5)
    ax3.set_ylim([-300, 300])
    ax3.set_title('Wire position error', loc='left')
    ax3.set_ylabel('Wire position error (\u03BCm)')
    ax3.set_xlabel('Laser position (mm)')
    prairie.style(ax3)

    plt.tight_layout()

    if separate is True:

        if save is True:
            plt.show(block=False)

            if saving_name is not None:
                plt.savefig(saving_name + '_calibration_residuals.png', format='png', dpi=DPI)
            else:
                print('saving_name is None - Figure not saved')
        else:
            plt.show(block=True)

        fig.clear()

    equation = "{:3.2f}".format(param[1]) + '-' + "{:3.2f}".format(param[2]) + '*' + 'cos(\u03C0-x+' + "{:3.2f}".format(
        param[0]) + ')'
    legend = 'Theoretical Wire position: ' + equation

    if separate is True:
        fig = plt.figure(figsize=(8, 2.5))
        ax1 = fig.add_subplot(111)
        prairie.use()

    ax1.plot(occlusion_position_mean, theorical_laser_position_mean, linewidth=0.5, color='black')
    ax1.plot(occlusion_position, laser_position, '.', color=color, markersize=4)
    ax1.legend([legend, 'Measured positions'])
    ax1.set_title('[' + folder_name.split('\\')[::-1][0] + '  ' + in_or_out + '] Theoretical wire positions vs. measured positions', loc='left')
    ax1.set_xlabel('Angular position at laser crossing (rad)')
    ax1.set_ylabel('Laser position (mm)')
    prairie.style(ax1)

    if complete_residuals_curve is True:

        ax4 = plt.subplot2grid((d, 2), (2, 0), colspan=2)
        ax4.plot(1e3*residuals, '.', color=color, markersize=1.5)
        ax4.plot(1e3*residuals, color=color, linewidth=0.5)
        ax4.set_title('Wire position error over scans', loc='left')
        ax4.set_ylabel('Wire position error (\u03BCm)')
        ax4.set_xlabel('Scan #')
        prairie.style(ax4)

    plt.tight_layout()

    if save is True:
        plt.show(block=False)

        if saving_name is not None:
            if separate is True:
                plt.savefig(saving_name + '_calibration_curve.png', format='png', dpi=DPI)
            else:
                plt.savefig(saving_name + '_calibration.png', format='png', dpi=DPI)
        else:
            print('saving_name is None - Figure not saved')
    else:
        plt.show(block=True)


def plot_calibration_INOUT(folder_name, save=False, saving_name=None, complete_residuals_curve=False, separate=False, remove_sytematics=False, N=1, impose_parameters=False, inout_independent=False, parameters=[0,0,0]):
    """
    Plot the complete calibration figure of a measurement set

    Args:
        folder_name: folder containing PROCESSED_IN and PROCESSED_OUT, the processed data
        in_or_out: 'IN' or 'OUT' analysis
        save: save the figure as png (figure will not be displayed if True)
        saving_name: Name of the png file (without extension)
    """


    filenameIN = 'PROCESSED_IN.mat'
    colorIN = '#018BCF'

    filenameOUT = 'PROCESSED_OUT.mat'
    colorOUT = '#0EA318'

    parameter_file = utils.resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    positions_for_fit = eval(config.get('OPS processing parameters', 'positions_for_fit'))
    positions_for_analysis = eval(config.get('OPS processing parameters', 'positions_for_analysis'))
    tank_center = eval(config.get('Geometry', 'stages_position_at_tank_center'))
    SlitsperTurn = eval(config.get('OPS processing parameters', 'slits_per_turn'))

    #AngularIncrement = 2 * np.pi / SlitsperTurn
    #AngularIncrementC = 2 * np.pi / (29386)

    # IN
    data_IN = sio.loadmat(folder_name + '/' + filenameIN, struct_as_record=False, squeeze_me=True)
    occlusion_position_IN = data_IN['occlusion_position']
    laser_position_IN = data_IN['laser_position']
    scan_number_IN =  data_IN['scan_number']
    idxs_IN = np.argsort(scan_number_IN)
    scan_number_IN= scan_number_IN[idxs_IN]

    occlusion_position_IN = occlusion_position_IN[idxs_IN]

    #occlusion_position_IN = occlusion_position_IN/AngularIncrement
    #occlusion_position_IN = occlusion_position_IN * AngularIncrementC

    laser_position_IN = laser_position_IN[idxs_IN]
    laser_position_IN = -laser_position_IN + tank_center

    #OUT
    data_OUT = sio.loadmat(folder_name + '/' + filenameOUT, struct_as_record=False, squeeze_me=True)
    occlusion_position_OUT = data_OUT['occlusion_position']
    laser_position_OUT = data_OUT['laser_position']
    scan_number_OUT = data_OUT['scan_number']
    idxs_OUT = np.argsort(scan_number_OUT)
    occlusion_position_OUT = occlusion_position_OUT[idxs_OUT]

    #occlusion_position_OUT = occlusion_position_OUT/AngularIncrement
    #occlusion_position_OUT = occlusion_position_OUT * AngularIncrementC

    laser_position_OUT = laser_position_OUT[idxs_OUT]
    scan_number_OUT = scan_number_OUT[idxs_OUT]
    laser_position_OUT = -laser_position_OUT + tank_center
    #occlusion_position_OUT = (np.pi / 2) + 4.5 * AngularIncrementC - occlusion_position_OUT

    unique_laser_position = np.unique(laser_position_IN)
    occlusion_position_mean_IN = []
    occlusion_position_mean_OUT = []

    for laser_pos in unique_laser_position:
        occlusion_position_mean_IN.append(np.mean(occlusion_position_IN[np.where(laser_position_IN == laser_pos)[0]]))
        occlusion_position_mean_OUT.append(np.mean(occlusion_position_OUT[np.where(laser_position_OUT == laser_pos)[0]]))

    occlusion_position_mean_IN = np.asarray(occlusion_position_mean_IN)
    occlusion_position_mean_OUT = np.asarray(occlusion_position_mean_OUT)

    occlusion_position_mean = np.concatenate((occlusion_position_mean_IN, occlusion_position_mean_OUT),axis=0)
    UniqueLPIN= np.unique(laser_position_IN)
    UniqueLPOUT = np.unique(laser_position_OUT)

    if inout_independent is True:
        popt_in, pcov = curve_fit(utils.theoretical_laser_position, occlusion_position_mean_IN,
                               UniqueLPIN, bounds=([-5, 80, 100], [5, 500, 500]))
        popt_out, pcov = curve_fit(utils.theoretical_laser_position, occlusion_position_mean_OUT,
                               UniqueLPOUT, bounds=([-5, 80, 100], [5, 500, 500]))

    else:
        unique_laser_position_fit = np.concatenate((UniqueLPIN,UniqueLPOUT), axis=0)

        if impose_parameters is True:
            popt = parameters
        else:
            popt, pcov = curve_fit(utils.theoretical_laser_position, occlusion_position_mean,
                               unique_laser_position_fit,bounds=([-5, 80, 100], [5, 500, 500]))
        popt_in  = popt
        popt_out = popt

    # POPT Values:
    # -----------
    # popt[0] = Phase , popt[1] = CenterOffset, popt[2] = ForkLength

    param = popt_in
    print(param)

    theorical_laser_position_mean = utils.theoretical_laser_position(occlusion_position_mean_IN,popt_in[0], popt_in[1], popt_in[2])

    theoretical_laser_position_IN = utils.theoretical_laser_position(occlusion_position_IN, popt_in[0], popt_in[1], popt_in[2])
    theoretical_laser_position_OUT = utils.theoretical_laser_position(occlusion_position_OUT, popt_out[0], popt_out[1], popt_out[2])



    #off2 = [int(positions_for_analysis[0] / 100 * laser_position.size),
    #        int(positions_for_analysis[1] / 100 * laser_position.size)]

    #laser_position = laser_position[off2[0]:off2[1]]
    #theoretical_laser_position = theoretical_laser_position[off2[0]:off2[1]]
    #occlusion_position = occlusion_position[off2[0]:off2[1]]

    residuals_IN = laser_position_IN - theoretical_laser_position_IN
    residuals_OUT = laser_position_OUT - theoretical_laser_position_OUT

    unique_residuals_in = []
    unique_residuals_out = []

    for laser_pos in unique_laser_position:
        unique_residuals_in.append(np.mean(residuals_IN[np.where(laser_position_IN == laser_pos)]))
        unique_residuals_out.append(np.mean(residuals_OUT[np.where(laser_position_OUT == laser_pos)]))

    unique_residuals_in = np.asarray(unique_residuals_in)
    unique_residuals_out = np.asarray(unique_residuals_out)

    unique_residuals_in = np.convolve(unique_residuals_in, np.ones((N,))/N, mode='valid')
    unique_residuals_out = np.convolve(unique_residuals_out, np.ones((N,))/N, mode='valid')

    UniqueLPIN = UniqueLPIN[np.int(N/2-1):np.int(UniqueLPIN.size-N/2)]

    if remove_sytematics is True:
        for laser_pos in UniqueLPIN:
            residuals_IN[np.where(laser_position_IN==laser_pos)] = residuals_IN[np.where(laser_position_IN==laser_pos)] - unique_residuals_in[np.where(UniqueLPIN==laser_pos)] #np.mean(residuals_IN[np.where(laser_position_IN==laser_pos)])
            residuals_OUT[np.where(laser_position_OUT==laser_pos)] = residuals_OUT[np.where(laser_position_OUT==laser_pos)] - unique_residuals_out[np.where(UniqueLPIN==laser_pos)]#np.mean(residuals_OUT[np.where(laser_position_OUT==laser_pos)])

    #residuals_IN = residuals_IN[np.where(laser_position_IN==UniqueLPIN)]
    #residuals_OUT = residuals_OUT[np.where(laser_position_OUT==UniqueLPIN)]

    #laser_position_IN_s = laser_position_IN[np.where(laser_position_IN==UniqueLPIN)]
    #laser_position_OUT_s = laser_position_OUT[np.where(laser_position_OUT==UniqueLPIN)]

    if complete_residuals_curve is True:
        d = 3
    else:
        d = 2

    if separate is True:
        fig = plt.figure(figsize=(8, 6))
        prairie.use()
        gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
        ax3 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
    else:
        fig = plt.figure(figsize=(8, 6))
        prairie.use()
        ax2 = plt.subplot2grid((d, 2), (1, 1))
        ax3 = plt.subplot2grid((d, 2), (1, 0))
        ax1 = plt.subplot2grid((d, 2), (0, 0), colspan=2)

    #residuals_IN  = residuals_IN[off2[0]:off2[1]]
    #residuals_OUT = residuals_OUT[off2[0]:off2[1]]

    make_histogram(1e3*residuals_IN, [-200, 200], '\u03BCm', axe=ax2, color=colorIN)
    make_histogram(1e3*residuals_OUT, [-200, 200], '\u03BCm', axe=ax2, color=colorOUT)
    ax2.set_title('Wire position error histogram', loc='left')
    ax2.set_xlabel('Wire position error (\u03BCm)')
    ax2.set_ylabel('Occurrence')
    prairie.style(ax2)


    ax3.plot(laser_position_IN, 1e3*residuals_IN, '.', color=colorIN, markersize=1.5)
    #ax3.plot(UniqueLPIN,1e3*unique_residuals_in, color=colorIN)
    ax3.plot(laser_position_OUT, 1e3*residuals_OUT, '.', color=colorOUT, markersize=1.5)
    #ax3.plot(UniqueLPIN,1e3*unique_residuals_out, color=colorOUT)

    ax3.set_ylim([-200, 200])
    ax3.set_title('Wire position error', loc='left')
    ax3.set_ylabel('Wire position error (\u03BCm)')
    ax3.set_xlabel('Laser position (mm)')
    prairie.style(ax3)

    plt.tight_layout()

    if separate is True:

        if save is True:
            plt.show(block=False)

            if saving_name is not None:
                plt.savefig(saving_name + '_calibration_residuals.png', format='png', dpi=DPI)
            else:
                print('saving_name is None - Figure not saved')
        else:
            plt.show(block=True)

        fig.clear()

    equation = "{:3.2f}".format(param[1]) + '-' + "{:3.2f}".format(param[2]) + '*' + 'cos(\u03C0-x+' + "{:3.2f}".format(
        param[0]) + ')'
    legend = 'Theoretical Wire position: ' + equation

    if separate is True:
        fig = plt.figure(figsize=(8, 2.5))
        ax1 = fig.add_subplot(111)
        prairie.use()

    ax1.plot(occlusion_position_mean_IN, theorical_laser_position_mean, linewidth=0.5, color='black')
    ax1.plot(occlusion_position_IN, laser_position_IN, '.', color=colorIN, markersize=4)
    ax1.plot(occlusion_position_OUT, laser_position_OUT, '.', color=colorOUT, markersize=4)

    ax1.legend([legend, 'Data IN', 'Data OUT'])
    ax1.set_title('[' + folder_name.split('\\')[::-1][0] + '  IN + OUT ] Theoretical wire positions vs. measured positions', loc='left')
    ax1.set_xlabel('Angular position at laser crossing (rad)')
    ax1.set_ylabel('Laser position (mm)')
    prairie.style(ax1)

    if complete_residuals_curve is True:

        ax4 = plt.subplot2grid((d, 2), (2, 0), colspan=2)
        ax4.plot(scan_number_IN, 1e3*residuals_IN, '.', color=colorIN, markersize=1.5)
        ax4.plot(scan_number_OUT, 1e3*residuals_OUT,'.', color=colorOUT,markersize=1.5)
        ax4.set_title('Wire position error over scans', loc='left')
        ax4.set_ylabel('Wire position error (\u03BCm)')
        ax4.set_xlabel('Scan #')
        prairie.style(ax4)

    plt.tight_layout()

    if save is True:
        plt.show(block=False)

        if saving_name is not None:
            if separate is True:
                plt.savefig(saving_name + '_calibration_curve.png', format='png', dpi=DPI)
            else:
                plt.savefig(saving_name + '_calibration.png', format='png', dpi=DPI)
        else:
            print('saving_name is None - Figure not saved')
    else:
        plt.show(block=True)

def plot_peaks_distance(folder_name):
    f = plt.figure(figsize = [14,7])
    ax0 = f.add_subplot(1,2,1)
    ax0.set_xlabel('Angular Position [rad]')
    ax0.set_ylabel('Projected Position [mm]')
    ax0.set_title('Occlusions Detection')

    ax1 = f.add_subplot(1,2,2)
    ax1.set_ylabel('Distance between occlusions [mm]')
    ax1.set_xlabel('Projected Position [mm]')
    ax1.set_title('Occlusions Difference')

    for s in range(0,2):
        if s == 1:
            Filename = 'PROCESSED_IN.mat'
            Col = 'b'
            Lbl = 'IN'
        else:
            Filename = 'PROCESSED_OUT.mat'
            Col = 'r'
            Lbl = 'OUT'

        data = sio.loadmat(folder_name + '/' + Filename, struct_as_record=False, squeeze_me=True)
        laser_position = data['laser_position']
        oc = data['oc']
        valid = data['data_valid']

        #Cleanup and only take those valid
        Idx = np.where(valid==1)[0]
        pos = laser_position[Idx]
        oc = oc[Idx,:]
        # **

        FitOrder = 5

        fit_func = [[],[]]
        for i in range(0, 2):
            oc_c = oc[:,i]
            fit_poly = np.polyfit(oc_c, pos, FitOrder)
            fit_func[i] = np.poly1d(fit_poly)
            xfit = np.arange(np.min(oc_c), np.max(oc_c),(np.max(oc_c)-np.min(oc_c))/100)
            yfit = fit_func[i](xfit)
            ax0.plot(oc_c, pos, '.' + Col, label = Lbl)
            ax0.plot(xfit, yfit, Col)

        Difference = np.abs(fit_func[0](oc[:,1]) -  fit_func[0](oc[:,0]))

        ax1.plot(pos,Difference,'.', color = Col ,label = Lbl + '\nMean:{:.2f}mm'.format(np.mean(Difference))+ '\nRMSE: {:.1f}um'.format(np.std(1e3*Difference)))

    ax0.grid()
    ax0.legend()
    ax1.grid()
    ax1.legend()
    ax1.set_ylim(2.4, 3.3)
    plt.show()

def plot_all_eccentricity(folder_name, in_or_out, howmuch='all', diagnostic=False, save=False, saving_name=None, separate=False):
    """
          Plot all the eccenticity curve extracted form the OPS processing to see if any jump occured

          Args:
              folder_name: folder containing PROCESSED_IN and PROCESSED_OUT, the processed data
              save: save the figure as png (figure will not be displayed if True)
              saving_name: Name of the png file (without extension)
          """

    if in_or_out is 'IN':
        filename = 'PROCESSED_IN.mat'
        color = '#018BCF'
    elif in_or_out is 'OUT':
        filename = 'PROCESSED_OUT.mat'
        color = '#0EA318'
    off = 100

    data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
    eccentricity = data['eccentricity']
    angular_position_SA = data['angular_position_SA']

    values = range(len(eccentricity)+1)
    jet = cm = plt.get_cmap('jet')
    cNorm = colors.Normalize(vmin=0, vmax=values[-1])
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

    if diagnostic == True or diagnostic == 1:
        laser_position = data['laser_position']
        scan_number = data['scan_number']

    ref_ecc = eccentricity[0]
    ref_ecc = ref_ecc[off:ref_ecc.size - off]
    ref_pos = angular_position_SA[0]
    ref_pos = ref_pos[off:ref_pos.size - off]
    ecc_all = []

    def theor_ecc(x, a, b, c):
        return a * np.sin(x + b) + c

    popt, pcov = curve_fit(theor_ecc, ref_pos, ref_ecc, bounds=([-100, -100, -100], [100, 100, 100]))

    if howmuch == 'all':

        for ecc, pos in zip(eccentricity, angular_position_SA):
            ecc = ecc[off:ecc.size - off]
            pos = pos[off:pos.size - off]
            ecc = utils.resample(np.array([pos, ecc]), np.array([ref_pos, ref_ecc]))
            ecc_all.append(ecc[1])

        [ref_ecc, ref_pos] = [eccentricity[0], angular_position_SA[0]]

        deff = []
        residuals_mean = []

        if separate is True:
            fig = plt.figure(figsize=(8, 2.5))
            prairie.use()
            ax1 = fig.add_subplot(111)
        else:
            fig = plt.figure(figsize=(8, 4))
            prairie.use()
            ax2 = plt.subplot2grid((2, 2), (1, 1))
            ax3 = plt.subplot2grid((2, 2), (1, 0))
            ax1 = plt.subplot2grid((2, 2), (0, 0), colspan=2)

        ax1.plot(ref_pos, 1e3*theor_ecc(ref_pos, popt[0], popt[1], popt[2]), linewidth=0.5, color='black')
        cnt = 1
        for ecc, pos in zip(eccentricity, angular_position_SA):
            colorVal = scalarMap.to_rgba(values[cnt])
            ecc = ecc[off:ecc.size - off]
            pos = pos[off:pos.size - off]
            ax1.plot(pos, 1e3*ecc, linewidth=0.8, color=colorVal)
            cnt = cnt + 1

        if diagnostic == True or diagnostic == 1:

            for ecc, pos in zip(eccentricity, angular_position_SA):
                ecc = ecc[off:ecc.size - off]
                pos = pos[off:pos.size - off]
                # plt.plot(1e3*pos, ecc, linewidth=1)
                deft = np.abs(np.diff(ecc))
                deff.append(np.amax(deft))

        ax1.set_title('Position error and eccentricity compensation - Sensor A', loc='left')
        ax1.set_xlabel('Angular position (rad)')
        ax1.set_ylabel('Position error (mrad)')
        ax1.legend(['Eccentricity global fit', 'Eccentricity profiles (' + str(eccentricity.size) + ')'])
        prairie.style(ax1)

        plt.tight_layout()

        if separate is True:

            if save is True:
                plt.show(block=False)

                if saving_name is not None:
                    plt.savefig(saving_name + '_curve.png', format='png', dpi=DPI)
                else:
                    print('saving_name is None - Figure not saved')
            else:
                plt.show(block=True)

            fig.clear()

            fig = plt.figure(figsize=(8, 2.5))
            prairie.use()
            gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
            ax2 = fig.add_subplot(gs[0])
            ax3 = fig.add_subplot(gs[1])
        cnt = 1
        for ecc, pos in zip(eccentricity, angular_position_SA):
            colorVal = scalarMap.to_rgba(values[cnt])
            ecc = ecc[off:ecc.size - off]
            pos = pos[off:pos.size - off]
            residuals = ecc - theor_ecc(pos, popt[0], popt[1], popt[2])
            ax2.plot(pos, 1e6*residuals, linewidth=0.2, color=colorVal)
            residuals_mean.append(np.mean(residuals))
            cnt = cnt + 1

        ax2.set_title('Position error after compensation', loc='left')
        ax2.set_xlabel('Angular position (rad)')
        ax2.set_ylabel('Position error (\u03BCrad)')
        ax2.legend(['Residuals profiles (' + str(eccentricity.size) + ')'])
        prairie.style(ax2)

        make_histogram(1e6 * np.asarray(residuals_mean), [-10, 10], '\u03BCrad', ax3, projected=True, color=color)
        ax3.set_title('Error histogram (' + str(len(eccentricity)) + ' traces)', loc='left')
        ax3.set_ylabel('Occurrence')
        ax3.set_xlabel('Position error (\u03BCrad)')
        prairie.style(ax2)
        prairie.style(ax3)

        plt.tight_layout()

        if save is True:
            plt.show(block=False)

            if saving_name is not None:
                if separate is True:
                    plt.savefig(saving_name + '_residuals.png', format='png', dpi=DPI)
                else:
                    plt.savefig(saving_name + '.png', format='png', dpi=DPI)
            else:
                print('saving_name is None - Figure not saved')
        else:
            plt.show(block=True)

        # if diagnostic == True or diagnostic == 1:
        #     return [laser_position[np.argmax(np.asarray(deff))], scan_number[np.argmax(np.asarray(deff))]]

    elif howmuch == 'random':

        plt.figure()
        plt.subplot(1, 2, 1)
        prairie.use()()()
        prairie.use_colors('cold')
        plt.plot(ref_pos, theor_ecc(ref_pos, popt[0], popt[1], popt[2]), linewidth=0.5, color='black')
        plt.plot(ref_pos, ref_ecc, linewidth=1)
        plt.subplot(1, 2, 2)
        plt.plot(ref_pos, ref_ecc - theor_ecc(ref_pos, popt[0], popt[1], popt[2]), linewidth=0.5)
        plt.plot(ref_pos, utils.ref_ecc - theor_ecc(ref_pos, popt[0], popt[1], popt[2]))
        plt.plot(ref_pos, ref_ecc - theor_ecc(ref_pos, popt[0], popt[1], popt[2]))
        plt.show()

        return popt

    return ax1

def plot_all_eccentricityV2(folder_name):
    """
          Plot all the eccenticity curve extracted form the OPS processing to see if any jump occured

          Args:
              folder_name: folder containing PROCESSED_IN and PROCESSED_OUT, the processed data
              save: save the figure as png (figure will not be displayed if True)
              saving_name: Name of the png file (without extension)
          """

    fig = plt.figure(figsize=(11, 5.5))
    prairie.use()

    ax1 = plt.subplot2grid((2, 3), (0, 0), colspan=2)
    ax2 = plt.subplot2grid((2, 3), (0, 2), sharex=ax1)
    ax3 = plt.subplot2grid((2, 3), (1, 0), colspan=2, sharex=ax1,sharey=ax1)
    ax4 = plt.subplot2grid((2, 3), (1, 2), sharex=ax1,sharey=ax2)

    for i in range(1,3):
        if i == 1:
            filename = 'PROCESSED_IN.mat'
            title = 'IN'
            ax_all = ax1
            ax_res = ax2
            data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
            eccentricity = data['eccentricity']
            angular_position_SA = data['angular_position_SA']
        else:
            filename = 'PROCESSED_OUT.mat'
            title = 'OUT'
            ax_all = ax3
            ax_res = ax4
            data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
            eccentricity = -data['eccentricity']
            angular_position_SA = (np.pi/2)-data['angular_position_SA']

        off = 100
        values = range(len(eccentricity)+1)
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

        popt, pcov = curve_fit(theor_ecc, ref_pos, ref_ecc, bounds=([-100, -100, -100], [100, 100, 100]))

        for ecc, pos in zip(eccentricity, angular_position_SA):
            ecc = ecc[off:ecc.size - off]
            pos = pos[off:pos.size - off]
            ecc = utils.resample(np.array([pos, ecc]), np.array([ref_pos, ref_ecc]))
            ecc_all.append(ecc[1])

        [ref_ecc, ref_pos] = [eccentricity[0], angular_position_SA[0]]

        deff = []
        residuals_mean = []

        ax_all.plot(ref_pos, 1e3*theor_ecc(ref_pos, popt[0], popt[1], popt[2]), linewidth=0.5, color='black')

        cnt = 1
        for ecc, pos in zip(eccentricity, angular_position_SA):
            colorVal = scalarMap.to_rgba(values[cnt])
            ecc = ecc[off:ecc.size - off]
            pos = pos[off:pos.size - off]
            ax_all.plot(pos, 1e3*ecc, linewidth=0.8, color=colorVal)
            cnt = cnt + 1

        ax_all.set_title('Position error and eccentricity compensation '+ title + ' - Sensor A', loc='left')
        ax_all.set_xlabel('Angular position (rad)')
        ax_all.set_ylabel('Position error (mrad)')
        ax_all.legend(['Eccentricity global fit', 'Eccentricity profiles (' + str(eccentricity.size) + ')'])
        prairie.style(ax_all)

        plt.tight_layout()

        cnt = 1
        for ecc, pos in zip(eccentricity, angular_position_SA):
            colorVal = scalarMap.to_rgba(values[cnt])
            ecc = ecc[off:ecc.size - off]
            pos = pos[off:pos.size - off]
            residuals = ecc - theor_ecc(pos, popt[0], popt[1], popt[2])
            ax_res.plot(pos, 1e6*residuals, linewidth=0.2, color=colorVal)
            residuals_mean.append(np.mean(residuals))
            cnt = cnt + 1

        ax_res.set_title('Position error after compensation', loc='left')
        ax_res.set_xlabel('Angular position (rad)')
        ax_res.set_ylabel('Position error (\u03BCrad)')
        ax_res.legend(['Residuals profiles (' + str(eccentricity.size) + ')'])
        prairie.style(ax_res)

    plt.tight_layout()
    plt.show(block=True)


def plot_all_speed(folder_name, in_or_out, save=False, saving_name=None, separate=True):

    if separate is True:
        fig = plt.figure(figsize=(8, 2.5))
        prairie.use()
        ax1 = fig.add_subplot(111)
    else:
        fig = plt.figure(figsize=(8, 4))
        prairie.use()
        ax2 = plt.subplot2grid((2, 2), (1, 1))
        ax3 = plt.subplot2grid((2, 2), (1, 0))
        ax1 = plt.subplot2grid((2, 2), (0, 0), colspan=2)

    if in_or_out is 'IN':
        filename = 'PROCESSED_IN.mat'
        color = '#018BCF'
    elif in_or_out is 'OUT':
        filename = 'PROCESSED_OUT.mat'
        color = '#0EA318'

    data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
    speed_SA = data['speed_SA']
    time_SA = data['time_SA']

    parameter_file = utils.resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)

    ref_speed = speed_SA[0]
    ref_time = time_SA[0]
    R_speed = []
    M_speed = ref_speed

    offset = 10

    values = range(len(speed_SA)+1)
    jet = cm = plt.get_cmap('jet')
    cNorm = colors.Normalize(vmin=0, vmax=values[-1])
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

    for speed, time in zip(speed_SA, time_SA):
        speed = speed[offset:(speed.size-offset)]
        time = time[offset:(time.size - offset - 1)]
        r_speed = utils.resample(np.array([time, speed]), np.array([ref_time, ref_speed]))
        M_speed = np.add(r_speed[1][0:M_speed.size], M_speed)
        M_speed /= 2

    ax1.plot(ref_time[0:M_speed.size], M_speed, 'k', linewidth=0.5)
    cnt = 1
    N = 8
    for speed, time in zip(speed_SA, time_SA):
        colorVal = scalarMap.to_rgba(values[cnt])
        speed = speed[offset:(speed.size-offset)]
        speed_s = np.convolve(speed,np.ones((N,))/N, mode='valid')
        time = time[offset:(time.size - offset - 1)]
        r_speed = utils.resample(np.array([time, speed]), np.array([ref_time, ref_speed]))
        ax1.plot(time[np.int(N/2):time.size-np.int(N/2)+1], speed_s, linewidth=0.5, color=colorVal)
        R_speed.append(np.mean((r_speed[1][0:M_speed.size] - M_speed)[200:M_speed.size-offset-20]))
        cnt = cnt + 1

    ax1.set_title('Speed profiles', loc='left')
    ax1.set_ylabel('Speed (rad/s)')
    ax1.set_xlabel('Time (s)')
    ax1.legend(['Mean speed', 'Speed profiles (' + str(speed_SA.size) + ')'])
    ax1.set_ylim([0, 150])
    prairie.style(ax1)

    plt.tight_layout()

    if separate is True:

        if save is True:
            plt.show(block=False)

            if saving_name is not None:
                plt.savefig(saving_name + '_curve.png', format='png', dpi=DPI)
            else:
                print('saving_name is None - Figure not saved')
        else:
            plt.show(block=True)

        fig.clear()

        fig = plt.figure(figsize=(8, 2.5))
        prairie.use()
        gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
        ax2 = fig.add_subplot(gs[0])
        ax3 = fig.add_subplot(gs[1])

    for speed, time in zip(speed_SA, time_SA):
        speed = speed[offset:(speed.size-offset)]
        time = time[offset:(time.size - offset - 1)]
        r_speed = utils.resample(np.array([time, speed]), np.array([ref_time, ref_speed]))
        ax2.plot(r_speed[0][200:M_speed.size-offset-20], (r_speed[1][0:M_speed.size] - M_speed)[200:M_speed.size-offset-20], color=color, linewidth=0.5)
        R_speed.append(np.mean((r_speed[1][0:M_speed.size] - M_speed)[200:M_speed.size-offset-20]))

    make_histogram(np.asarray(R_speed), [-5, 5], 'rad/s', ax3, color=color)

    ax2.set_title('Speed profile residuals \n w.r.t the mean speed profile', loc='left')
    ax2.set_ylabel('Residuals (rad/s)')
    ax2.set_xlabel('Time (s)')
    ax2.legend(['Residuals profiles (' + str(speed_SA.size) + ')'])
    prairie.style(ax2)
    ax3.set_title('Error histogram', loc='left')
    ax3.set_ylabel('Occurrence')
    ax3.set_xlabel('Speed error (rad/s)')
    prairie.style(ax3)

    plt.tight_layout()

    if save is True:
        plt.show(block=False)

        if saving_name is not None:
            if separate is True:
                plt.savefig(saving_name + '_residuals.png', format='png', dpi=DPI)
            else:
                plt.savefig(saving_name + '.png', format='png', dpi=DPI)
        else:
            print('saving_name is None - Figure not saved')
    else:
        plt.show(block=True)


def plot_all_speedV2(folder_name):

    fig = plt.figure(figsize=(13, 5.5))
    prairie.use()
    ax1 = plt.subplot2grid((1, 2), (0, 0))
    ax2 = plt.subplot2grid((1, 2), (0, 1), sharey=ax1)
    for i in range(1,3):

        if i==1:
            filename = 'PROCESSED_IN.mat'
            ax_speed = ax1
            title = 'IN'
        else:
            filename = 'PROCESSED_OUT.mat'
            ax_speed = ax2
            title = 'OUT'

        data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
        speed_SA = data['speed_SA']
        time_SA = data['time_SA']

        #parameter_file = utils.resource_path('data/parameters.cfg')
        #config = configparser.RawConfigParser()
        #config.read(parameter_file)

        ref_speed = speed_SA[0]
        ref_time = time_SA[0]
        R_speed = []
        M_speed = ref_speed

        offset = 10

        values = range(len(speed_SA)+1)
        jet = cm = plt.get_cmap('jet')
        cNorm = colors.Normalize(vmin=0, vmax=values[-1])
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

        for speed, time in zip(speed_SA, time_SA):
            speed = speed[offset:(speed.size-offset)]
            time = time[offset:(time.size - offset - 1)]
            r_speed = utils.resample(np.array([time, speed]), np.array([ref_time, ref_speed]))
            M_speed = np.add(r_speed[1][0:M_speed.size], M_speed)
            M_speed /= 2

        ax_speed.plot(ref_time[0:M_speed.size], M_speed, 'k', linewidth=0.5)

        cnt = 1
        N = 8

        for speed, time in zip(speed_SA, time_SA):
            colorVal = scalarMap.to_rgba(values[cnt])
            speed = speed[offset:(speed.size-offset)]
            speed_s = np.convolve(speed,np.ones((N,))/N, mode='valid')
            time = time[offset:(time.size - offset - 1)]
            r_speed = utils.resample(np.array([time, speed]), np.array([ref_time, ref_speed]))
            ax_speed.plot(time[np.int(N/2):time.size-np.int(N/2)+1], speed_s, linewidth=0.5, color=colorVal)
            R_speed.append(np.mean((r_speed[1][0:M_speed.size] - M_speed)[200:M_speed.size-offset-20]))
            cnt = cnt + 1

        ax_speed.set_title('Speed profiles '+ title, loc='left')
        ax_speed.set_ylabel('Speed (rad/s)')
        ax_speed.set_xlabel('Time (s)')
        ax_speed.legend(['Mean speed', 'Speed profiles (' + str(speed_SA.size) + ')'])
        ax_speed.set_ylim([0, 150])
        prairie.style(ax_speed)
        plt.tight_layout()

    plt.show(block=True)


def plot_RDS(folder_name, in_or_out, offset=0, index=None):
    """
        Plot of the relative distance thresholding performed in the OPS processing to correct defaults

        Args:
            folder_name: folder containing PROCESSED_IN and PROCESSED_OUT, the processed data
            in_or_out: 'IN' or 'OUT' analysis
            offset : number of point to remove at the beginning and the end of the data
            index: index of the specific scan to analyse
    """

    if in_or_out is 'IN':
        filename = 'PROCESSED_IN.mat'
    elif in_or_out is 'OUT':
        filename = 'PROCESSED_OUT.mat'

    data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
    time_SA = data['time_SA']
    time_SB = data['time_SB']
    print(time_SA.size)

    parameter_file = utils.resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    rdcp = eval(config.get('OPS processing parameters', 'relative_distance_correction_prameters'))

    fig = plt.figure()
    #prairie.use()()()
    ax = fig.add_subplot(111)
    plt.axhspan(rdcp[1], rdcp[0], color='black', alpha=0.1)

    if index == None:
        for i in np.arange(0, time_SA.size):
            distances_A = np.diff(time_SA[i])[offset:time_SA[i].size - 1 - offset]
            rel_distances_A = np.divide(distances_A[1::], distances_A[0:distances_A.size - 1])
            distances_B = np.diff(time_SB[i])[offset:time_SB[i].size - 1 - offset]
            rel_distances_B = np.divide(distances_B[1::], distances_B[0:distances_B.size - 1])
            ax.plot(1e3 * time_SA[i][offset:time_SA[i].size - 2 - offset], rel_distances_A, '.',
                     color=prairie.use_colors('cold', i))
            ax.plot(1e3 * time_SB[i][offset:time_SB[i].size - 2 - offset], rel_distances_B, '.',
                     color=prairie.use_colors('hot', i))
    else:
        i = index
        distances_A = np.diff(time_SA[i])[offset:time_SA[i].size - 1 - offset]
        rel_distances_A = np.divide(distances_A[1::], distances_A[0:distances_A.size - 1])
        distances_B = np.diff(time_SB[i])[offset:time_SB[i].size - 1 - offset]
        rel_distances_B = np.divide(distances_B[1::], distances_B[0:distances_B.size - 1])
        ax.plot(1e3 * time_SA[i][offset:time_SA[i].size - 2 - offset], rel_distances_A, '.',
                 color=prairie.use_colors('cold', i))
        ax.plot(1e3 * time_SB[i][offset:time_SB[i].size - 2 - offset], rel_distances_B, '.',
                 color=prairie.use_colors('hot', i))

    ax.set_xlabel('Time (' + '\u03BC' + 's)')
    ax.set_ylabel('Relative distance')
    ax.set_title('RDS plot', loc='left')
    red_patch = mpatches.Patch(color=prairie.use_colors('cold', i), label='Sensor A')
    blue_patch = mpatches.Patch(color=prairie.use_colors('hot', i), label='Sensor B')
    ax.legend(handles=[blue_patch, red_patch])
    prairie.style(ax)
    plt.show()


def plot_all_positions(folder_name, in_or_out, save=False, saving_name=None):

    fig = plt.figure(figsize=(8, 2.5))
    prairie.use()
    ax1 = fig.add_subplot(111)

    if in_or_out is 'IN':
        filename = 'PROCESSED_IN.mat'
    elif in_or_out is 'OUT':
        filename = 'PROCESSED_OUT.mat'

    data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
    angular_position_SA = data['angular_position_SB']
    time_SA = data['time_SB']

    values = range(len(angular_position_SA)+1)
    jet = cm = plt.get_cmap('jet')
    cNorm = colors.Normalize(vmin=0, vmax=values[-1])
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

    cnt = 1
    for pos, time in zip(angular_position_SA, time_SA):
        colorVal = scalarMap.to_rgba(values[cnt])
        ax1.plot(time[2:time.size - 2], pos[2:pos.size - 2], linewidth=0.5,color=colorVal)
        cnt = cnt + 1

    ax1.set_title('Motor angular positions', loc='left')
    ax1.set_ylabel('Position (rad)')
    ax1.set_xlabel('Time (s)')
    ax1.legend(['position profiles (' + str(angular_position_SA.size) + ')'])
    prairie.style(ax1)

    plt.tight_layout()

    if save is True:
        plt.show(block=False)

        if saving_name is not None:
            plt.savefig(saving_name + '.png', format='png', dpi=DPI)
        else:
            print('saving_name is None - Figure not saved')
    else:
        plt.show(block=True)


def plot_all_referencedetections(folder_name, in_or_out,timems=20):

    fig = plt.figure(figsize=(8, 2.5))
    prairie.use()
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)

    if in_or_out is 'IN':
        filename = 'PROCESSED_IN.mat'
    elif in_or_out is 'OUT':
        filename = 'PROCESSED_OUT.mat'

    data = sio.loadmat(folder_name + '/' + filename, struct_as_record=False, squeeze_me=True)
    angular_position_SA = data['angular_position_SA']
    time_SA = data['time_SA']
    angular_position_SB = data['angular_position_SB']
    time_SB = data['time_SB']
    laser_position = data['laser_position']
    occlusion_position = data['occlusion_position']
    scan_number = data['scan_number']

    time_refA  = []
    laser_posA = []
    scan_numA  = []
    pos_at_timeA = []

    time_refB  = []
    laser_posB = []
    scan_numB  = []
    pos_at_timeB = []

    for i in range(0, angular_position_SA.size):
        time_refA.append(time_SA[i][np.where(angular_position_SA[i] > 0)[0][0]])
        try:
            pos_at_timeA.append(angular_position_SA[i][(np.where(time_SA[i] > timems / 1000)[0][0])])
        except:
            print('ReferencesError A')
    #    laser_posA.append(laser_position[i])
    #    scan_numA.append(scan_number[i])

    for i in range(0, angular_position_SB.size):
        time_refB.append(time_SB[i][np.where(angular_position_SB[i] > 0)[0][0]])
        try:
            pos_at_timeB.append(angular_position_SB[i][(np.where(time_SB[i] > timems / 1000)[0][0])])
        except:
            print('ReferencesError A')

    #    laser_posB.append(laser_position[i])
    #    scan_numB.append(scan_number[i])

    #total_scan_num = []
    #for i in range(0,laser_pos.size):
    #    total_scan_num.append( last + scan_num[np.where(laser_position)])

    time_refA = np.asarray(time_refA) * 1e3
    time_refB = np.asarray(time_refB) * 1e3

    ax1.plot(np.asarray(pos_at_timeA)* 360 / (2 * np.pi), 'ob')
    ax1.plot(np.asarray(pos_at_timeB)* 360 / (2 * np.pi), 'or')
    ax1.set_title('Position at a given time' + in_or_out + ' ' + str(timems) + 'ms', loc='left')
    ax1.set_ylabel('Angular Position (deg)')
    ax1.set_xlabel('Scan Number')

    if in_or_out is 'OUT':
        occlusion_position = np.pi/2 - occlusion_position

    ax2.plot(occlusion_position * 360 / (2 * np.pi), 'ob')
    #ax2.set_ylim([69,78])
    ax2.set_title('Angular position on Laser Crosing', loc='left')
    ax2.set_ylabel('Angular Position (deg)')
    ax2.set_xlabel('Scan Number')

    plt.tight_layout()
    plt.show(block=True)

# Raw data analysis (TDMS)  ------------------------------------------------------------------------


def plot_rawdata_from_tdms(file):

    """
    Just plots data from a TDMS File
    """

    file = utils.reformate_path(file)

    parameter_file = utils.resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    sampling_frequency = eval(config.get('OPS processing parameters', 'sampling_frequency'))
    start_time_out = int(sampling_frequency * 0.020)
    print(start_time_out)

    tdms_file = TdmsFile(file)
    data__s_a__in = tdms_file.object('Picoscope Data', 'DISC PH. HOME dir IN').data
    data__s_b__in = tdms_file.object('Picoscope Data', 'DISC PH. IN dir IN').data
    data__p_d__in = np.abs(-tdms_file.object('Picoscope Data', 'WIRE PH. dir IN').data)
    data__s_a__out = tdms_file.object('Picoscope Data', 'DISC PH. HOME dir HOME').data[start_time_out::]
    data__s_b__out = tdms_file.object('Picoscope Data', 'DISC PH. IN dir HOME').data[start_time_out::]
    data__p_d__out = np.abs(-tdms_file.object('Picoscope Data', 'WIRE PH. dir HOME').data)[start_time_out::]

    timein  = np.arange(data__s_a__in.size) / sampling_frequency
    timeout  = np.arange(data__s_a__out.size) / sampling_frequency

    plt.figure()

    plt.subplot(321)
    plt.plot(timein,data__s_a__in)
    plt.subplot(322)
    plt.plot(timeout, data__s_a__out)

    plt.subplot(323)
    plt.plot(timein,data__s_b__in)
    plt.subplot(324)
    plt.plot(timeout, data__s_b__out)

    plt.subplot(325)
    plt.plot(timein,data__p_d__in)
    plt.subplot(326)
    plt.plot(timeout, data__p_d__out)

    plt.show()


def make_one_plot_analysis_from_tdms(INorOUT, datarange, data_SA, data_SB, data_PD, subplot, title, showplot):
    parameter_file = utils.resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    sampling_frequency = config.getfloat('OPS processing parameters', 'sampling_frequency')

    print(sampling_frequency)

    if INorOUT is 'IN':
        StartTime = datarange[0]
        EndTime = datarange[1]
        IndexStart = int(sampling_frequency * datarange[0])
        IndexStop = int(sampling_frequency * datarange[1])
        colors = ['#ece7f2', '#2b8cbe', '#2D3A40']
        IN = True

    elif INorOUT is 'OUT':
        StartTime = datarange[2]
        EndTime = datarange[3]
        IndexStart = int(sampling_frequency * datarange[2])
        IndexStop = int(sampling_frequency * datarange[3])
        colors = ['#ffeda0', '#f03b20', '#2D3A40']
        IN = False

    data_SA = data_SA[IndexStart:IndexStop]
    data_PD = data_PD[IndexStart:IndexStop]

    Data_SA = ops.process_position(data_SA, parameter_file, 0, showplot)
    Data_SB = ops.process_position(data_SB, parameter_file, 0, False)
    Data_SB_R = utils.resample(Data_SB, Data_SA)
    time_SA = Data_SA[0]
    time_SB = Data_SB[0]
    offset = 100

    eccentricity = np.subtract(Data_SA[1], Data_SB_R[1]) / 2
    #
    data_SA = utils.butter_lowpass_filter(data_SA, 1e6, 20e6, order=6)
    data_PD = utils.butter_lowpass_filter(data_PD, 1e6, 20e6, order=6)

    #    plt.subplot(subplot[0], subplot[1], subplot[2])
    plt.figure()
    plt.subplot(2, 2, 1)
    plt.plot(StartTime + np.arange(0, data_SA.size, 5) / sampling_frequency,
             data_SA[0::5] / np.amax(data_SA[0::5]) * np.amax(Data_SA[1]))
    plt.plot(StartTime + Data_SA[0], Data_SA[1])
    plt.plot(StartTime + np.arange(0, data_SA.size, 10) / sampling_frequency,
             data_PD[0::10] / np.amax(data_PD[0::10]) * np.amax(Data_SA[1]))
    plt.xlabel('Time')
    plt.ylabel('Angular Position')
    plt.xlim = [StartTime, EndTime]
    plt.title(title)

    plt.subplot(2, 2, 2)
    plt.plot(Data_SA[0] * 1e3, eccentricity)
    plt.title(title)

    plt.subplot(2, 2, 3)
    distances_A = np.diff(time_SA)[offset:time_SA.size - 1 - offset]
    rel_distances_A = np.divide(distances_A[1::], distances_A[0:distances_A.size - 1])
    plt.plot(1e3 * time_SA[offset:time_SA.size - 2 - offset], rel_distances_A, '.', color=prairie.use_colors('cold', 0))

    plt.show(block=False)

    _occ = StartTime + ops.find_occlusions(data_PD, IN, diagnostic_plot=False) / sampling_frequency
    occ = np.mean(_occ)
    p = utils.resample(Data_SA, np.array([[occ], [0]]))
    p = p[1]

    return _occ


def make_one_plot_analysis_from_tdms_2(INorOUT, datarange, data_SA, data_SB, data_PD, subplot, title, showplot, arange):

    parameter_file = utils.resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    range_55rs = eval(config.get('OPS processing parameters', 'range_55rs'))
    range_133rs = eval(config.get('OPS processing parameters', 'range_133rs'))
    sampling_frequency = eval(config.get('OPS processing parameters', 'sampling_frequency'))

    if INorOUT is 'IN':
        print('------- OPS Processing IN -------')
        Index_for_StartTime = 0
        StartTime = 0
        EndTime = 0.08
        IN = True
    elif INorOUT is 'OUT':
        Index_for_StartTime = 2
        StartTime = 0.380
        EndTime = 0.460
        print('------- OPS Processing OUT -------')
        IN = False

    # ==========================================================================
    # Raw data file names extraction
    # ==========================================================================


    _data_SA = data_SA
    _data_SB = data_SB
    _data_PD = data_PD
    offset = 100

    Data_SA = ops.process_position(_data_SA, utils.resource_path('data/parameters.cfg'), StartTime, showplot)
    Data_SB = ops.process_position(_data_SB, utils.resource_path('data/parameters.cfg'), StartTime, showplot)

    Data_SB_R = utils.resample(Data_SB, Data_SA)

    # Eccentricity from OPS processing and saving in list
    _eccentricity = np.subtract(Data_SA[1], Data_SB_R[1]) / 2

    Data_SA[1] = np.subtract(Data_SA[1], _eccentricity)
    Data_SB_R[1] = np.add(Data_SB_R[1], _eccentricity)

    time_SA = Data_SA[0]
    time_SB = Data_SB[0]

    # Finding of occlusions and saving into a list
    _time_PD = StartTime + np.arange(0, _data_PD.size) * 1 / sampling_frequency
    occlusions = ops.find_occlusions(_data_PD, IN, True, StartTime)

    Data_SA_R = utils.resample(Data_SA, np.array([_time_PD, _data_PD]))
    occ1 = Data_SA_R[1][int(occlusions[0])]
    occ2 = Data_SA_R[1][int(occlusions[1])]
    _occlusion = (occ2 - occ1) / 2 + occ1

    print(_time_PD[int(np.mean(occlusions))])
    print(Data_SA_R[0][int(np.mean(occlusions))])
    print(Data_SA_R[1][int(np.mean(occlusions))])

    prairie.use()()()

    plt.figure()
    plt.subplot(2, 2, 1)
    plt.plot(StartTime + np.arange(0, data_SA.size, 5) / sampling_frequency,
             data_SA[0::5] / np.amax(data_SA[0::5]) * np.amax(Data_SA[1]))
    plt.plot(Data_SA[0], Data_SA[1])
    plt.plot(StartTime + np.arange(0, data_SA.size, 10) / sampling_frequency,
             data_PD[0::10] / np.amax(data_PD[0::10]) * np.amax(Data_SA[1]))
    plt.xlabel('Time')
    plt.ylabel('Angular Position')
    plt.xlim = [StartTime, EndTime]
    plt.title(title)

    plt.subplot(2, 2, 2)
    plt.plot(Data_SA[0] * 1e3, _eccentricity)
    plt.title(title)

    plt.subplot(2, 2, 3)
    distances_A = np.diff(time_SA)[offset:time_SA.size - 1 - offset]
    rel_distances_A = np.divide(distances_A[1::], distances_A[0:distances_A.size - 1])
    plt.plot(1e3 * time_SA[offset:time_SA.size - 2 - offset], rel_distances_A, '.', color=prairie.use_colors('cold', 0))

    plt.show(block=False)

    return _occlusion


def plot_analysis_from_tdms(file, showplot=False):
    """
      Analysis of a single tdms file for the data acquired during the second calibration campaign (After the
      LabView program modification concerning the time windows of INs and OUTs)

      Args:
          file: tdms file to analyse
          showplot: show OPS processing plots

      Returns
          Values of crossing position
      """
    
    file = utils.reformate_path(file)

    tdms_file = TdmsFile(file)
    data__s_a = tdms_file.object('Picoscope Data', 'DISC PHOTODIODE HOME').data
    data__s_b = tdms_file.object('Picoscope Data', 'DISC PHOTODIODE IN').data
    data__p_d = np.abs(-tdms_file.object('Picoscope Data', 'WIRE PHOTODIODE').data)

    parameter_file = utils.resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    range_55rs = eval(config.get('OPS processing parameters', 'range_55rs'))
    range_133rs = eval(config.get('OPS processing parameters', 'range_133rs'))

    if file.find('55rs') != -1:
        datarange = range_55rs
    elif file.find('133rs') != -1:
        datarange = range_133rs

    a1 = make_one_plot_analysis_from_tdms('IN', datarange, data__s_a, data__s_b, data__p_d, [2, 2, 1], 'OPSA_IN', showplot)
    a2 = make_one_plot_analysis_from_tdms('OUT', datarange, data__s_a, data__s_b, data__p_d, [2, 2, 2], 'OPSA_OUT', showplot)
    a3 = make_one_plot_analysis_from_tdms('IN', datarange, data__s_b, data__s_b, data__p_d, [2, 2, 3], 'OPSB_IN', showplot)
    a4 = make_one_plot_analysis_from_tdms('OUT', datarange, data__s_b, data__s_b, data__p_d, [2, 2, 4], 'OPSB_OUT', showplot)

    return [a1, a2, a3, a4]


def plot_analysis_from_tdms_2(file, show_plot=False):
    """
    Analysis of a single tdms file for the data acquired during the second calibration campaign (After the
    LabView program modification concerning the time windows of INs and OUTs)

    Args:
        file: tdms file to analyse
        show_plot: show OPS processing plots

    Returns
        Values of crossing position
    """

    file = utils.reformate_path(file)

    parameter_file = utils.resource_path('data/parameters.cfg')
    config = configparser.RawConfigParser()
    config.read(parameter_file)
    #range_55rs = eval(config.get('OPS processing parameters', 'range_55rs'))
    #range_133rs = eval(config.get('OPS processing parameters', 'range_133rs'))
    sampling_frequency = eval(config.get('OPS processing parameters', 'sampling_frequency'))
    start_time_out = int(sampling_frequency * 0.020)
    print(start_time_out)

    tdms_file = TdmsFile(file)
    data__s_a__in = tdms_file.object('Picoscope Data', 'DISC PH. HOME dir IN').data
    data__s_b__in = tdms_file.object('Picoscope Data', 'DISC PH. IN dir IN').data
    data__p_d__in = np.abs(-tdms_file.object('Picoscope Data', 'WIRE PH. dir IN').data)
    data__s_a__out = tdms_file.object('Picoscope Data', 'DISC PH. HOME dir HOME').data[start_time_out::]
    data__s_b__out = tdms_file.object('Picoscope Data', 'DISC PH. IN dir HOME').data[start_time_out::]
    data__p_d__out = np.abs(-tdms_file.object('Picoscope Data', 'WIRE PH. dir HOME').data)[start_time_out::]

    if file.find('55rs') != -1:
        data_range = range_55rs
    elif file.find('133rs') != -1:
        data_range = range_133rs

    data_range = np.asarray(data_range)

    a1 = make_one_plot_analysis_from_tdms_2('IN', data_range, data__s_a__in, data__s_b__in, data__p_d__in, [2, 2, 1], 'OPSA_IN',
                                            show_plot, data_range[0:2] / sampling_frequency)
    a2 = make_one_plot_analysis_from_tdms_2('OUT', data_range, data__s_a__out, data__s_b__out, data__p_d__out, [2, 2, 2],
                                            'OPSA_OUT', show_plot, data_range[2:4] / sampling_frequency)
    a3 = make_one_plot_analysis_from_tdms_2('IN', data_range, data__s_b__in, data__s_b__in, data__p_d__in, [2, 2, 3], 'OPSB_IN',
                                            show_plot, data_range[0:2] / sampling_frequency)
    a4 = make_one_plot_analysis_from_tdms_2('OUT', data_range, data__s_b__out, data__s_b__out, data__p_d__out, [2, 2, 4],
                                            'OPSB_OUT', show_plot, data_range[2:4] / sampling_frequency)

    return [a1, a2, a3, a4]


def plot_fatigue_monitoring(folders):
    blue = '#3C5D9D'
    orange = '#FA7D30'

    labels = []
    dates = []
    a = []
    b = []
    c = []
    colors = []
    sigma_IN = []
    center_IN = []
    sigma_OUT = []
    center_OUT = []
    size = (8, 2.5)

    day_max=16

    for folder in folders:

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
        data = sio.loadmat(folder + '/' + 'calibration_results.mat', struct_as_record=False, squeeze_me=True)
        p = data['f_parameters_IN']
        dates.append(2 * date)
        a.append(p[0])
        b.append(p[1])
        c.append(p[2])
        acolor = np.zeros(3)
        acolor[1] = (day_max - color) / day_max
        acolor[2] = 0.75
        acolor[0] = 0.2
        colors.append(acolor)
        sigma_IN.append(data['sigma_IN'])
        center_IN.append(data['center_IN'])
        sigma_OUT.append(data['sigma_OUT'])
        center_OUT.append(data['center_OUT'])

    prairie.use()

    center_IN = np.asarray(center_IN)
    center_OUT = np.asarray(center_OUT)

    fig, ax1 = plt.subplots(figsize=size)
    ax1.plot(dates, sigma_IN, '.', color=blue)
    ax1.set_xlabel('Date')
    # Make the y-axis label, ticks and tick labels match the line color.
    ax1.set_ylabel('um', color=blue)
    ax1.tick_params('y', colors=blue)
    prairie.style(ax1)
    plt.xticks(dates, labels, rotation=30)
    plt.ylim([6, 15])
    plt.title('Fatigue test monitoring of June 2017 (IN) - Angular position error sigma')

    # ax2 = ax1.twinx()
    # s2 = np.array([600, 4900, 5200, 10000, 10300, 14600, 14900, 20400, 20700, 25500]) + 8500
    # ax2.plot(t, s2, color=orange, alpha=0.3)
    # ax2.set_ylabel('Number of scans', color=orange)
    # ax2.tick_params('y', colors=orange)

    fig.tight_layout()
    plt.show(block=False)

    plt.savefig('../figures/Fatigue test monitoring of June 2017 - Angular position error sigma',
                format='png', dpi=DPI)

    fig, ax1 = plt.subplots(figsize=size)
    ax1.plot(dates, center_IN - center_IN[0], '.', color=blue)
    ax1.set_xlabel('Date')
    # Make the y-axis label, ticks and tick labels match the line color.
    ax1.set_ylabel('um', color=blue)
    ax1.tick_params('y', colors=blue)
    prairie.style(ax1)
    plt.xticks(dates, labels, rotation=30)
    plt.ylim([-10, 30])
    plt.title('Fatigue test monitoring of June 2017 (IN) - Relative position of the center')

    # ax2 = ax1.twinx()
    # s2 = np.array([600, 4900, 5200, 10000, 10300, 14600, 14900, 20400, 20700, 25500]) + 8500
    # ax2.plot(t, s2, color=orange, alpha=0.3)
    # ax2.set_ylabel('Number of scans', color=orange)
    # ax2.tick_params('y', colors=orange)

    fig.tight_layout()
    plt.show(block=False)

    plt.savefig('../figures/Fatigue test monitoring of June 2017 (IN) - Relative position of the center',
                format='png', dpi=DPI)

    fig, ax1 = plt.subplots(figsize=size)
    ax1.plot(dates, sigma_OUT, '.', color=blue)
    ax1.set_xlabel('Date')
    # Make the y-axis label, ticks and tick labels match the lOUTe color.
    ax1.set_ylabel('um', color=blue)
    ax1.tick_params('y', colors=blue)
    prairie.style(ax1)
    plt.xticks(dates, labels, rotation=30)
    plt.ylim([6, 15])
    plt.title('Fatigue test monitoring of June 2017 (OUT) - Angular position error sigma')

    # ax2 = ax1.twOUTx()
    # s2 = np.array([600, 4900, 5200, 10000, 10300, 14600, 14900, 20400, 20700, 25500]) + 8500
    # ax2.plot(t, s2, color=orange, alpha=0.3)
    # ax2.set_ylabel('Number of scans', color=orange)
    # ax2.tick_params('y', colors=orange)

    fig.tight_layout()
    plt.show(block=False)

    plt.savefig('../figures/Fatigue test monitoring of June 2017 (OUT) - Angular position error sigma.png',
                format='png', dpi=DPI)

    fig, ax1 = plt.subplots(figsize=size)
    ax1.plot(dates, center_OUT, '.', color=blue)
    ax1.set_xlabel('Date')
    # Make the y-axis label, ticks and tick labels match the lOUTe color.
    ax1.set_ylabel('um', color=blue)
    ax1.tick_params('y', colors=blue)
    prairie.style(ax1)
    plt.xticks(dates, labels, rotation=30)
    plt.ylim([-10, 30])
    plt.title('Fatigue test monitorOUTg of June 2017 (OUT) - Relative position of the center')

    # ax2 = ax1.twOUTx()
    # s2 = np.array([600, 4900, 5200, 10000, 10300, 14600, 14900, 20400, 20700, 25500]) + 8500
    # ax2.plot(t, s2, color=orange, alpha=0.3)
    # ax2.set_ylabel('Number of scans', color=orange)
    # ax2.tick_params('y', colors=orange)

    fig.tight_layout()
    plt.show(block=False)

    plt.savefig('../figures/Fatigue test monitorOUTg of June 2017 (OUT) - Relative position of the center.png',
                format='png', dpi=DPI)


# Multiple calibration analysis  ---------------------------------------------------------------------


def plot_superposed_theoretical_curve(folders, in_or_out, save=False, saving_name=None):
    """
    Plot the superposition of several calibration fitted curves

    Args:
        folders: list of PROCESSED data folders
        save: save the figure as png (figure will not be displayed if True)

    """
    day_max = 20

    fig = plt.figure(figsize=(9, 5))
    prairie.use()

    f = []
    legend = []
    residuals = []
    rms_list = []
    plot_colors = []

    ops.mean_fit_parameters(folders)

    portion = np.arange(0.65, 1.65, 0.01)
    mean_fit_file = sio.loadmat('../data/mean_fit.mat', struct_as_record=False, squeeze_me=True)

    if in_or_out is 'IN':
        a = mean_fit_file['a_IN']
        b = mean_fit_file['b_IN']
        c = mean_fit_file['c_IN']
    elif in_or_out is 'OUT':
        a = mean_fit_file['a_OUT']
        b = mean_fit_file['b_OUT']
        c = mean_fit_file['c_OUT']

    f0 = utils.theoretical_laser_position(portion, a, b, c)

    ax = plt.subplot2grid((2, 2), (0, 0), rowspan=2)

    for folder in folders:

        data = sio.loadmat(folder + '/' + 'calibration_results.mat', struct_as_record=False, squeeze_me=True)

        if in_or_out is 'IN':
            p = data['f_parameters_IN']
        elif in_or_out is 'OUT':
            p = data['f_parameters_OUT']

        plot_legend = folder.split('/')[::-1][0].split('__')[1].split('_')[1] + '/' + \
                      folder.split('/')[::-1][0].split('__')[1].split('_')[2]

        color = int(folder.split('/')[::-1][0].split('__')[1].split('_')[2])

        if int(folder.split('/')[::-1][0].split('__')[2].split('_')[0]) <= 12:
            plot_legend += ' a.m.'
        else:
            plot_legend += ' p.m.'
            color += 0.5

        theoretical_laser_position = utils.theoretical_laser_position(portion, p[0], p[1], p[2])

        RMS = 1e3 * sqrt(mean_squared_error(theoretical_laser_position, f0))
        residuals.append(1e3 * (theoretical_laser_position - f0))
        legend.append(plot_legend + ': ' + "{:.1f}".format(RMS))
        rms_list.append(RMS)

        plot_color = np.zeros(3)
        plot_color[1] = (day_max - color) / day_max
        plot_color[2] = 0.75
        plot_color[0] = 0.2
        plot_colors.append(plot_color)
        ax.plot(portion, theoretical_laser_position, color=plot_color)
        # plt.text(1 + u * 1e-9, utils.theoretical_laser_position(1, p[0], p[1], p[2]) + 0.0001, plot_legend, fontsize=8, color=acolor)

    _legend = plt.legend(legend, title='Relative difference' + '(\u03BCm)')
    plt.setp(_legend.get_title(), fontsize=8)
    ax.set_xlabel('Angular wire position (rad)')
    ax.set_ylabel('Laser Position (mm)')
    ax.set_title('Mechanical equation of the scanner over calibrations' + ' ' + in_or_out, fontsize=9, weight='bold', family='Arial',
              loc='left')
    prairie.style(ax)

    ax2 = plt.subplot2grid((2, 2), (0, 1))
    for d, color in zip(residuals, plot_colors):
        ax2.plot(portion, d, color=color)
    ax2.set_ylim([-150, 150])
    ax2.set_ylabel('RMS error (\u03BCm)')
    ax2.set_xlabel('Angular wire position (rad)')
    plt.title('Mechanical equation residuals (w.r.t the mean curve)', loc='left')
    prairie.style(ax2)

    ax3 = plt.subplot2grid((2, 2), (1, 1))
    make_histogram(rms_list, [-100, 100], '\u03BCm')
    prairie.style(ax3)
    ax3.set_xlabel('RMS error (\u03BCm)')
    ax3.set_ylabel('Normalized occurence')
    plt.title('histogram of rms error', loc='left')

    plt.tight_layout()

    if save is True:
        plt.show(block=False)
        if saving_name is not None:
            plt.savefig(saving_name + '.png', format='png', dpi=DPI)
        else:
            print('saving_name is None - Figure not saved')
    else:
        plt.show(block=True)


def plot_multiple_calibrations_analysis(folders, in_or_out='IN', save=False, saving_name=None):

    fig = plt.figure(figsize=(10, 4))
    prairie.use()
    day_max = 25

    legends = []

    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = fig.add_subplot(2, 1, 2)
    labels = []
    dates = []
    colors = []
    mu = []
    ranges_0 = []
    ranges_1 = []

    for folder in folders:

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

            if in_or_out is 'IN':

                residuals = np.asarray(data['residuals_IN_origin'])
                range_0 = 1e3 * (np.mean(residuals) - 4 * np.std(residuals))
                ranges_0.append(range_0)
                range_1 = 1e3 * (np.mean(residuals) + 4 * np.std(residuals))
                ranges_1.append(range_1)

                ax1.plot(data['laser_position_IN'], 1e3 * data['residuals_IN_origin'], '.', color=acolor)
                m = make_histogram(1e3 * data['residuals_IN_origin'], [range_0, range_1], 'um', axe=ax2,
                                      color=acolor)

            elif in_or_out is 'OUT':

                residuals = np.asarray(data['residuals_OUT_origin'])
                range_0 = 1e3 * (np.mean(residuals) - 4 * np.std(residuals))
                ranges_0.append(range_0)
                range_1 = 1e3 * (np.mean(residuals) + 4 * np.std(residuals))
                ranges_1.append(range_1)

                ax1.plot(data['laser_position_OUT'], 1e3 * data['residuals_OUT_origin'], '.', color=acolor)
                m = make_histogram(1e3 * data['residuals_OUT_origin'], [range_0, range_1], 'um', axe=ax2,
                                      color=acolor)
            mu.append(m)

    if len(ranges_0) > 0:
        ax1.set_ylim([np.min(np.asarray(ranges_0)), np.max(np.asarray(ranges_1))])
        ax2.set_xlim([np.min(np.asarray(ranges_0)), np.max(np.asarray(ranges_1))])
    else:
        ax1.set_ylim([-100, 100])

    ax1.set_xlim([-60, 60])

    if len(folders) > 1:

        texts = ax2.get_legend().get_texts()
        for text in texts:
            legends.append(text._text)

        legends = np.asarray([label + '  ' + legend for label, legend in zip(labels, legends)])

        ax2.legend(legends, bbox_to_anchor=(1.05, 2.5), loc=2, borderpad=1)

        prairie.style(ax1)
        prairie.style(ax2)

        if in_or_out is 'IN':
            title = 'Wire position error overs scans - IN'
        else:
            title = 'Wire position error overs scans - OUT'

        ax1.set_title(title, loc='left')
        ax1.set_ylabel('Error (\u03BCm)')
        ax1.set_xlabel('Laser position (mm)')
        ax2.set_title('Wire position error histogram', loc='left')
        ax2.set_ylabel('Occurence')
        ax2.set_xlabel('Error (\u03BCm)')

        prairie.style(ax1)
        prairie.style(ax2)

        fig.tight_layout()
        fig.subplots_adjust(right=0.7)

        if save is True:
            plt.show(block=False)

            if saving_name is not None:
                plt.savefig(saving_name + '.png', format='png', dpi=DPI)
            else:
                print('saving_name is None - Figure not saved')
        else:
            plt.show(block=True)


def plot_global_residuals(folders, save=False, saving_name=None):

    legends = []

    fig = plt.figure(figsize=(8, 3))
    prairie.use()
    ax1 = plt.subplot2grid((1, 2), (0, 0))
    # ax2 = plt.subplot2grid((2, 2), (1, 0))
    ax3 = plt.subplot2grid((1, 2), (0, 1))
    # ax4 = plt.subplot2grid((2, 2), (1, 1))
    labels = []
    dates = []
    colors = []
    residuals_IN = np.empty((1))
    residuals_OUT = np.empty((1))
    laser_position_IN =  np.empty((1))
    laser_position_OUT = np.empty((1))
    mu = []
    sigma =[]

    day_max= len(folders)


    for folder in folders:

        color = int(folder.split('/')[::-1][0].split('__')[1].split('_')[2])

        if int(folder.split('/')[::-1][0].split('__')[2].split('_')[0]) >= 12:
            color += 0.5

        # acolor = np.zeros(3)
        # acolor[1] = (day_max - color) / day_max
        # acolor[2] = 0.75
        # acolor[0] = 0.2

        data = sio.loadmat(folder + '/' + 'calibration_results.mat', struct_as_record=False, squeeze_me=True)
        residuals_IN = np.concatenate((residuals_IN, data['residuals_IN_origin']), axis=0)
        residuals_OUT = np.concatenate((residuals_OUT, data['residuals_OUT_origin']), axis=0)
        laser_position_IN = np.concatenate((laser_position_IN, data['laser_position_IN']), axis=0)
        laser_position_OUT = np.concatenate((laser_position_OUT, data['laser_position_OUT']), axis=0)

        ax1.plot(data['laser_position_IN'], 1e3 * data['residuals_IN_origin'], '.', markersize=3.5)
        ax3.plot(data['laser_position_OUT'], 1e3 * data['residuals_OUT_origin'], '.', markersize=3.5)

    laser_position_IN_mean = []
    residuals_IN_mean = []

    laser_position_OUT_mean = []
    residuals_OUT_mean = []

    for laser_position in laser_position_IN:
        residuals_IN_mean.append(np.mean(residuals_IN[np.where(laser_position_IN == laser_position)]))
        laser_position_IN_mean.append(laser_position)

    for laser_position in laser_position_OUT:
        residuals_OUT_mean.append(np.mean(residuals_OUT[np.where(laser_position_OUT == laser_position)]))
        laser_position_OUT_mean.append(laser_position)


    laser_position_IN_mean = np.asarray(laser_position_IN_mean)
    residuals_IN_mean = np.asarray(residuals_IN_mean)

    laser_position_OUT_mean = np.asarray(laser_position_OUT_mean)
    residuals_OUT_mean = np.asarray(residuals_OUT_mean)

    # in_legend = make_histogram(1e3 * residuals_IN, [-200, 200], 'um')
    # out_legend = make_histogram(1e3 * residuals_OUT, [-200, 200], 'um')
    ax1.set_ylim([-200, 200])
    ax3.set_ylim([-200, 200])

    prairie.style(ax1)
    # prairie.style(ax2)
    prairie.style(ax3)
    # prairie.style(ax4)
    plt.tight_layout()
    ax1.set_title('Wire position error overs scans - IN', loc='left')
    ax1.set_ylabel('Error (\u03BCm)')
    ax1.set_xlabel('Laser position (mm)')
    ax1.legend(['\u03C3 ' + "{:3.3f}".format(np.std(1e3 * residuals_IN) / np.sqrt(2)) + '   ' + '\u03BC ' + "{:3.3f}".format(np.mean(1e3 * residuals_IN)) + '  (\u03BCm)'])
    ax3.set_title('Wire position error overs scans - OUT', loc='left')
    ax3.set_ylabel('Error (\u03BCm)')
    ax3.set_xlabel('Laser position (mm)')
    ax3.legend(['\u03C3 ' + "{:3.3f}".format(
        np.std(1e3 * residuals_OUT) / np.sqrt(2)) + '   ' + '\u03BC ' + "{:3.3f}".format(
        np.mean(1e3 * residuals_OUT)) + '  (\u03BCm)'])
    # ax2.set_title('Wire position error histogram - IN', loc='left')
    # ax2.set_ylabel('Occurence')
    # ax2.set_xlabel('Error (\u03BCm)')
    # ax4.set_title('Wire position error histogram - OUT', loc='left')
    # ax4.set_ylabel('Occurence')
    # ax4.set_xlabel('Error (\u03BCm)')
    plt.tight_layout()

    if save is True:
        plt.show(block=False)

        if saving_name is not None:
            plt.savefig(saving_name + '.png', format='png', dpi=DPI)
        else:
            print('saving_name is None - Figure not saved')
    else:
        plt.show(block=True)


def plot_residuals_shape(folders, save=False, saving_name=None, origin=True, title=None):

    fig = plt.figure(figsize=(8, 3))
    prairie.use()
    ax = fig.add_subplot(111)

    M = []

    i = 0

    for folder in folders:
        data = sio.loadmat(folder + '/calibration_results.mat')
        residuals = data['residuals_IN_origin_mean'][0]
        laser_position = data['laser_position_IN_mean'][0]
        if i == 0:
            plt.plot(laser_position, utils.butter_lowpass_filter(residuals, 1 / 101, 1 / 10) - np.mean(residuals),
                     alpha=0.2, linewidth=2, label='Calibration residuals profiles (' + str(len(folders)) + ' - filtered and centered)')
        else:
            plt.plot(laser_position, utils.butter_lowpass_filter(residuals, 1 / 101, 1 / 10) - np.mean(residuals),
                     alpha=0.2, linewidth=2, label='_nolegend_')
        # plt.plot(laser_position, residuals - np.mean(residuals),
        #          alpha=0.2, linewidth=2, label='_nolegend_')
        M.append(residuals)
        i += 1

    M = np.asarray(M)
    M = np.mean(M, 0)

    ax.plot(laser_position, utils.butter_lowpass_filter(M, 1 / 101, 1 / 10), color='k', linewidth=2.5,
            label='Mean residual profile')
    # ax.plot(laser_position, M, color='k', linewidth=2.5,
    #         label='Mean residual profile')
    ax.set_xlabel('Laser position (mm)')
    ax.set_ylabel('Residual error (\u03BCm)')
    if title is not None:
        ax.set_title('Residuals shape of the ' + title, loc='left')
    ax.legend()
    plt.tight_layout()
    prairie.style(ax)

    if save is True:
        plt.show(block=False)

        if saving_name is not None:
            plt.savefig(saving_name + '.png', format='png', dpi=DPI)
        else:
            print('saving_name is None - Figure not saved')
    else:
        plt.show(block=True)


def plot_calibration_procedure(folders, save=False, saving_name=None, origin=True, title=None, strategy=1):

    fig = plt.figure(figsize=(8, 3))
    prairie.use()

    gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])

    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    M = []

    R = []

    final_residuals = []

    i=0

    for folder in folders:
        data = sio.loadmat(folder + '/calibration_results.mat')
        residuals = 1e3*data['residuals_IN_origin'][0]
        laser_position = data['laser_position_IN'][0]
        if i==0:
            ax1.plot(laser_position, residuals, '.', alpha=0.3, label='Residuals with the theoretical curve')
        else:
            ax1.plot(laser_position, residuals, '.', alpha=0.3, label='_nolegend_')

        M.append(1e3*data['residuals_IN_origin_mean'][0])
        i += 1

    M = np.asarray(M)
    M = np.mean(M, 0)

    if strategy == 1:
        M = np.ones(M.size)*np.mean(M)

    for folder in folders:
        data = sio.loadmat(folder + '/calibration_results.mat')
        residuals = 1e3*data['residuals_IN_origin'][0]
        laser_position = data['laser_position_IN'][0]
        laser_position_mean = data['laser_position_IN_mean'][0]
        for l in laser_position_mean:
            R.append(np.asarray(residuals[np.where(laser_position == l)] - M[np.where(l == laser_position_mean)]))

    ax1.plot(data['laser_position_IN_mean'][0], M, alpha=0.5, linewidth=5, label='Raw calibration curve')
    ax1.plot(data['laser_position_IN_mean'][0], utils.butter_lowpass_filter(M, 1 / 101, 1 / 10), color='k', linewidth=1.5, label='Final Calibration curve')
    ax1.set_xlim([-50, 50])
    ax1.set_ylim([-80, 80])
    ax1.set_title('Wire position error with regard to the theoretical curve vs. the calibration curve')

    ax1.set_xlabel('Laser position (mm)')
    ax1.set_ylabel('Position error (\u03BCm)')
    ax1.legend(loc='upper right')
    plt.tight_layout()
    prairie.style(ax1)

    for folder in folders:
        data = sio.loadmat(folder + '/calibration_results.mat')
        residuals = data['residuals_IN_origin_mean'][0]
        final_residuals.append(utils.butter_lowpass_filter(M, 1 / 101, 1 / 10)-residuals)

    final_residuals = (np.hstack(R)).flatten()

    make_histogram(final_residuals, [-120, 120], '\u03BCm', axe=ax2)

    ax2.set_title('Wire position error histogram')
    ax2.set_xlabel('Position error (\u03BCm)')
    ax2.set_ylabel('Normalized occurrence')
    prairie.style(ax2)

    if save is True:
        plt.show(block=False)

        if saving_name is not None:
            plt.savefig(saving_name + '.png', format='png', dpi=DPI)
        else:
            print('saving_name is None - Figure not saved')
    else:
        plt.show(block=True)
        
        










