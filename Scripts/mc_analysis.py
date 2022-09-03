"""
This is part 2 of the Monte-Carlo analysis process. This script will take system parameters
from a pickl and perform both yield and cost analysis using Monte-Carlo methods
"""

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

 # %% ===========================================================
 # define scenarios

scenarios = [#'2024',
            #'2026',
            '2028']

 # %% ===========================================================
 # import scenario data from pickle and simulation parameters from csv

current_path = os.getcwd()
parent_path = os.path.dirname(current_path)
scenario_dict = {}

for key in scenarios:
    pickle_path = os.path.join(parent_path, 'OutputFigures', 'scenario_tables_' + key + '.p')
    scenario_dict[key] = cpickle.load(open(pickle_path, 'rb'))

csv_path = os.path.join(parent_path, 'OutputFigures', 'input_params.csv')
input_params = pd.read_csv(csv_path, header=0)

# Import airtable data previously saved
data_tables = import_excel_data('CostDatabaseSept2022.xlsx')

 # %% ===========================================================
 # convert dtypes in input_params, want to keep saving as csv so human readable but does not preserve dtypes

input_params['temp_model'] = input_params['temp_model'].astype('string')
input_params['storage_capacity'] = pd.to_numeric(input_params['storage_capacity'])
input_params['scheduled_price'] = pd.to_numeric(input_params['scheduled_price'])
input_params['export_lim'] = pd.to_numeric(input_params['export_lim'])
input_params['discount_rate'] = pd.to_numeric(input_params['discount_rate'])
input_params['zone_area'] = pd.to_numeric(input_params['zone_area'])
input_params['num_of_zones'] = pd.to_numeric(input_params['num_of_zones'])

discount_rate = input_params['discount_rate'].values[0]

loss_datatables = {}
loss_datatables['MAV'], loss_datatables['SAT'] = get_yield_datatables()

 # %% ===========================================================
# Monte Carlo for yield parameters
# first create ordered dict of weather and output
# need a weather file containing several years worth of data, no gaps allowed

mc_weather_name = 'Combined_Longi_570_Tracker-bifacial_FullTS_8m.csv'
mc_weather_file = mc_func.mc_weather_import(mc_weather_name)

# %%

weather_mc_dict = {}
loss_mc_dict = {}
combined_mc_dict = {}
for key in scenarios:
    results_dict = scenario_dict[key]
    weather_mc_dict[key], loss_mc_dict[key], combined_mc_dict[key], ghi_df = \
        mc_func.run_yield_mc(results_dict, input_params, mc_weather_file, loss_datatables)

# %% ===========================================================
# Now calculate AC output (currently not used)



# %% ==========================================================
# Calculate LCOE and/or NPV for each iteration, and plot these for each optimum scenario.
# First generate a big table with index consisting of Iteration, Year, ScenarioID.


# %%
# Call Monte Carlo Cost analysis

# Do be deleted later - import occurs above.
data_tables = import_excel_data('CostDatabaseSept2022.xlsx')


# %%
def extract_scenario_tables(scenario_dict, analysis_year):
    mydata = scenario_dict[analysis_year]
    # print(mydata)
    output_list = []
    for item in mydata:
        # print(item)

        label = mydata[item][0]

        data = mydata[item][1]
        output_tuple = (data, label)
        output_list.append(output_tuple)

    return output_list

def extract_results_tables(scenario_dict, analysis_year):
    mydata = scenario_dict[analysis_year]
    output_list = []
    for item in mydata:
        output_tuple = (mydata[item][0], mydata[item][1], mydata[item][2], mydata[item][3], mydata[item][4])
        output_list.append(output_tuple)

    return output_list



# %%
cost_mc_dict = {}

for year in scenarios:
    analysis_year = int(year)
    scenario_tables = extract_scenario_tables(scenario_dict, year)

    # First generate data tables with the ScenarioID changed to something more intuitive
    new_data_tables = form_new_data_tables(data_tables, scenario_tables)

    # Create iteration data
    data_tables_iter = create_iteration_tables(new_data_tables, 100, iteration_start=0)

    # Calculate cost result
    outputs_iter = calculate_scenarios_iterations(data_tables_iter, year_start=analysis_year, year_end=2058)
    component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, cash_flow_by_year_iter = outputs_iter

    cost_dict = mc_func.get_cost_dict(cash_flow_by_year_iter, discount_rate)
    cost_mc_dict[year] = cost_dict

# %% ==================================================
# Export relevant data