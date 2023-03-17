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
import _pickle as cpickle

# This suppresses a divide be zero warning message that occurs in pvlib tools.py.
warnings.filterwarnings(action='ignore',
                                message='divide by zero encountered in true_divide*')

def pickl_it(file_name, tag):
    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)
    file_tag = tag + '.p'
    pickle_path = os.path.join(parent_path, 'Data', 'mc_analysis', file_tag)
    print(pickle_path)
    cpickle.dump(file_name, open(pickle_path, "wb"))

def run_mc(projectID, iter, start_year, revenue_year, end_year):
    def dump_iter(weather_mc_dict, loss_mc_dict, combined_mc_dict, repeat_num, scenario_id):
         """"""

         dump_dict = {'weather_mc': weather_mc_dict,
                          'loss_mc': loss_mc_dict, 'combined_yield_mc': combined_mc_dict,
                          'discounted_ghi': ghi_df}
         file_name = "analysis_dict" + '_' +str(scenario_id) + "_" + str(repeat_num) + '.p'
         pickle_path = os.path.join(parent_path, 'Data', 'mc_analysis', file_name)
         cpickle.dump(dump_dict, open(pickle_path, "wb"))

     # %% ===========================================================
     # define scenarios



    scenarios = [str(projectID)]
    iter_num = iter
    iter_limit = 10
     # %% ===========================================================
     # import scenario data from pickle and simulation parameters from csv

    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)

    pickle_path = os.path.join(parent_path, 'Data', 'mc_analysis', 'scenario_tables_' + projectID + '.p')
    scenario_dict = cpickle.load(open(pickle_path, 'rb'))

    # TODO this should read from inputs database
    csv_path = os.path.join(parent_path, 'OutputFigures', 'input_params.csv')
    input_params = pd.read_csv(csv_path, header=0)

    # Import airtable data
    use_previous_airtable_data = False
    if use_previous_airtable_data:
        data_tables = import_excel_data('CostDatabaseFeb2022a.xlsx')
    else:
        # cost data tables from airtable
        data_tables = get_airtable(save_tables=True)

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
    loss_datatables['MAV'], loss_datatables['SAT'] = get_yield_datatables(iter_num)

     # %% ===========================================================
    # Monte Carlo for yield parameters
    # first create ordered dict of weather and output
    # need a weather file containing several years worth of data, no gaps allowed

    mc_weather_name = 'Combined_Longi_570_Tracker-bifacial_FullTS_8m.csv'
    mc_weather_file = mc_func.mc_weather_import(mc_weather_name)

    # %%
    # generate full timeseries for weather and yield

    dc_ordered, ghi_dict = mc_func.gen_dcseries(scenario_dict, input_params, mc_weather_file)

    # %% ============================================================
    weather_mc_dict = {}
    loss_mc_dict = {}
    combined_mc_dict = {}
    if iter_num > iter_limit:
        repeats = iter_num // iter_limit + (iter_num % iter_limit > 0)
        for i in range(repeats):
            loss_datatables_split = {}
            loss_datatables_split['MAV'] = loss_datatables['MAV'][i * iter_limit:(i+1) * iter_limit]
            loss_datatables_split['SAT'] = loss_datatables['SAT'][i * iter_limit:(i+1) * iter_limit]
            weather_mc_dict, loss_mc_dict, combined_mc_dict, ghi_df = \
                mc_func.run_yield_mc(dc_ordered, input_params, ghi_dict, loss_datatables_split, start_year, revenue_year, end_year)
            dump_iter(weather_mc_dict, loss_mc_dict, combined_mc_dict, i, projectID)
    else:
        weather_mc_dict, loss_mc_dict, combined_mc_dict, ghi_df = \
            mc_func.run_yield_mc(dc_ordered, input_params, ghi_dict, loss_datatables, start_year, revenue_year, end_year)

    # %% ===========================================================
    # Now calculate AC output (currently not used)

    # %%
    def extract_scenario_tables(scenario_dict):
        # print(mydata)
        output_list = []
        for item in scenario_dict:
            # print(item)

            label = scenario_dict[item][0]

            data = scenario_dict[item][1]
            output_tuple = (data, label)
            output_list.append(output_tuple)

        return output_list

    def extract_results_tables(scenario_dict):
        output_list = []
        for item in scenario_dict:
            output_tuple = (scenario_dict[item][0], scenario_dict[item][1], scenario_dict[item][2],
                            scenario_dict[item][3], scenario_dict[item][4])
            output_list.append(output_tuple)

        return output_list



    # %%
    cost_mc_dict = {}
    data_iter_dict = {}
    # output_iter_dict ={}

    scenario_tables = extract_scenario_tables(scenario_dict)

    # First generate data tables with the ScenarioID changed to something more intuitive
    new_data_tables = form_new_data_tables(data_tables, scenario_tables)

    # Create iteration data
    data_tables_iter = create_iteration_tables(new_data_tables, iter_num, iteration_start=0)

    pickl_it(data_tables_iter, 'data_tables')
    # calculate cost result
    for scenario in scenario_dict:

        install_year = scenario_dict[scenario][7]
        data_tables_0 = data_tables_iter[0][data_tables_iter[0]['ScenarioID'] == scenario]
        data_tables_1 = data_tables_iter[1][data_tables_iter[1]['ScenarioID'] == scenario]
        data_tables_update = (data_tables_0, data_tables_1, data_tables_iter[2], data_tables_iter[3], data_tables_iter[4],
                              data_tables_iter[5], data_tables_iter[6])
        pickl_it(data_tables_update, 'update')
        outputs_iter = calculate_scenarios_iterations(data_tables_update, year_start=install_year, year_end=end_year)
        component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, cash_flow_by_year_iter = outputs_iter
        pickl_it(outputs_iter, 'outputs')
        cost_dict = mc_func.get_cost_dict(cash_flow_by_year_iter, discount_rate, start_year, install_year, end_year)
        pickl_it(cost_dict, scenario)
        cost_mc_dict[scenario] = cost_dict[scenario]

        # output_iter_dict[year] = outputs_iter
    pickl_it(cost_mc_dict, 'cost')
    # %% ==================================================
    # Assemble pickled data

    yield_iter_dict = {}

    i = 0
    test = True
    while test:
        tag = 'analysis_dict' + '_' + projectID + '_' + str(i) + '.p'
        iter_path = os.path.join(parent_path, 'Data', 'mc_analysis', tag)
        if os.path.isfile(iter_path):
            yield_iter_dict[i] = cpickle.load(open(iter_path, 'rb'))
            i = i + 1
        else:
            test = False

    # %% ==================================================
    discounted_ghi_full = pd.DataFrame()
    analysis_dict = {}

    for iteration in yield_iter_dict:
        for key in yield_iter_dict[iteration]:
            if key == 'discounted_ghi':
                pass
            else:
                for scenario in yield_iter_dict[iteration][key]:
                    dict_name = str(scenario)
                    analysis_dict[dict_name] = {}

    for iteration in yield_iter_dict:
        for key in yield_iter_dict[iteration]:
            if key == 'discounted_ghi':
                pass
            else:
                for scenario in yield_iter_dict[iteration][key]:
                    dict_name = str(scenario)
                    analysis_dict[dict_name][key] = {}
                    for parameter in yield_iter_dict[iteration][key][scenario]:
                        analysis_dict[dict_name][key][parameter] = pd.DataFrame()


    for iteration in yield_iter_dict:
        for key in yield_iter_dict[iteration]:
            if key == 'discounted_ghi':
                discounted_ghi_full = pd.concat([discounted_ghi_full, yield_iter_dict[iteration][key]], axis=0,
                                                ignore_index=True)
            else:
                for scenario in yield_iter_dict[iteration][key]:
                    dict_name = str(scenario)
                    for parameter in yield_iter_dict[iteration][key][scenario]:
                        analysis_dict[dict_name][key][parameter] = \
                            pd.concat([analysis_dict[dict_name][key][parameter],
                            yield_iter_dict[iteration][key][scenario][parameter]],
                            axis=0, ignore_index=True)


    # %% ==================================================
    # Export relevant data

    for key in analysis_dict:
        analysis_dict[key]['cost_mc'] = cost_mc_dict[key]
    analysis_dict['discounted_ghi'] = discounted_ghi_full
    analysis_dict['loss_parameters'] = loss_datatables
    analysis_dict['data_tables'] = data_tables_iter

    file_name = 'analysis_dictionary_' + projectID + '.p'
    pickle_path = os.path.join(parent_path, 'Data', 'mc_analysis', file_name)
    cpickle.dump(analysis_dict, open(pickle_path, "wb"))