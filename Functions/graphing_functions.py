# %% Import
import random
import sys
sys.path.append( '..' )
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
import Functions.simulation_functions as func
import Functions.mc_yield_functions as mc_func
from numpy.polynomial import Polynomial
from Functions.optimising_functions import form_new_data_tables, optimise_layout
from Functions.sizing_functions import get_airtable, get_npv
from Functions.cost_functions import calculate_scenarios_iterations, create_iteration_tables, \
     generate_parameters, import_excel_data
import warnings
from Functions.mc_yield_functions import weather_sort, generate_mc_timeseries, get_yield_datatables
import _pickle as cpickle
from scipy import stats

# This suppresses a divide be zero warning message that occurs in pvlib tools.py.
warnings.filterwarnings(action='ignore',
                                message='divide by zero encountered in true_divide*')

# %% =======================================
# script here to take inputs from GUI for generating graphs and extract the relevant entries

def load_analysis_dict(projectID):
    # import data from pickle
    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)

    file_name = 'analysis_dictionary_' + projectID +'.p'
    pickle_path = os.path.join(parent_path, 'Data', 'mc_analysis', file_name)
    Analysis_dict = cpickle.load(open(pickle_path, 'rb'))

    return Analysis_dict

def calculate_variance_table(input_factors, cost_result_name, num_table=20):

    # Remove any columns that are not numeric
    filtered_factors = input_factors.select_dtypes(exclude=['object'])
    # This removes first any input factors with no variation
    filtered_factors = filtered_factors.loc[:, (filtered_factors.std() > 0)]

    correlation_table = filtered_factors.corr()

    correlation_table['variance'] = round((correlation_table[cost_result_name] **2) * 100, 0)

    correlation_table['variance'] = correlation_table['variance'].fillna(0).astype(int)

    input_factor_range = input_factors.describe(percentiles=(0.1, 0.5, 0.9)).T.loc[:, ['10%', '50%', '90%']].round(
        2)
    input_factor_range['range'] = input_factor_range['10%'].astype(str) + ' - ' + input_factor_range['90%'].astype(
        str)

    correlation_table['range'] = input_factor_range['range']

    output_table = correlation_table.sort_values(by='variance', ascending=False).loc[:, [cost_result_name, 'variance', 'range']].head(num_table)
    print(output_table)
    return output_table

def calculate_variance_contributions(input_factors, cost_result_name, savename=None):
    num_table=20
    num_graphs=10
    title=None
    short_titles=False
    xlabel=None
    ylabel=None
    show_regression=True
    show_r=True
    show_r2=False

    # Remove any columns that are not numeric
    filtered_factors = input_factors.select_dtypes(exclude=['object'])

    # This removes first any input factors with no variation
    filtered_factors = filtered_factors.loc[:, (filtered_factors.std() > 0)]

    filtered_factors.to_csv('filtered_factors.csv')
    correlation_table = filtered_factors.corr()

    correlation_table['variance'] = round(
        (correlation_table[cost_result_name] * correlation_table[cost_result_name]) * 100, 0)

    total_variance = correlation_table['variance'].sum()
    correlation_table['variance'] = correlation_table['variance'].fillna(0).astype(int)

    input_factor_range = input_factors.describe(percentiles=(0.1, 0.5, 0.9)).T.loc[:, ['10%', '50%', '90%']].round(2)
    input_factor_range['range'] = input_factor_range['10%'].astype(str) + ' - ' + input_factor_range['90%'].astype(str)

    correlation_table['range'] = input_factor_range['range']
    correlation_table['10th percentile'] = input_factor_range['10%']
    correlation_table['50th percentile'] = input_factor_range['50%']
    correlation_table['90th percentile'] = input_factor_range['90%']

    print('Total Variance sum (should be 2.0) = ', total_variance)

    print(correlation_table.sort_values(
        by='variance', ascending=False).loc[:, [cost_result_name, 'variance', 'range']].head(num_table))

    # Graph scatterplot:
    parameter_list = correlation_table.sort_values(by='variance', ascending=False).loc[:,
                     [cost_result_name, 'variance']].head(num_graphs + 1).index
    # print(parameter_list)
    parameter_description_list = zip(parameter_list, parameter_list)
    # print(parameter_description_list)

    for (parameter, label) in parameter_description_list:
        # print(parameter)
        # print(label)
        if parameter != cost_result_name:
            plt.scatter(input_factors[parameter], input_factors[cost_result_name], edgecolor='None')
            if title is None:
                if short_titles:
                    this_title = 'Correlation to ' + cost_result_name
                else:
                    this_title = 'Impact of ' + str(parameter) + ' on ' + cost_result_name
            plt.title(this_title)
            if xlabel is None:
                if short_titles:
                    this_xlabel = str(label)
                else:
                    this_xlabel = 'Input Factor: ' + str(label)
            else:
                this_xlabel = xlabel
            plt.xlabel(this_xlabel)
            if ylabel is None:
                if short_titles:
                    this_ylabel = cost_result_name
                else:
                    this_ylabel = 'Output Factor: ' + cost_result_name
            plt.ylabel(this_ylabel)

            if show_regression:
                slope, intercept, r_value, p_value, std_err = stats.linregress(input_factors[parameter],
                                                                               input_factors[cost_result_name])

                xmin, xmax = plt.xlim()
                ymin = slope * xmin + intercept
                ymax = slope * xmax + intercept

                plt.annotate('', xy=(xmin, ymin), xycoords='data', xytext=(xmax, ymax), textcoords='data',
                             arrowprops=dict(arrowstyle="-"))

                if show_r:
                    text = 'r = {0:.2f}'.format(r_value)
                if show_r2:
                    r2_value = r_value * r_value
                    text = text + '\nr$^2$ = {0:.2f}'.format(r2_value)
                plt.annotate(text, xy=(0.5, 0.5), fontsize=20, xycoords='figure fraction')

            if savename is not None:
                file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../OutputFigures/', savename + parameter)
                plt.savefig(file_name)
            plt.show()

    parameter_select = parameter_list.tolist()

    return parameter_select

def graph_scatter_1d(input_factors, cost_result_name, parameter_list, title=None, short_titles=True,
                     xlabel=None, ylabel=None, show_regression=True, show_r=False, show_r2=True, savename=None):


    parameter_description_list = zip(parameter_list, parameter_list)

    params = {'legend.fontsize': 'medium',
              'figure.figsize': (15, 10),
              'axes.labelsize': 'large',
              'axes.titlesize': 'large',
              'xtick.labelsize': 'small',
              'ytick.labelsize': 'small'}

    pylab.rcParams.update(params)

    for (parameter, label) in parameter_description_list:
        if parameter != cost_result_name:
            plt.scatter(input_factors[parameter], input_factors[cost_result_name], edgecolor='None')
            if title is None:
                if short_titles:
                    this_title = 'Correlation to ' + cost_result_name
                else:
                    this_title = 'Impact of ' + str(parameter) + ' on ' + cost_result_name
            else:
                this_title=title
            plt.title(this_title)

            if xlabel is None:
                if short_titles:
                    this_xlabel = str(label)
                else:
                    this_xlabel = 'Input Factor: ' + str(label)
            else:
                this_xlabel = xlabel
            plt.xlabel(this_xlabel)
            if ylabel is None:
                if short_titles:
                    this_ylabel = cost_result_name
                else:
                    this_ylabel = 'Output Factor: ' + cost_result_name
            else:
                this_ylabel=ylabel

            plt.ylabel(this_ylabel)

            if show_regression:
                slope, intercept, r_value, p_value, std_err = stats.linregress(input_factors[parameter],
                                                                               input_factors[cost_result_name])

                xmin, xmax = plt.xlim()
                ymin = slope * xmin + intercept
                ymax = slope * xmax + intercept

                plt.annotate('', xy=(xmin, ymin), xycoords='data', xytext=(xmax, ymax), textcoords='data',
                             arrowprops=dict(arrowstyle="-"))
                text = ''
                if show_r:
                    text = 'r = {0:.2f}'.format(r_value)
                if show_r2:
                    r2_value = r_value * r_value
                    text = text + '\nr$^2$ = {0:.2f}'.format(r2_value)
                plt.annotate(text, xy=(0.5, 0.5), fontsize=20, xycoords='figure fraction')
                plt.plot([xmin, xmax], [ymin, ymax], 'red', linestyle='--')

            if savename is not None:
                file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../OutputFigures/',
                                         savename + parameter)
                plt.savefig(file_name)

            plt.show()

def calculate_graph_variance_contributions(input_factors, cost_result_name, savename=None, num_table = 20, num_graphs=0):
    title = None
    short_titles = False
    xlabel = None
    ylabel = None
    show_regression = True
    show_r = True
    show_r2 = False

    output_table = calculate_variance_table(input_factors, cost_result_name, num_table=num_table)

    parameter_list = output_table.head(num_table+1).index
    graph_scatter_1d(input_factors, cost_result_name, parameter_list = parameter_list)


def graph_variance_contributions(output_parameters, input_parameters, scenario_name, cost_mc =True , revenue_type = 'loss'):
    df = output_parameters.copy()

    if (revenue_type == 'loss') or (revenue_type == 'weather') or (revenue_type == 'combined'):
        revenue_column = scenario_name + '_d_revenue_' + revenue_type

    elif revenue_type == 'fixed':
        revenue_column = scenario_name + '_d_revenue_' + revenue_type
        df[revenue_column] = df[scenario_name + '_d_revenue_loss'][0]
    else:
        print('Error! Revenue type does not exist!')

    cost_column = scenario_name + '_d_cost'
    if cost_mc == True:
        cost_column = scenario_name + '_d_cost'
    else:
        cost_column = scenario_name + '_d_cost_fixed'
        df[cost_column] = df[scenario_name + '_d_cost'][0]

    output_name = scenario_name + '_NPV'
    df[output_name] = df[cost_column] / df[revenue_column]

    all_parameters = input_parameters.join(df[output_name])

    calculate_graph_variance_contributions(all_parameters, output_name,
                                     savename=None)

def graph_scatter_2d(input_data, parameter_x, parameter_y, parameter_z,
               title=None, xlabel=None, ylabel=None, zlabel=None):
    x = input_data[parameter_x]
    y = input_data[parameter_y]
    z = input_data[parameter_z]

    params = {'legend.fontsize': 'medium',
              'figure.figsize': (15, 10),
              'axes.labelsize': 'small',
              'axes.titlesize': 'medium',
              'xtick.labelsize': 'small',
              'ytick.labelsize': 'small'}

    pylab.rcParams.update(params)

    fig, (ax0, ax1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [25, 1]})

    scatterplot = ax0.scatter(x, y, c=z, cmap=None, s=None)
    plt.colorbar(scatterplot, cax=ax1)

    if title is not None:
        ax0.set_title(title)

    if xlabel is not None:
        ax0.set_xlabel(xlabel)
    else:
        ax0.set_xlabel(parameter_x)
    if ylabel is not None:
        ax0.set_ylabel(ylabel)
    else:
        ax0.set_ylabel(parameter_y)
    if zlabel is not None:
        ax1.set_title(zlabel)

    ax0.tick_params(axis='both', which='major', labelsize=14)
    ax0.tick_params(axis='both', which='minor', labelsize=12)
    ax1.tick_params(axis='both', which='major', labelsize=18)
    ax1.tick_params(axis='both', which='minor', labelsize=16)

    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)
    file_name = os.path.join(parent_path, 'OutputFigures', title)
    plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
    plt.close()

def graph_histogram(input_data, scenario_list, title=None, xlabel=None):
    data = input_data

    # Set general font size
    params = {'legend.fontsize': 'small',
              'figure.figsize': (15, 10),
              'axes.labelsize': 'medium',
              'axes.titlesize': 'medium',
              'xtick.labelsize': 'small',
              'ytick.labelsize': 'small'}

    pylab.rcParams.update(params)

    fig, ax = plt.subplots(figsize=(1,1))

    print(data)
    data.plot.hist(bins=50, histtype='step', fontsize=10)
    if title is None:
        title = 'Histogram'
    plt.title(title)

    if xlabel is not None:
        plt.xlabel(xlabel)

    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)
    file_name = os.path.join(parent_path, 'OutputFigures', title)
    plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
    plt.close()

def graph_stacked(cost_data, scenario_list, title=None):
    scenario_costs_iter = cost_data[cost_data['ScenarioID'].isin(scenario_list)]
    scenario_costs_nominal = scenario_costs_iter[scenario_costs_iter['Iteration'] == 0]


    scenario_costs_total_category = pd.pivot_table(scenario_costs_nominal, values='TotalCostAUDY',
                                                   index=['ScenarioID'], aggfunc=np.sum,
                                                   columns=['CostCategory_ShortName'])
    if title is None:
        title = 'Cost by Category'
    scenario_costs_total_category.plot.bar(stacked=True, title= title)
    plt.close()

def extract_parameter_data(df, scenario1):
    """"""

    cost_mc = df[scenario1]['cost_mc']
    weather_mc = df[scenario1]['weather_mc']
    loss_mc = df[scenario1]['loss_mc']
    combined_yield_mc = df[scenario1]['combined_yield_mc']

    discounted_ghi = df['discounted_ghi']
    loss_parameters = df['loss_parameters']
    data_tables = df['data_tables']

    # First set up a dataframe with all the possible output parameters we would like - the discounted revenue and cost
    output_parameters = pd.DataFrame(index=discounted_ghi.index)

    # Get results for cost monte carlo
    cost_mc_flat = cost_mc['discounted_cost_total'].rename('d_cost').to_frame()
    cost_mc_flat = cost_mc_flat.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(cost_mc_flat)

    # Get results for yield only monte carlo - from loss_mc (which varies the loss parameters)
    loss_mc_flat = loss_mc['npv_revenue']
    loss_mc_flat.columns = ['d_revenue_loss']
    loss_mc_flat = loss_mc_flat.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(loss_mc_flat)

    loss_mc_flat2 = loss_mc['kWh_total_discounted']
    loss_mc_flat2.columns = ['d_kWh_loss']
    loss_mc_flat2 = loss_mc_flat2.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(loss_mc_flat2)

    # Get results for weather only Monte Carlo
    weather_mc_flat = weather_mc['npv_revenue']
    weather_mc_flat.columns = ['d_revenue_weather']
    weather_mc_flat = weather_mc_flat.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(weather_mc_flat)

    weather_mc_flat2 = weather_mc['kWh_total_discounted']
    weather_mc_flat2.columns = ['d_kWh_weather']
    weather_mc_flat2 = weather_mc_flat2.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(weather_mc_flat2)

    # Get results for combined_yield
    combined_yield_mc_flat = combined_yield_mc['npv_revenue']
    combined_yield_mc_flat.columns = ['d_revenue_combined']
    combined_yield_mc_flat = combined_yield_mc_flat.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(combined_yield_mc_flat)

    combined_mc_flat2 = combined_yield_mc['kWh_total_discounted']
    combined_mc_flat2.columns = ['d_kWh_combined']
    combined_mc_flat2 = combined_mc_flat2.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(combined_mc_flat2)

    output_parameters = output_parameters.apply(pd.to_numeric, errors='ignore')

    # Now generate a list of all input parameters
    input_parameters = pd.DataFrame(index=discounted_ghi.index)
    # Get input parameters from cost monte carlo
    cost_parameters = generate_parameters(data_tables)
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

    # Grab gdi parameters
    discounted_ghi_flat = discounted_ghi.copy()
    discounted_ghi_flat.columns = ['discounted_ghi']
    input_parameters = input_parameters.join(discounted_ghi_flat)

    input_parameters = input_parameters.apply(pd.to_numeric, errors='ignore')
    return input_parameters, output_parameters

def extract_schedule_parameters(df, schedule1, ID1):
    """"""

    cost_mc = schedule1['cost_mc']
    weather_mc = schedule1['weather_mc']
    loss_mc = schedule1['loss_mc']
    combined_yield_mc = schedule1['combined_yield_mc']

    discounted_ghi = df['discounted_ghi']
    loss_parameters = df['loss_parameters']
    data_tables = df['data_tables']

    # First set up a dataframe with all the possible output parameters we would like - the discounted revenue and cost
    output_parameters = pd.DataFrame(index=discounted_ghi.index)

    # Get results for cost monte carlo
    cost_mc_flat = cost_mc['discounted_cost_total'].rename('d_cost').to_frame()
    cost_mc_flat = cost_mc_flat.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(cost_mc_flat)

    # Get results for yield only monte carlo - from loss_mc (which varies the loss parameters)
    loss_mc_flat = loss_mc['npv_revenue']
    loss_mc_flat.columns = ['d_revenue_loss']
    loss_mc_flat = loss_mc_flat.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(loss_mc_flat)

    loss_mc_flat2 = loss_mc['kWh_total_discounted']
    loss_mc_flat2.columns = ['d_kWh_loss']
    loss_mc_flat2 = loss_mc_flat2.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(loss_mc_flat2)

    # Get results for weather only Monte Carlo
    weather_mc_flat = weather_mc['npv_revenue']
    weather_mc_flat.columns = ['d_revenue_weather']
    weather_mc_flat = weather_mc_flat.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(weather_mc_flat)

    weather_mc_flat2 = weather_mc['kWh_total_discounted']
    weather_mc_flat2.columns = ['d_kWh_weather']
    weather_mc_flat2 = weather_mc_flat2.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(weather_mc_flat2)

    # Get results for combined_yield
    combined_yield_mc_flat = combined_yield_mc['npv_revenue']
    combined_yield_mc_flat.columns = ['d_revenue_combined']
    combined_yield_mc_flat = combined_yield_mc_flat.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(combined_yield_mc_flat)

    combined_mc_flat2 = combined_yield_mc['kWh_total_discounted']
    combined_mc_flat2.columns = ['d_kWh_combined']
    combined_mc_flat2 = combined_mc_flat2.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(combined_mc_flat2)

    output_parameters = output_parameters.apply(pd.to_numeric, errors='ignore')

    # Now generate a list of all input parameters
    input_parameters = pd.DataFrame(index=discounted_ghi.index)
    # Get input parameters from cost monte carlo
    cost_parameters = generate_parameters(data_tables)
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

    # Grab gdi parameters
    discounted_ghi_flat = discounted_ghi.copy()
    discounted_ghi_flat.columns = ['discounted_ghi']
    input_parameters = input_parameters.join(discounted_ghi_flat)

    input_parameters = input_parameters.apply(pd.to_numeric, errors='ignore')
    return input_parameters, output_parameters

def extract_difference_data(df, scenario1, scenario2):

    cost_mc1 = df[scenario1]['cost_mc']
    cost_mc2 = df[scenario2]['cost_mc']
    weather_mc1 = df[scenario1]['weather_mc']
    weather_mc2 = df[scenario2]['weather_mc']
    loss_mc1 = df[scenario1]['loss_mc']
    loss_mc2 = df[scenario2]['loss_mc']
    combined_mc1 = df[scenario1]['combined_yield_mc']
    combined_mc2 = df[scenario2]['combined_yield_mc']

    discounted_ghi = df['discounted_ghi']
    loss_parameters = df['loss_parameters']
    data_tables = df['data_tables']


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

    loss_mc_flat1 = loss_mc1['kWh_total_discounted']
    loss_mc_flat1.columns = ['d_kWh_loss']
    loss_mc_flat1 = loss_mc_flat1.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(loss_mc_flat1)

    loss_mc_flat2 = loss_mc2['npv_revenue']
    loss_mc_flat2.columns = ['d_revenue_loss']
    loss_mc_flat2 = loss_mc_flat2.add_prefix(scenario2 + '_')
    output_parameters = output_parameters.join(loss_mc_flat2)

    loss_mc_flat2 = loss_mc2['kWh_total_discounted']
    loss_mc_flat2.columns = ['d_kWh_loss']
    loss_mc_flat2 = loss_mc_flat2.add_prefix(scenario2 + '_')
    output_parameters = output_parameters.join(loss_mc_flat2)

    # Get results for weather only Monte Carlo
    weather_mc_flat1 = weather_mc1['npv_revenue']
    weather_mc_flat1.columns = ['d_revenue_weather']
    weather_mc_flat1 = weather_mc_flat1.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(weather_mc_flat1)

    weather_mc_flat1 = weather_mc1['kWh_total_discounted']
    weather_mc_flat1.columns = ['d_kWh_weather']
    weather_mc_flat1 = weather_mc_flat1.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(weather_mc_flat1)

    weather_mc_flat2 = weather_mc2['npv_revenue']
    weather_mc_flat2.columns = ['d_revenue_weather']
    weather_mc_flat2 = weather_mc_flat2.add_prefix(scenario2 + '_')
    output_parameters = output_parameters.join(weather_mc_flat2)

    weather_mc_flat2 = weather_mc2['kWh_total_discounted']
    weather_mc_flat2.columns = ['d_kWh_weather']
    weather_mc_flat2 = weather_mc_flat2.add_prefix(scenario2 + '_')
    output_parameters = output_parameters.join(weather_mc_flat2)

    # Get results for combined_yield
    combined_mc_flat1 = combined_mc1['npv_revenue']
    combined_mc_flat1.columns = ['d_revenue_combined']
    combined_mc_flat1 = combined_mc_flat1.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(combined_mc_flat1)

    combined_mc_flat1 = combined_mc1['kWh_total_discounted']
    combined_mc_flat1.columns = ['d_kWh_combined']
    combined_mc_flat1 = combined_mc_flat1.add_prefix(scenario1 + '_')
    output_parameters = output_parameters.join(combined_mc_flat1)

    combined_yield_mc_flat2 = combined_mc2['npv_revenue']
    combined_yield_mc_flat2.columns = ['d_revenue_combined']
    combined_yield_mc_flat2 = combined_yield_mc_flat2.add_prefix(scenario2 + '_')
    output_parameters = output_parameters.join(combined_yield_mc_flat2)

    combined_mc_flat2 = combined_mc2['kWh_total_discounted']
    combined_mc_flat2.columns = ['d_kWh_combined']
    combined_mc_flat2 = combined_mc_flat2.add_prefix(scenario2 + '_')
    output_parameters = output_parameters.join(combined_mc_flat2)

    output_parameters = output_parameters.apply(pd.to_numeric, errors='ignore')

    # Now generate a list of all input parameters
    input_parameters = pd.DataFrame(index=discounted_ghi.index)
    # Get input parameters from cost monte carlo
    cost_parameters = generate_parameters(data_tables)
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

def extract_schedule_difference(df, results1, results2, ID1, ID2):

    cost_mc1 = results1['cost_mc']
    cost_mc2 = results2['cost_mc']
    weather_mc1 = results1['weather_mc']
    weather_mc2 = results2['weather_mc']
    loss_mc1 = results1['loss_mc']
    loss_mc2 = results2['loss_mc']
    combined_mc1 = results1['combined_yield_mc']
    combined_mc2 = results2['combined_yield_mc']

    discounted_ghi = df['discounted_ghi']
    loss_parameters = df['loss_parameters']
    data_tables = df['data_tables']


    # First set up a dataframe with all the possible output parameters we would like - the discounted revenue and cost
    output_parameters = pd.DataFrame(index=discounted_ghi.index)

    # Get results for cost monte carlo
    cost_mc_flat1 = cost_mc1['discounted_cost_total'].rename('d_cost').to_frame()
    cost_mc_flat1 = cost_mc_flat1.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(cost_mc_flat1)

    cost_mc_flat2 = cost_mc2['discounted_cost_total'].rename('d_cost').to_frame()
    cost_mc_flat2 = cost_mc_flat2.add_prefix(ID2 + '_')
    output_parameters = output_parameters.join(cost_mc_flat2)

    # Get results for yield only monte carlo - from loss_mc (which varies the loss parameters)
    loss_mc_flat1 = loss_mc1['npv_revenue']
    loss_mc_flat1.columns = ['d_revenue_loss']
    loss_mc_flat1 = loss_mc_flat1.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(loss_mc_flat1)

    loss_mc_flat1 = loss_mc1['kWh_total_discounted']
    loss_mc_flat1.columns = ['d_kWh_loss']
    loss_mc_flat1 = loss_mc_flat1.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(loss_mc_flat1)

    loss_mc_flat2 = loss_mc2['npv_revenue']
    loss_mc_flat2.columns = ['d_revenue_loss']
    loss_mc_flat2 = loss_mc_flat2.add_prefix(ID2 + '_')
    output_parameters = output_parameters.join(loss_mc_flat2)

    loss_mc_flat2 = loss_mc2['kWh_total_discounted']
    loss_mc_flat2.columns = ['d_kWh_loss']
    loss_mc_flat2 = loss_mc_flat2.add_prefix(ID2 + '_')
    output_parameters = output_parameters.join(loss_mc_flat2)

    # Get results for weather only Monte Carlo
    weather_mc_flat1 = weather_mc1['npv_revenue']
    weather_mc_flat1.columns = ['d_revenue_weather']
    weather_mc_flat1 = weather_mc_flat1.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(weather_mc_flat1)

    weather_mc_flat1 = weather_mc1['kWh_total_discounted']
    weather_mc_flat1.columns = ['d_kWh_weather']
    weather_mc_flat1 = weather_mc_flat1.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(weather_mc_flat1)

    weather_mc_flat2 = weather_mc2['npv_revenue']
    weather_mc_flat2.columns = ['d_revenue_weather']
    weather_mc_flat2 = weather_mc_flat2.add_prefix(ID2 + '_')
    output_parameters = output_parameters.join(weather_mc_flat2)

    weather_mc_flat2 = weather_mc2['kWh_total_discounted']
    weather_mc_flat2.columns = ['d_kWh_weather']
    weather_mc_flat2 = weather_mc_flat2.add_prefix(ID2 + '_')
    output_parameters = output_parameters.join(weather_mc_flat2)

    # Get results for combined_yield
    combined_mc_flat1 = combined_mc1['npv_revenue']
    combined_mc_flat1.columns = ['d_revenue_combined']
    combined_mc_flat1 = combined_mc_flat1.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(combined_mc_flat1)

    combined_mc_flat1 = combined_mc1['kWh_total_discounted']
    combined_mc_flat1.columns = ['d_kWh_combined']
    combined_mc_flat1 = combined_mc_flat1.add_prefix(ID1 + '_')
    output_parameters = output_parameters.join(combined_mc_flat1)

    combined_yield_mc_flat2 = combined_mc2['npv_revenue']
    combined_yield_mc_flat2.columns = ['d_revenue_combined']
    combined_yield_mc_flat2 = combined_yield_mc_flat2.add_prefix(ID2 + '_')
    output_parameters = output_parameters.join(combined_yield_mc_flat2)

    combined_mc_flat2 = combined_mc2['kWh_total_discounted']
    combined_mc_flat2.columns = ['d_kWh_combined']
    combined_mc_flat2 = combined_mc_flat2.add_prefix(ID2 + '_')
    output_parameters = output_parameters.join(combined_mc_flat2)

    output_parameters = output_parameters.apply(pd.to_numeric, errors='ignore')

    # Now generate a list of all input parameters
    input_parameters = pd.DataFrame(index=discounted_ghi.index)
    # Get input parameters from cost monte carlo
    cost_parameters = generate_parameters(data_tables)
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

def lcoe_fiddle(generation, cost):
    lcoe_list = []
    for i in generation.index:
        lcoe_list.append(cost[i]/generation[i])

    lcoe_df = pd.DataFrame(lcoe_list)
    lcoe_df.index = generation.index

    return lcoe_df

def prep_difference_graphs(scenario1, scenario2, input_parameters, output_parameters,
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

    cost_tag1 = scenario1 + '_d_cost'
    cost_tag2 = scenario2 + '_d_cost'
    if cost_check:
        cost1 = output_parameters[cost_tag1]
        cost2 = output_parameters[cost_tag2]
    elif not cost_check:
        cost1 = output_parameters[cost_tag1][0]
        cost2 = output_parameters[cost_tag2][0]

    if output_metric == 'NPV':
        rev_tag1 = scenario1 + '_d_revenue_' + scenario_tag
        rev_tag2 = scenario2 + '_d_revenue_' + scenario_tag
        npv1 = output_parameters[rev_tag1] - cost1
        npv2 = output_parameters[rev_tag2] - cost2
        output_diffa = npv1 - npv2
    elif output_metric == 'LCOE':
        rev_tag1 = scenario1 + '_d_kWh_' + scenario_tag
        rev_tag2 = scenario2 + '_d_kWh_' + scenario_tag
        lcoe1 = lcoe_fiddle(output_parameters[rev_tag1], cost1)
        lcoe2 = lcoe_fiddle(output_parameters[rev_tag2], cost2)
        output_diffa = lcoe1 - lcoe2
    elif output_metric == 'cost':
        output_diffa = cost1 - cost2
    elif output_metric == 'yield':
        rev_tag1 = scenario1 + '_d_kWh_' + scenario_tag
        rev_tag2 = scenario2 + '_d_kWh_' + scenario_tag
        output_diffa = output_parameters[rev_tag1] - output_parameters[rev_tag2]
    try:
        output_diff = output_diffa.to_frame()
    except AttributeError:
        output_diff = output_diffa

    output_diff.columns = [output_metric]

    return output_diff

def prep_parameter_graphs(scenario1, input_parameters, output_parameters,
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

    cost_tag = scenario1 + '_d_cost'
    if cost_check:
        cost = output_parameters[cost_tag]
    elif not cost_check:
        cost = output_parameters[cost_tag][0]

    if output_metric == 'NPV':
        rev_tag = scenario1 + '_d_revenue_' + scenario_tag
        outputa = output_parameters[rev_tag] - cost
    elif output_metric == 'LCOE':
        rev_tag = scenario1 + '_d_kWh_' + scenario_tag
        outputa = lcoe_fiddle(output_parameters[rev_tag], cost)
    elif output_metric == 'cost':
        outputa = cost
    elif output_metric == 'yield':
        rev_tag = scenario1 + '_d_kWh_' + scenario_tag
        outputa = output_parameters[rev_tag]
    try:
        output = outputa.to_frame()
    except AttributeError:
        output = outputa
    output.columns = [output_metric]

    return output

def compile_df(df, identifiers, new_tags, output_df):
    """"""

    mc_flat = df[identifiers]
    mc_flat.columns = [new_tags]
    output_df = output_df.join(mc_flat)

    return output_df

def calculate_variance_diff(projectID, scenario1, scenario2, loss_check,
                            weather_check, cost_check,  output_metric):
    """"""
    # load pickl file containing mc results
    results_dict = load_analysis_dict(projectID)

    # grab parameters for scenarios of interest
    try:
        input_parameters, output_parameters = extract_difference_data(results_dict, scenario1, scenario2)
        output_diff = prep_difference_graphs(scenario1, scenario2, input_parameters, output_parameters,
                           loss_check, weather_check, cost_check,  output_metric)

        all_parameters = input_parameters.join(output_diff)
        output_table = calculate_variance_table(all_parameters, output_metric)

    except KeyError:
        input_parameters, output_parameters = extract_parameter_data(results_dict, scenario1)
        output = prep_parameter_graphs(scenario1, input_parameters, output_parameters,
                           loss_check, weather_check, cost_check,  output_metric)

        all_parameters = input_parameters.join(output)
        output_table = calculate_variance_table(all_parameters, output_metric)

    return output_table, input_parameters, output_parameters

def run_2d_scatter(scenario1, scenario2, parameter1, parameter2,
                   input_parameters, output_parameters,
                   loss_check, weather_check, cost_check, output_metric,
                   title, xlabel, ylabel):
    """"""
    if output_metric == 'LCOE':
        zlabel='LCOE \n(AU$/kWh)'
    elif output_metric == 'NPV':
        zlabel = 'NPV \n(AU$)'
    elif output_metric == 'cost':
        zlabel = 'Cost \n(AU$)'
    elif output_metric == 'yield':
        zlabel = 'Total Energy Output \n(kWh)'

    try:
        output_diff = prep_difference_graphs(scenario1, scenario2, input_parameters, output_parameters,
                               loss_check, weather_check, cost_check,  output_metric)
        label_diff = '2D_Scatter_' + scenario1 + '_vs_' + scenario2 + '_' + output_metric
        all_parameters = input_parameters.join(output_diff)
        zlabel_diff = '\u0394 ' + zlabel
        graph_scatter_2d(all_parameters, parameter1, parameter2, output_metric, title=title,
                 xlabel=xlabel, ylabel=ylabel, zlabel=zlabel_diff)
    except KeyError:
        output = prep_parameter_graphs(scenario1, input_parameters, output_parameters,
                                       loss_check, weather_check, cost_check, output_metric)
        label = scenario1 + '_' + output_metric
        all_parameters = input_parameters.join(output)
        graph_scatter_2d(all_parameters, parameter1, parameter2, output_metric,
                         title=title, xlabel=xlabel, ylabel=ylabel,
                         zlabel=zlabel)


def run_1d_scatter(scenario1, scenario2, parameter_list,
                   input_parameters, output_parameters,
                   loss_check, weather_check, cost_check, output_metric,
                   title, xlabel):
    """"""
    if output_metric == 'LCOE':
        ylabel='LCOE (AU$/kWh)'
    elif output_metric == 'NPV':
        ylabel = 'NPV (AU$)'
    elif output_metric == 'cost':
        ylabel = 'Cost (AU$)'
    elif output_metric == 'yield':
        ylabel = 'Total Energy Output (kWh)'

    try:
        output_diff = prep_difference_graphs(scenario1, scenario2, input_parameters, output_parameters,
                              loss_check, weather_check, cost_check,  output_metric)
        all_parameters = input_parameters.join(output_diff)
        label_diff = '1D_Scatter_' + scenario1 + '_vs_' + scenario2 + '_' + output_metric
        graph_scatter_1d(all_parameters, output_metric, parameter_list, title=title, xlabel=xlabel, ylabel=ylabel, savename=label_diff)

    except TypeError:
        output = prep_parameter_graphs(scenario1, input_parameters, output_parameters,
                                       loss_check, weather_check, cost_check, output_metric)
        all_parameters = input_parameters.join(output)
        label = scenario1 + '_' + output_metric
        graph_scatter_1d(all_parameters, output_metric, parameter_list, title=title, xlabel=xlabel, ylabel=ylabel, savename=label)


def run_histogram(projectID, scenario_list, loss_check, weather_check, cost_check, output_metric):
    """"""

    results_dict = load_analysis_dict(projectID)

    output_dict = {}
    for scenario in scenario_list:
        input_parameters, output_parameters = extract_parameter_data(results_dict, scenario)
        output_dict[scenario] = prep_parameter_graphs(scenario, input_parameters, output_parameters,
                                       loss_check, weather_check, cost_check, output_metric)

    label = output_metric + ' histogram'

    output_df = pd.DataFrame()
    for key in output_dict:
        output_df = pd.concat([output_df, output_dict[key]], axis=1)

    output_df.columns = scenario_list
    #output_df.columns = ['RackA_LowEffModule', 'RackB_LowEffModule', 'RackB_HighEffModule', 'RackC_LowEffModule', 'RackC_HighEffModule']

    if output_metric == 'LCOE':
        xlabel='LCOE (AU$/kWh)'
    elif output_metric == 'NPV':
        xlabel = 'NPV (AU$)'
    elif output_metric == 'cost':
        xlabel = 'Cost (AU$)'
    elif output_metric == 'yield':
        xlabel = 'Total Energy Output (kWh)'

    graph_histogram(output_df, scenario_list, title=label, xlabel=xlabel)

def gen_schedule(results_dict, scenario_list):
    """"""

    schedule_dict = {}
    test = 1;

    for key, multiplier in scenario_list:
        if test ==1:
            for category in results_dict[key]:
                schedule_dict[category] = {}
                for df in results_dict[key][category]:
                    if isinstance(results_dict[key][category][df], pd.DataFrame):
                        dim = results_dict[key][category][df].shape
                        schedule_dict[category][df] = pd.DataFrame(np.zeros(dim))
                        schedule_dict[category][df].index = results_dict[key][category][df].index
                        schedule_dict[category][df].columns = results_dict[key][category][df].columns
                    elif isinstance(results_dict[key][category][df], pd.Series):
                        dim = len(results_dict[key][category][df])
                        schedule_dict[category][df] = pd.Series(np.zeros(dim))
                        schedule_dict[category][df].index = results_dict[key][category][df].index
        else:
            pass
        test = 0;

    for key, multiplier in scenario_list:
        for category in results_dict[key]:
            for df in results_dict[key][category]:
                if isinstance(schedule_dict[category][df], pd.DataFrame):
                    add_item = results_dict[key][category][df] * multiplier
                    schedule_dict[category][df] = schedule_dict[category][df].add(add_item, fill_value=0)
                elif isinstance(schedule_dict[category][df], pd.Series):
                    schedule_dict[category][df] = schedule_dict[category][df] + results_dict[key][category][df] * multiplier

    return schedule_dict

def compare_schedules(projectID, schedule1, schedule1ID, schedule2, schedule2ID,
                      loss_check, weather_check, cost_check, output_metric):
    """"""

    results_dict = load_analysis_dict(projectID)

    # grab parameters for scenarios of interest
    try:
        results1 = gen_schedule(results_dict, schedule1)
        results2 = gen_schedule(results_dict, schedule2)
        input_parameters, output_parameters = extract_schedule_difference(results_dict, results1, results2,
                                                                      schedule1ID, schedule2ID)
        output_diff = prep_difference_graphs(results1, results2, input_parameters, output_parameters,
                                             loss_check, weather_check, cost_check, output_metric)
        label_diff = schedule1ID + '_vs_' + schedule2ID + '_' + output_metric
        all_parameters = input_parameters.join(output_diff)
        output_table = calculate_variance_table(all_parameters, output_metric, label_diff)

    except NameError:
        results1 = gen_schedule(results_dict, schedule1)
        input_parameters, output_parameters = extract_schedule_parameters(results_dict, results1)
        output = prep_parameter_graphs(results1, input_parameters, output_parameters,
                                       loss_check, weather_check, cost_check, output_metric)
        label = schedule1ID + '_' + output_metric
        all_parameters = input_parameters.join(output)
        output_table = calculate_variance_table(all_parameters, output_metric, label)

    return output_table, input_parameters, output_parameters
