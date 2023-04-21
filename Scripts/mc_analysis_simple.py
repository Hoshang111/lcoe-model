"""
This is part 2 of the Monte-Carlo analysis process. This script will take system parameters
from a pickl and perform both yield and cost analysis using Monte-Carlo methods
"""

# %% Import
import random
import sys
import pvlib.pvsystem
sys.path.append( '..' )

import pandas as pd
import numpy as np
import os
import Functions.mc_yield_functions as mc_func
from Functions.optimising_functions import form_new_data_tables, optimise_layout
from Functions.sizing_functions import get_airtable, get_npv
from Functions.cost_functions import calculate_scenarios_iterations, create_iteration_tables, \
     generate_parameters, calculate_variance_contributions, import_excel_data, generate_iterations
import warnings
import _pickle as cpickle
import pytz
from pvlib.location import Location
import ast
import Functions.bangladesh_functions as b_func

# This suppresses a divide be zero warning message that occurs in pvlib tools.py.
warnings.filterwarnings(action='ignore',
                                message='divide by zero encountered in true_divide*')

 # %% ===========================================================
 # Need to replace API_KEY and EMAIL with appropriate account

API_KEY = "gHAuzn9Uv6qRgQ8EYgTdIQRkWk2hpfqNjTxItLQk"
EMAIL = "p.hamer@unsw.edu.au"
BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/himawari-tmy-download.csv?"
DATASET = ['tmy-2020']


 # %% ===========================================================
def dump_iter(combined_mc_dict, repeat_num, scenario_id):
     """"""

     bng_path = 'Data\OutputData'
     dump_dict = {'combined_yield_mc': combined_mc_dict,
                      'discounted_ghi': ghi_df}
     file_name = "analysis_dict" + '_' +str(scenario_id) + "_" + str(repeat_num) + '.p'
     pickle_path = os.path.join(bng_path, 'mc_analysis', file_name)
     cpickle.dump(dump_dict, open(pickle_path, "wb"))

def gen_costs(cost_datatables, site_params, discount_rate):
    """"""

    cost_capital_pMW = cost_datatables['base_pMW']+cost_datatables['transmission']*site_params['dist_substation']\
        +cost_datatables['site_prep']*site_params['flood_multiplier']
    cost_capital_other = cost_datatables['roads']*site_params['dist_road']
    ongoing_costs_pMW = cost_datatables['om_pMWpy']
    capital_cost = cost_capital_pMW*site_params['num_inverters']*2.5+cost_capital_other

    cost_dict = {}
    for i in range(31):
        if i==0:
            cost_dict[i] = capital_cost
        else:
            cost_dict[i] = ongoing_costs_pMW*site_params['num_inverters']*2.5

    cost_outputs_dict = {}
    yearly_costs = pd.concat(cost_dict, axis=1)
    yearly_costs.columns = range(2022, 2053)

    cost_outputs_dict['yearly_costs'] = yearly_costs

    cost_outputs_dict['total_cost'] = yearly_costs.sum(axis=1)

    year_offset = pd.Series(range(0, 31))
    year_offset.index = yearly_costs.columns

    yearly_factor = 1 / (1 + discount_rate) ** year_offset
    df_factor_dummy = pd.DataFrame(yearly_factor)
    df_factor = df_factor_dummy.T
    cost_outputs_dict['yearly_npv'] = yearly_costs.mul(yearly_factor, axis=1)

    cost_outputs_dict['cost_npv'] = cost_outputs_dict['yearly_npv'].sum(axis=1)

    return cost_outputs_dict

def get_site_params(site_name):
    """"""

    data_path = 'Data\SystemData'
    filename = site_name + '.csv'
    file_path = os.path.join(data_path, filename)
    site_params = pd.read_csv(file_path, index_col=0)
    site_dict = {}
    site_dict['latitude'] = float(site_params[site_name]['latitude'])
    site_dict['longitude'] = float(site_params[site_name]['longitude'])
    site_dict['altitude'] = float(site_params[site_name]['altitude'])
    site_dict['site_area'] = float(site_params[site_name]['site_area'])
    site_dict['MW_rating'] = float(site_params[site_name]['MW_rating'])
    site_dict['timezone'] = site_params[site_name]['timezone']
    site_dict['num_inverters'] = float(site_params[site_name]['num_inverters'])
    site_dict['dist_road'] = float(site_params[site_name]['dist_road'])
    site_dict['dist_substation'] = float(site_params[site_name]['dist_substation'])
    site_dict['discount_rate'] = float(site_params[site_name]['discount_rate'])
    site_dict['tariff'] = float(site_params[site_name]['tariff'])
    site_dict['flood_multiplier'] = float(site_params[site_name]['flood_multiplier'])

    return site_dict
 # %% ===========================================================
 # define iteration scenarios

iter_num = 500
iter_limit = 50

 # %% ===========================================================
 # define input and scenario data
site = 'jamalpur'
site_params = get_site_params(site)

input_params = {}
input_params['temp_model'] = 'pvsyst'
input_params['albedo'] = 0.2
input_params['bdt_to_usd'] = 0.0096
input_params['zone_area'] = 28000
input_params['num_of_zones'] = site_params['num_inverters']
input_params['discount_rate'] = site_params['discount_rate']
input_params['MW_rating'] = site_params['MW_rating']
input_params['MW_per_inverter'] = 3.0096
input_params['site_area'] = 4046.86*site_params['site_area']

location = {}
location['latitude'] = site_params['latitude']
location['longitude'] = site_params['longitude']
location['name'] = site
location['altitude'] = site_params['altitude']
location['timezone'] = site_params['timezone']

scenario_dict = {}
scenario_dict['scenario_ID'] = site
scenario_dict['module'] = b_func.get_module('Trina_TSM_DEG21C_20')
scenario_dict['inverter'] = b_func.get_inverter()
scenario_dict['strings_per_inverter'] = 24
scenario_dict['modules_per_string'] = 190
scenario_dict['modules_per_inverter'] = 4560
scenario_dict['rack'] = 'fixed'
scenario_dict['MW_rating'] = site_params['MW_rating']
scenario_dict['MW_per_inverter'] = input_params['MW_per_inverter']

 # %% ==========================================================
 #code to define number of zones from provided land area

 # %% ===========================================================
 # define cost breakdown and generate cost datatables

cost_path = 'Data\CostData\\bang_costs.csv'
cost_tables = pd.read_csv(cost_path)
cost_datatables = generate_iterations(cost_tables, index_name='ScenarioID',
                                        index_description='ScenarioName', num_iterations=iter_num,
                                        iteration_start=0, default_dist_type = 'flat')

 # %% ===========================================================
 # code defining loss factors and generating mc dataframe

loss_path = 'Data\SystemData\\bang_loss.csv'
loss_tables = pd.read_csv(loss_path)
loss_datatables = generate_iterations(loss_tables, index_name='YieldID',
                                        index_description='YieldName', num_iterations=iter_num,
                                        iteration_start=0, default_dist_type = 'flat')

 # %% ===========================================================
# Monte Carlo for yield parameters
# first create ordered dict of weather and output
# need a weather file containing several years worth of data, no gaps allowed
# All time stamps should be UTC

def weather_import(API_KEY, EMAIL, BASE_URL, LAT, LONG, DATASET):
    """"""

    weather_file = b_func.get_nsrdb(API_KEY, EMAIL, BASE_URL, LAT, LONG, DATASET)
    weather_file.index = pd.to_datetime(weather_file.index, utc=True)
    ghi = weather_file['ghi'].groupby(weather_file.index.year).sum()

    return weather_file, ghi


mc_weather_file, yearly_ghi = weather_import(API_KEY, EMAIL, BASE_URL, site_params['latitude'],
                                             site_params['longitude'], DATASET)



# %%

weather_mc_dict = {}
loss_mc_dict = {}
combined_mc_dict = {}
if iter_num > iter_limit:
    repeats = iter_num // iter_limit + (iter_num % iter_limit > 0)
    for i in range(repeats):
        loss_datatables_split = {}
        loss_datatables_split = loss_datatables[i * iter_limit:(i + 1) * iter_limit]
        combined_mc_dict, ghi_df = \
            mc_func.run_yield_mc(scenario_dict, input_params, mc_weather_file, loss_datatables_split, location, 20)
        dump_iter(combined_mc_dict, i, scenario_dict['scenario_ID'])
else:
    combined_mc_dict, ghi_df = \
        mc_func.run_yield_mc(scenario_dict, input_params, mc_weather_file, loss_datatables, location)

# %% ==================================================
# Generate costs
cost_iter_dict = gen_costs(cost_datatables, site_params, input_params['discount_rate'])

# %% ==================================================
# Assemble pickled data
yield_iter_dict = {}

i =0
test=True
while test:
    bng_path = 'C:\\Users\phill\Documents\Bangladesh Application\output_files'
    tag = 'analysis_dict' + '_' + scenario_dict['scenario_ID'] + '_' + str(i) + '.p'
    iter_path = os.path.join(bng_path, 'mc_analysis', tag)
    if os.path.isfile(iter_path):
        yield_iter_dict[i] = cpickle.load(open(iter_path, 'rb'))
        i = i + 1
    else:
        test=False


# %% ==================================================
combined_yield_mc_dict ={}
discounted_ghi_full = pd.DataFrame()

for iteration in yield_iter_dict:
    for key in yield_iter_dict[iteration]:
        if key == 'discounted_ghi':
            pass
        else:
            dict_name = key + '_dict'
            globals()[dict_name] = {}
            for parameter in yield_iter_dict[iteration][key]:
                globals()[dict_name][parameter] = pd.DataFrame()

for iteration in yield_iter_dict:
    for key in yield_iter_dict[iteration]:
        if key == 'discounted_ghi':
            discounted_ghi_full = pd.concat([discounted_ghi_full, yield_iter_dict[iteration][key]], axis=0,
                                            ignore_index=True)
        else:
            dict_name = key + '_dict'
            for parameter in yield_iter_dict[iteration][key]:
                globals()[dict_name][parameter] = \
                    pd.concat([globals()[dict_name][parameter],
                        yield_iter_dict[iteration][key][parameter]],
                        axis=0, ignore_index=True)

# %% ==================================================
# Export relevant data

analysis_dict = {'cost_mc': cost_iter_dict, 'combined_yield_mc': combined_yield_mc_dict,
                 'discounted_ghi': discounted_ghi_full, 'loss_parameters': loss_datatables,
                 'data_tables': cost_datatables}

# %% ==================================================
# Generate Report


# output_name = site + '_output_dict.p'
# pickle_path = os.path.join(bng_path, 'mc_analysis', output_name)
# cpickle.dump(analysis_dict, open(pickle_path, "wb"))
