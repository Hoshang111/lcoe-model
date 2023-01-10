# %% Import
import random
import sys
sys.path.append( '..' )
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import Functions.simulation_functions as func
import Functions.mc_yield_functions as mc_func
from numpy.polynomial import Polynomial
from Functions.optimising_functions import form_new_data_tables, optimise_layout
from Functions.sizing_functions import get_airtable, get_npv
from Functions.cost_functions import calculate_scenarios_iterations, create_iteration_tables, \
     generate_parameters, calculate_variance_contributions, import_excel_data
import warnings
from Functions.mc_yield_functions import weather_sort, generate_mc_timeseries, get_yield_datatables
import _pickle as cpickle

# This suppresses a divide be zero warning message that occurs in pvlib tools.py.
warnings.filterwarnings(action='ignore',
                                message='divide by zero encountered in true_divide*')


# import data from pickle

current_path = os.getcwd()
parent_path = os.path.dirname(current_path)

pickle_path = os.path.join(parent_path, 'Data', 'mc_analysis', 'analysis_dictionary_phill_test.p')
Analysis_dict = cpickle.load(open(pickle_path, 'rb'))


# Function to extract data tables from the analysis_dict

def extract_parameter_data(df, year_str):
    cost_mc = df['cost_mc'][year_str]
    weather_mc = df['weather_mc'][year_str]
    loss_mc = df['loss_mc'][year_str]
    combined_yield_mc = df['combined_yield_mc'][year_str]

    discounted_ghi = df['discounted_ghi']
    loss_parameters = df['loss_parameters']
    data_tables = df['data_tables'][year_str]




    # First set up a dataframe with all the possible output parameters we would like - the discounted revenue and cost
    output_parameters = pd.DataFrame(index=discounted_ghi.index)

    # Get results for cost monte carlo
    for item in cost_mc:
        cost_mc_flat = cost_mc[item]['discounted_cost_total'].rename('d_cost').to_frame()
        cost_mc_flat = cost_mc_flat.add_prefix(item + '_')
        output_parameters = output_parameters.join(cost_mc_flat)

    # Get results for yield only monte carlo - from loss_mc (which varies the loss parameters)
    for item in loss_mc:
        loss_mc_flat = loss_mc[item]['npv_revenue'].rename('d_revenue_loss').to_frame()
        loss_mc_flat = loss_mc_flat.add_prefix(item + '_')
        output_parameters = output_parameters.join(loss_mc_flat)

    # Get results for weather only Monte Carlo
    for item in weather_mc:
        weather_mc_flat = weather_mc[item]['npv_revenue'].rename('d_revenue_weather').to_frame()
        weather_mc_flat = weather_mc_flat.add_prefix(item + '_')
        output_parameters = output_parameters.join(weather_mc_flat)


    # Get results for combined_yield
    for item in combined_yield_mc:
        combined_yield_mc_flat = combined_yield_mc[item]['npv_revenue'].rename('d_revenue_combined').to_frame()
        combined_yield_mc_flat = combined_yield_mc_flat.add_prefix(item + '_')
        output_parameters = output_parameters.join(combined_yield_mc_flat)

    output_parameters = output_parameters.apply(pd.to_numeric, errors='ignore')

    # Now generate a list of all input parameters
    input_parameters = pd.DataFrame(index=discounted_ghi.index)
    # Get input parameters from cost monte carlo
    cost_parameters = generate_parameters(data_tables, use_name_as_ID=True)
    cost_parameters_flat = cost_parameters.copy()
    cost_parameters_flat.columns = [str(ID) + ': ' + var for (group, ID, var) in
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




# %%
scenarios = ['2028']
for year in scenarios:
    analysis_year = int(year)
    input_parameters, output_parameters = extract_parameter_data(Analysis_dict, year)




# %%
from scipy import stats

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

def graph_scatter_1d(input_factors, cost_result_name, parameter_list, title=None, short_titles=True,
                     xlabel=None, ylabel=None, show_regression=True, show_r=False, show_r2=True, savename=None):


    parameter_description_list = zip(parameter_list, parameter_list)

    for (parameter, label) in parameter_description_list:
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
                text = ''
                if show_r:
                    text = 'r = {0:.2f}'.format(r_value)
                if show_r2:
                    r2_value = r_value * r_value
                    text = text + '\nr$^2$ = {0:.2f}'.format(r2_value)
                plt.annotate(text, xy=(0.5, 0.5), fontsize=20, xycoords='figure fraction')

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



# import matplotlib.pylab as pylab
# params = {
#     # 'legend.fontsize': 'x-large',
#     #       'figure.figsize': (15, 5),
#          'axes.labelsize': 'small',
#          'axes.titlesize':'small',
#       'xtick.labelsize':'small',
#       'ytick.labelsize':'small'
# }
# pylab.rcParams.update(params)
import matplotlib

matplotlib.rcParams.update(matplotlib.rcParamsDefault)

# %%

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

graph_variance_contributions(output_parameters, input_parameters, 'MAV_PERCa_2028', cost_mc = True, revenue_type='fixed')

# graph_variance_contributions(output_parameters, input_parameters, 'MAV_PERCa_2028', cost_mc = False, revenue_type='loss')
#
# graph_variance_contributions(output_parameters, input_parameters, 'MAV_PERCa_2028', cost_mc = False, revenue_type='weather')
#
# graph_variance_contributions(output_parameters, input_parameters, 'MAV_PERCa_2028', cost_mc = False, revenue_type='combined')
#
# graph_variance_contributions(output_parameters, input_parameters, 'MAV_PERCa_2028', cost_mc = True, revenue_type='combined')







# %%
def graph_scatter_2d(input_data, parameter_x, parameter_y, parameter_z,
               title=None, xlabel=None, ylabel=None, zlabel=None):
    x = input_data[parameter_x]
    y = input_data[parameter_y]
    z = input_data[parameter_z]

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

    plt.show()
    plt.close()
# %%

def graph_histogram(input_data, scenario_list, title=None):
    data = input_data[[scenario_list]].reset_index()
    print(data)
    data.plot.hist(bins=50, histtype='step', fontsize=8)
    if title is None:
        title = 'Histogram'
    plt.title(title)
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

# %%

# graph_scatter_2d(scenario_tables,
#                  parameter_x='MAV_ave_temp_increase',
#                  parameter_y = 'MAV_degr_annual',
#                  parameter_z = 'MAV_PERCa_2028_kWh_total_discounted',
#                  xlabel = 'MAV ave temp increase',
#                  ylabel = 'MAV annual degradation',
#                  zlabel = 'Disc kWh',
#                  title = 'Key factors affecting MAV generation')
#
# # %%
#
# graph_scatter_2d(scenario_tables,
#                  parameter_x='SAT_degr_annual',
#                  parameter_y = 'SAT_bifaciality_modifier',
#                  parameter_z = 'SAT_HJTa_2028_kWh_total_discounted',
#                  xlabel = 'SAT annual degradation',
#                  ylabel = 'SAT bifaciality modifier',
#                  zlabel = 'Disc kWh',
#                  title = 'Key factors affecting SAT generation')

