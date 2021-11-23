import PyQt5
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# mpl.use('Qt5Agg')
# mpl.use('TkAgg')


# ================== Global parameters for fonts & sizes =================
font_size = 30
rc = {'font.size': font_size, 'axes.labelsize': font_size, 'legend.fontsize': font_size,
      'axes.titlesize': font_size, 'xtick.labelsize': font_size, 'ytick.labelsize': font_size}
plt.rcParams.update(**rc)
plt.rc('font', weight='bold')

# For label titles
fontdict = {'fontsize': font_size, 'fontweight': 'bold'}
# can add in above dictionary: 'verticalalignment': 'baseline'

# %% =======================================


def plot_yield(annual_yield_sat, annual_yield_mav, gcr_range, DCTotal, dc_size):
    """
        Function to plot the DC yield of 5B-MAV and SAT 1 (for difference gcr)
        Parameters
        ----------
        annual_yield_sat: dataframe
            annual yield of sat system as an array for the range of gcr

        annual_yield_mav: int
            annual yield of mav

        gcr_range: array
            range of values for the ground coverage ratio

        DCTotal: int
            Desired DC output from the system (main input)

        dc_size: int/array
            Actual DC size for the solar array (based on gcr and spacing etc.)

        Returns
        -------
        plot of the annual yield
    """

    fig, ax = plt.subplots(figsize=(25, 20))
    labels = round(gcr_range, 2)
    x = np.arange(11)
    ax.bar(x, annual_yield_sat, label='SAT')
    ax.bar(x[-1] + 1, annual_yield_mav, label='MAV')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel('Annual yield (GWh)', **fontdict)
    ax.set_xlabel('Ground coverage ratio (GCR)', **fontdict)
    ax.grid(b=True, which='major', color='gray', linestyle='-')
    ax.legend()

    ax2 = ax.twinx()
    ax2.plot(dc_size, '*-', color='red')
    ax2.set_ylabel('DC rated of the system (MW)', **fontdict)
    ax2.set_ylim(DCTotal*0.6, DCTotal*1.4)
    # dc_size.append(DCTotal)
    plt.show()


def plot_yield_per_module(annual_yield_sat, module_per_zone_num_range, num_of_zones, gcr_range):
    """
        Function to plot annual yield per module output for SAT system
        Parameters
        ----------
        annual_yield_sat: array
            annual yield for the sat array based on the gcr range

        module_per_zone_num_range: array
            range for number of modules per zone based on the gcr range

        num_of_zones: int
            number of zones

        gcr_range: array
            ground coverage ratio (gcr) range

        Returns
        -------
        plot for the yield per module
    """
    fig, ax = plt.subplots(figsize=(25, 20))
    labels = round(gcr_range, 2)
    x = np.arange(11)
    ax.bar(x, annual_yield_sat/module_per_zone_num_range/num_of_zones * 1e6, label='SAT')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel('Annual yield per module(kWh)', **fontdict)
    ax.set_xlabel('Ground coverage ratio (GCR)', **fontdict)
    ax.grid(b=True, which='major', color='gray', linestyle='-')
    ax.legend()
    # ax.set_ylabel()
    plt.show()


def plot_temp_models(annual_yield_sapm, annual_yield_pvsyst, dc_size):
    """
        Function to plot the DC yield of the array based on different temperature models
        Parameters
        ----------
        annual_yield_sapm: int
            annual yield based on Sandia national laboratory results

        annual_yield_pvsyst: int
            annual yield based on PVSyst temperature model
        Returns
        -------
        plot of the annual yield based on different temperature models
    """
    fig, ax = plt.subplots(figsize=(25, 20))
    x = np.arange(2)
    ax.bar(x, [annual_yield_sapm, annual_yield_pvsyst])
    ax.set_xticks(x)
    ax.set_xticklabels(['Sandia', 'PVSyst'], **fontdict)
    ax.set_ylabel('Annual yield (GWh)', **fontdict)
    ax.text(x[0], annual_yield_sapm + 50, str(np.round(annual_yield_sapm, 0)))
    ax.text(x[1], annual_yield_pvsyst + 50, str(np.round(annual_yield_pvsyst, 0)))
    ax.set_title('Annual yield for %d east-west calculated with different temperature models' % (dc_size/1000), **fontdict)
    plt.show()


def plot_npv(rack_per_zone_num_range_array, npv_array, gcr_range_array, npv_cost_array, npv_revenue_array):
    rack_range_plot = np.array(rack_per_zone_num_range_array).flatten()
    npv_plot = np.array(npv_array).flatten()
    npv_cost_plot = np.array(npv_cost_array).flatten()
    npv_revenue_plot = np.array(npv_revenue_array).flatten()
    gcr_plot = np.array(gcr_range_array).flatten()

    size = 100
    fig, ax = plt.subplots(1, 3, figsize=(30, 20))
    # fig.tight_layout()
    ax[0].scatter(rack_range_plot, npv_plot / 1e6, s=size, color='C1')
    ax[0].set_ylabel('NPV ($m)', **fontdict)
    ax[1].scatter(rack_range_plot, gcr_plot, s=size, color='C2')
    ax[1].set_ylabel('Ground coverage ratio (GCR)', **fontdict)
    ax[1].set_xlabel('Number of racks per zone', **fontdict)
    ax[2].scatter(rack_range_plot, npv_cost_plot / 1e6, s=size, color='C3')
    ax[2].set_ylabel('Cost & revenue ($m)', **fontdict)
    ax[2].scatter(rack_range_plot, npv_revenue_plot / 1e6, s=size, color='C4')
    fig.legend(['NPV', 'GCR', 'Cost', 'Revenue'], loc='upper right', prop={'size': 24})
    plt.show()


def plot_save(fig_name, save_path):
    """
        Function to save the plot
        Parameters
        ----------
        fig_name: str
            name for the desired figure

        save_path: str
            path for figure to be saved
        Returns
        -------
        saves the plot to the desired path location
    """
    path = save_path + fig_name
    plt.savefig(path, dpi=300, bbox_inches='tight')
    # path="C:/Users/baran/cloudstor/SunCable/Figures/"+ figname
