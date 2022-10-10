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
from Functions.apply_corrections import weather_correct

# This suppresses a divide be zero warning message that occurs in pvlib tools.py.
warnings.filterwarnings(action='ignore',
                                message='divide by zero encountered in true_divide*')

 # %% ===========================================================
def dump_iter(combined_mc_dict, repeat_num, scenario_id):
     """"""

     bng_path = 'C:\\Users\phill\Documents\Bangladesh Application\output_files'
     dump_dict = {'combined_yield_mc': combined_mc_dict,
                      'discounted_ghi': ghi_df}
     file_name = "analysis_dict" + '_' +str(scenario_id) + "_" + str(repeat_num) + '.p'
     pickle_path = os.path.join(bng_path, 'mc_analysis', file_name)
     cpickle.dump(dump_dict, open(pickle_path, "wb"))

 # %% ===========================================================
 # define iteration scenarios

iter_num = 500
iter_limit = 50

 # %% ===========================================================
 # define input and scenario data

input_params = {}
temp_model = 'pvsyst'
input_params['albedo'] = 0.2
input_params['tkd_to_usd'] = 1e3
input_params['scheduled_price'] = 83
input_params['zone_area'] = 500
input_params['num_of_zones'] = 50
input_params['discount_rate'] = 0.07

location = []
location[] =

scenario_dict = {}
scenario_dict['scenario_ID'] = 'Patuakhali'

 # %% ==========================================================
 #code to define number of zones from provided land area

 # %% ===========================================================
 # define cost breakdown and generate cost datatables

cost_path = 'C:\\Users\phill\Documents\Bangladesh Application\input_files\cost_tables.csv'
cost_tables = pd.read_csv(cost_path)
cost_datatables = generate_parameters(cost_tables)

 # %% ===========================================================
 # code defining loss factors and generating mc dataframe

loss_path = 'C:\\Users\phill\Documents\Bangladesh Application\input_files\loss_tables.csv'
loss_tables = pd.read_csv(loss_path)
loss_datatables = generate_parameters(loss_tables)

 # %% ===========================================================
# Monte Carlo for yield parameters
# first create ordered dict of weather and output
# need a weather file containing several years worth of data, no gaps allowed
# All time stamps should be UTC

def weather_import(file_name, location, corrections):
    """"""

    weather_folder = 'C:\\Users\phill\Documents\Bangladesh Application\input_files\weather'
    weather_path = os.path.join(weather_folder, file_name)
    weather_file_init = pd.read_csv(weather_path)
    weather_file = weather_correct(weather_file_init, location, corrections)

    return weather_file


mc_weather_name = 'Combined_Longi_570_Tracker-bifacial_FullTS_8m.csv'
data_path = "C:\\Users\phill\Documents\Bangladesh Application\input_files\weather"
file_path = os.path.join(data_path, "corrections.p")
corrections = cpickle.load(open(file_path, 'rb'))
mc_weather_file = weather_import(mc_weather_name, location, corrections)

# %%

weather_mc_dict = {}
loss_mc_dict = {}
combined_mc_dict = {}
if iter_num > iter_limit:
    repeats = iter_num // iter_limit + (iter_num % iter_limit > 0)
    for i in range(repeats):
        combined_mc_dict, ghi_df = \
            mc_func.run_yield_mc(scenario_dict, input_params, mc_weather_file, loss_datatables)
        dump_iter(combined_mc_dict, i, scenario_dict['scenario_ID'])
else:
    combined_mc_dict, ghi_df = \
        mc_func.run_yield_mc(scenario_dict, input_params, mc_weather_file, loss_datatables)

# %% ==================================================
# Assemble pickled data
yield_iter_dict = {}

i =0
test=True
while test:
    tag = 'analysis_dict' + '_' + scenario_dict['scenario_ID'] + '_' + str(i) + '.p'
    iter_path = os.path.join(parent_path, 'Data', 'mc_analysis', tag)
    if os.path.isfile(iter_path):
        yield_iter_dict[i] = cpickle.load(open(iter_path, 'rb'))
        i = i + 1
    else:
        test=False


# %% ==================================================
weather_mc_dict = {}
loss_mc_dict = {}
combined_yield_mc_dict ={}
discounted_ghi_full = pd.DataFrame()

for iteration in yield_iter_dict:
    for key in yield_iter_dict[iteration]:
        if key == 'discounted_ghi':
            pass
        else:
            for year in yield_iter_dict[iteration][key]:
                dict_name = key + '_dict'
                globals()[dict_name][year] = {}
                for scenario in yield_iter_dict[iteration][key][year]:
                    globals()[dict_name][year][scenario] = {}
                    for parameter in yield_iter_dict[iteration][key][year][scenario]:
                        globals()[dict_name][year][scenario][parameter] = pd.DataFrame()

for iteration in yield_iter_dict:
    for key in yield_iter_dict[iteration]:
        if key == 'discounted_ghi':
            discounted_ghi_full = pd.concat([discounted_ghi_full, yield_iter_dict[iteration][key]], axis=0,
                                            ignore_index=True)
        else:
            for year in yield_iter_dict[iteration][key]:
                dict_name = key + '_dict'
                for scenario in yield_iter_dict[iteration][key][year]:
                    for parameter in yield_iter_dict[iteration][key][year][scenario]:
                        globals()[dict_name][year][scenario][parameter] = \
                            pd.concat([globals()[dict_name][year][scenario][parameter],
                                yield_iter_dict[iteration][key][year][scenario][parameter]],
                                axis=0, ignore_index=True)

# %% ==================================================
# Generate cost dict





# %% ==================================================
# Export relevant data

analysis_dict = {'cost_mc': cost_mc_dict, 'combined_yield_mc': combined_yield_mc_dict,
                 'discounted_ghi': discounted_ghi_full, 'loss_parameters': loss_datatables,
                 'data_tables': data_iter_dict}


pickle_path = os.path.join(parent_path, 'Data', 'mc_analysis', 'analysis_dictionary.p')
cpickle.dump(analysis_dict, open(pickle_path, "wb"))
