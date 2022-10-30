import PyQt5
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd

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
    ax.bar(x, annual_yield_sat, width=0.3, label='SAT')
    ax.bar(x + 0.3, annual_yield_mav, width=0.3, label='MAV')
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


def plot_npv(rack_per_zone_num_range_array, npv_array, gcr_range_array, npv_cost_array, npv_revenue_array,
             module_per_rack, module_rated_power, fig_title=None):
    rack_range_plot = np.array(rack_per_zone_num_range_array).flatten()
    npv_plot = np.array(npv_array).flatten()
    npv_cost_plot = np.array(npv_cost_array).flatten()
    npv_revenue_plot = np.array(npv_revenue_array).flatten()
    gcr_plot = np.array(gcr_range_array).flatten()
    rated_power_per_zone_plot = rack_range_plot * module_per_rack * module_rated_power/1e6
    size = 100
    fig, ax = plt.subplots(2, 2, figsize=(30, 20))
    # fig.tight_layout()
    ax[0, 0].scatter(rack_range_plot, npv_plot / 1e6, s=size, color='C1')
    ax[0, 0].set_ylabel('NPV ($m)', **fontdict)
    ax[0, 0].set_xlabel('Number of units per zone', **fontdict)
    ax[0, 1].scatter(rack_range_plot, gcr_plot, s=size, color='C2')
    ax[0, 1].set_ylabel('Ground coverage ratio (GCR)', **fontdict)
    ax[0, 1].set_xlabel('Number of units per zone', **fontdict)
    ax[1, 0].scatter(rack_range_plot, npv_cost_plot / 1e6, s=size, color='C3')
    ax[1, 0].scatter(rack_range_plot, npv_revenue_plot / 1e6, s=size, color='C4')
    ax[1, 0].set_xlabel('Number of units per zone', **fontdict)
    ax[1, 0].set_ylabel('Cost & revenue ($m)', **fontdict)
    ax[1, 1].scatter(rack_range_plot, rated_power_per_zone_plot, s=size, color='C5')
    ax[1, 1].set_ylabel('Rated DC power per zone (MW)', **fontdict)
    ax[1, 1].set_xlabel('Number of units per zone', **fontdict)
    fig.legend(['NPV', 'GCR', 'Cost', 'Revenue', 'Size'], loc='upper right', prop={'size': 24})
    if fig_title is not None:
        fig.suptitle(fig_title, **fontdict)
        file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../OutputFigures/', fig_title)
        plt.savefig(file_name)
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


def extract_difference_data(df, scenario1, scenario2):

    year_list = ['2024', '2026', '2028']
    for year in year_list:
        if year in scenario1:
            sc1_year = year
        else:
            pass

        if year in scenario2:
            sc2_year = year
        else:
            pass

    cost_mc1 = df['cost_mc'][sc1_year][scenario1]
    cost_mc2 = df['cost_mc'][sc2_year][scenario2]
    weather_mc1 = df['weather_mc'][sc1_year][scenario1]
    weather_mc2 = df['weather_mc'][sc2_year][scenario2]
    loss_mc1 = df['loss_mc'][sc1_year][scenario1]
    loss_mc2 = df['loss_mc'][sc2_year][scenario2]
    combined_yield_mc1 = df['combined_yield_mc'][sc1_year][scenario1]
    combined_yield_mc2 = df['combined_yield_mc'][sc2_year][scenario2]

    discounted_ghi = df['discounted_ghi']
    loss_parameters = df['loss_parameters']
    data_tables1 = df['data_tables'][sc1_year]
    data_tables2 = df['data_tables'][sc2_year]

    # First set up a dataframe with all the possible output parameters we would like - the discounted revenue and cost
    output_parameters = pd.DataFrame(index=discounted_ghi.index)


    # Get results for cost monte carlo
    cost_mc_flat1 = cost_mc1['discounted_cost_total'].rename('d_cost').to_frame()
    cost_mc_flat1 = cost_mc_flat1.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(cost_mc_flat1)

    cost_mc_flat2 = cost_mc2['discounted_cost_total'].rename('d_cost').to_frame()
    cost_mc_flat2 = cost_mc_flat2.add_prefix(scenario2 + '_')
    output_parameters = output_parameters.join(cost_mc_flat2)

    # Get results for yield only monte carlo - from loss_mc (which varies the loss parameters)
    loss_mc_flat1 = loss_mc1['npv_revenue']
    loss_mc_flat1.columns = ['d_revenue_loss']
    loss_mc_flat1 = loss_mc_flat1.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(loss_mc_flat1)

    loss_mc_flat2 = loss_mc2['npv_revenue']
    loss_mc_flat2.columns = ['d_revenue_loss']
    loss_mc_flat2 = loss_mc_flat2.add_prefix(scenario2 + '_')
    output_parameters = output_parameters.join(loss_mc_flat2)

    # Get results for weather only Monte Carlo
    weather_mc_flat1 = weather_mc1['npv_revenue']
    weather_mc_flat1.columns = ['d_revenue_weather']
    weather_mc_flat1 = weather_mc_flat1.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(weather_mc_flat1)

    weather_mc_flat2 = weather_mc2['npv_revenue']
    weather_mc_flat2.columns = ['d_revenue_weather']
    weather_mc_flat2 = weather_mc_flat2.add_prefix(scenario2 + '_')
    output_parameters = output_parameters.join(weather_mc_flat2)

    # Get results for combined_yield
    combined_yield_mc_flat1 = combined_yield_mc1['npv_revenue']
    combined_yield_mc_flat1.columns = ['d_revenue_combined']
    combined_yield_mc_flat1 = combined_yield_mc_flat1.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(combined_yield_mc_flat1)

    combined_yield_mc_flat2 = combined_yield_mc2['npv_revenue']
    combined_yield_mc_flat2.columns = ['d_revenue_combined']
    combined_yield_mc_flat2 = combined_yield_mc_flat2.add_prefix(scenario2 + '_')
    output_parameters = output_parameters.join(combined_yield_mc_flat2)

    output_parameters = output_parameters.apply(pd.to_numeric, errors='ignore')

    # Now generate a list of all input parameters
    input_parameters = pd.DataFrame(index=discounted_ghi.index)
    # Get input parameters from cost monte carlo
    cost_parameters = generate_parameters(data_tables1)
    cost_parameters_flat = cost_parameters.copy()
    cost_parameters_flat.columns = [group + ' ' + str(ID) + ' ' + var for (group, ID, var) in
                                    cost_parameters_flat.columns.values]

    input_parameters = input_parameters.join(cost_parameters_flat)

    # Grab the loss parameters for MAV and SAT
    for item in loss_parameters:
        label = item
        loss_parameters_flat = loss_parameters[item]
        loss_parameters_flat = loss_parameters_flat.add_prefix(item + '_')
        input_parameters = input_parameters.join(loss_parameters_flat)

    # Grab ghi parameters
    discounted_ghi_flat = discounted_ghi.copy()
    discounted_ghi_flat.columns = ['discounted_ghi']
    input_parameters = input_parameters.join(discounted_ghi_flat)

    input_parameters = input_parameters.apply(pd.to_numeric, errors='ignore')

    return input_parameters, output_parameters


def prep_histogram(id_list):
     year_list = ['2024', '2026', '2028']
     scenario_list = ['weather', 'loss', 'cost']

     for id in id_list:
         scenario_str = []
         for year in year_list:
             if year in id:
                 year_id = year
             else:
                 pass

         for scenario in scenario_list:
             if scenario in id:
                 scenario_str.append()


def prep_difference_graphs(scenario1, scenario2, input_paramaters, output_parameters,
                           loss_check, weather_check, cost_check,  output_metric):
    """"""

    if loss_check and weather_check:
        scenario_tag = 'combined'
    elif loss_check and not weather_check:
        scenario_tag = 'loss'
    elif not loss_check and weather_check:
        scenario_tag = 'weather'
    elif not loss_check and not weather_check:
        scenario_tag = 'cost_only'
    else:
        raise ValueError('loss and weather check values must be boolean')

    if cost_check:
        if output_metric == 'NPV':
            rev_tag1 = scenario1 + '_d_revenue_' + scenario_tag
            cost_tag1 = scenario1 + '_d_cost_' + scenario_tag
            rev_tag2 = scenario2 + '_d_revenue_' + scenario_tag
            cost_tag2 = scenario2 + '_d_cost_' + scenario_tag
            npv1 = output_parameters[rev_tag1] - output_parameters[cost_tag1]
            npv2 = output_parameters[rev_tag2] - output_parameters[cost_tag2]
            output_diff = npv1 - npv2
        elif output_metric == 'LCOE':
            rev_tag1 = scenario1 + '_d_revenue_' + scenario_tag
            cost_tag1 = scenario1 + '_d_cost_' + scenario_tag
            rev_tag2 = scenario2 + '_d_revenue_' + scenario_tag
            cost_tag2 = scenario2 + '_d_cost_' + scenario_tag
            npv1 = output_parameters[rev_tag1] - output_parameters[cost_tag1]
            npv2 = output_parameters[rev_tag2] - output_parameters[cost_tag2]
            output_diff = npv1 - npv2

else:

    label_diff = scenario1 + '_vs_' + scenario2 + output_metric


def compile_df(df, identifiers, new_tags, output_df):
    """"""

    mc_flat = df[identifiers]
    mc_flat.columns = [new_tags]
    output_df = output_df.join(mc_flat)

    return output_df