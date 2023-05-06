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

import os
import Functions.mc_yield_functions as mc_func
from Functions.cost_functions import generate_iterations
import warnings
import _pickle as cpickle
import Functions.bangladesh_functions as b_func
import scipy.special
import numpy as np

from bokeh.layouts import gridplot
from bokeh.plotting import figure, show

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

     current_path = os.getcwd()
     parent_path = os.path.dirname(current_path)
     bng_path = 'Data\OutputData'
     dump_dict = {'combined_yield_mc': combined_mc_dict,
                      'discounted_ghi': ghi_df}
     file_name = "analysis_dict" + '_' +str(scenario_id) + "_" + str(repeat_num) + '.p'
     pickle_path = os.path.join(parent_path, bng_path, 'mc_analysis', file_name)
     cpickle.dump(dump_dict, open(pickle_path, "wb"))

def gen_costs(cost_datatables, site_params, input_params):
    """"""
    discount_rate = input_params['discount_rate']
    cost_capital_pMW = cost_datatables['base_pMW']+cost_datatables['transmission']*site_params['dist_substation']
    cost_capital_pm2 = cost_datatables['site_prep_base']+cost_datatables['site_prep_flood']*input_params['flood_multiplier']
    cost_capital_other = cost_datatables['roads']*site_params['dist_road']
    ongoing_costs_pMW = cost_datatables['om_pMWpy']
    capital_cost = cost_capital_pMW*input_params['num_of_inverter']*2.5+cost_capital_pm2*input_params['site_area']+cost_capital_other

    cost_dict = {}
    for i in range(31):
        if i==0:
            cost_dict[i] = capital_cost
        else:
            cost_dict[i] = ongoing_costs_pMW*input_params['num_of_inverter']*2.5

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
    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)
    data_path = 'Data\SystemData'
    filename = 'test.csv'
    file_path = os.path.join(parent_path, data_path, filename)
    site_params = pd.read_csv(file_path, index_col=0)
    site_dict = {}
    site_name = site_params.columns[0]
    site_dict['site_name'] = site_name
    site_dict['latitude'] = float(site_params[site_name]['latitude'])
    site_dict['longitude'] = float(site_params[site_name]['longitude'])
    site_dict['altitude'] = float(site_params[site_name]['altitude'])
    site_dict['site_area'] = float(site_params[site_name]['site_area'])
    site_dict['MW_rating'] = float(site_params[site_name]['MW_rating'])
    site_dict['timezone'] = site_params[site_name]['timezone']
    site_dict['dist_road'] = float(site_params[site_name]['dist_road'])
    site_dict['dist_substation'] = float(site_params[site_name]['dist_substation'])
    site_dict['discount_rate'] = float(site_params[site_name]['discount_rate'])
    site_dict['flood_risk'] = site_params[site_name]['flood_risk']

    return site_dict

 # %% ===========================================================
 # Plotting Functions

def make_plot(title, hist, edges, x, pdf, cdf):
    p = figure(title=title, tools='', background_fill_color="#fafafa")
    p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
           fill_color="navy", line_color="white", alpha=0.5)
    p.line(x, pdf, line_color="#ff8888", line_width=4, alpha=0.7, legend_label="PDF")
    p.line(x, cdf, line_color="orange", line_width=2, alpha=0.7, legend_label="CDF")

    p.y_range.start = 0
    p.legend.location = "center_right"
    p.legend.background_fill_color = "#fefefe"
    p.xaxis.axis_label = 'x'
    p.yaxis.axis_label = 'Pr(x)'
    p.grid.grid_line_color = "white"
    return p

 # %% ===========================================================
 # define iteration scenarios

iter_num = 200
iter_limit = 50

 # %% ===========================================================
 # define input and scenario data
site = 'test'
site_params = get_site_params(site)

input_params = {}
input_params['temp_model'] = 'pvsyst'
input_params['albedo'] = 0.2
input_params['bdt_to_usd'] = 0.0096
input_params['zone_area'] = 28000
input_params['discount_rate'] = site_params['discount_rate']
input_params['MW_rating'] = site_params['MW_rating']
input_params['MW_per_inverter'] = 3.0096
input_params['site_area'] = site_params['site_area']
input_params['flood_multiplier'] = b_func.get_flood_mul(site_params['flood_risk'])

location = {}
location['latitude'] = site_params['latitude']
location['longitude'] = site_params['longitude']
location['name'] = site_params['site_name']
location['altitude'] = site_params['altitude']
location['timezone'] = site_params['timezone']

scenario_dict = {}
scenario_dict['scenario_ID'] = site_params['site_name']
scenario_dict['module'] = b_func.get_module('Trina_TSM_DEG21C_20')
scenario_dict['inverter'] = b_func.get_inverter()
scenario_dict['strings_per_inverter'] = 24
scenario_dict['modules_per_string'] = 190
scenario_dict['modules_per_inverter'] = 4560
scenario_dict['rack'] = 'fixed'
scenario_dict['MW_per_inverter'] = input_params['MW_per_inverter']

scenario_dict['MW_rating'], input_params['num_of_inverter'] = b_func.get_layout(input_params['site_area'],
                                                                                input_params['MW_rating'],
                                                                                location['latitude'],
                                                                                scenario_dict['module'],
                                                                                scenario_dict['modules_per_inverter'])

 # %% ===========================================================
 # define cost breakdown and generate cost datatables
current_path = os.getcwd()
parent_path = os.path.dirname(current_path)
cost_path = os.path.join(parent_path, 'Data\SystemData\\bang_costs_new.csv')
cost_tables = pd.read_csv(cost_path)
cost_datatables = generate_iterations(cost_tables, index_name='ScenarioID',
                                        index_description='ScenarioName', num_iterations=iter_num,
                                        iteration_start=0, default_dist_type = 'flat')

 # %% ===========================================================
 # code defining loss factors and generating mc dataframe

loss_path = os.path.join(parent_path, 'Data\SystemData\\bang_loss.csv')
loss_tables = pd.read_csv(loss_path)
loss_datatables = generate_iterations(loss_tables, index_name='YieldID',
                                        index_description='YieldName', num_iterations=iter_num,
                                        iteration_start=0, default_dist_type = 'flat')

 # %% ===========================================================
# Monte Carlo for yield parameters
# first create ordered dict of weather and output
# need a weather file containing several years worth of data, no gaps allowed
# All time stamps should be UTC

metadata, mc_weather_file = b_func.get_nsrdb(API_KEY, EMAIL, BASE_URL, site_params['latitude'],
                                             site_params['longitude'], DATASET)

# %%

weather_mc_dict = {}
loss_mc_dict = {}
combined_mc_dict = {}
dc_ordered, vdc_ordered, ghi_dict = mc_func.run_dc_sort(scenario_dict, input_params, mc_weather_file, location, 20)
if iter_num > iter_limit:
    repeats = iter_num // iter_limit + (iter_num % iter_limit > 0)
    for i in range(repeats):
        loss_datatables_split = {}
        loss_datatables_split = loss_datatables[i * iter_limit:(i + 1) * iter_limit]
        combined_mc_dict, ghi_df = \
            mc_func.run_yield_mc(scenario_dict, input_params, loss_datatables_split, dc_ordered, vdc_ordered, ghi_dict)
        dump_iter(combined_mc_dict, i, scenario_dict['scenario_ID'])
else:
    combined_mc_dict, ghi_df = \
        mc_func.run_yield_mc(scenario_dict, input_params, loss_datatables, dc_ordered, vdc_ordered, ghi_dict)

# %% ==================================================
# Generate costs
cost_iter_dict = gen_costs(cost_datatables, site_params, input_params)

# %% ==================================================
# Assemble pickled data
yield_iter_dict = {}

i =0
test=True
while test:
    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)
    bng_path = 'Data\OutputData'
    tag = 'analysis_dict' + '_' + scenario_dict['scenario_ID'] + '_' + str(i) + '.p'
    iter_path = os.path.join(parent_path, bng_path, 'mc_analysis', tag)
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
# calculate output metrics

costs_cat = ['Ex_works', 'transmission', 'site_prep', 'roads']
costs_values = [analysis_dict['data_tables']['base_pMW'][0]*scenario_dict['MW_rating'],
                analysis_dict['data_tables']['transmission'][0]*scenario_dict['MW_rating']*site_params['dist_substation'],
                (analysis_dict['data_tables']['site_prep_base'][0]+analysis_dict['data_tables']['site_prep_flood'][0]*input_params['flood_multiplier'])*site_params['site_area'],
                analysis_dict['data_tables']['roads'][0]*site_params['dist_road']]

costs_series = analysis_dict['cost_mc']['cost_npv']
cost_df = pd.DataFrame(costs_series)
LCOE = cost_df/analysis_dict['combined_yield_mc']['kWh_total_discounted']
year1_output = analysis_dict['combined_yield_mc']['kWh_yearly'][2023]
capital_cost = analysis_dict['cost_mc']['yearly_costs'][2022]
ongoing_cost = analysis_dict['cost_mc']['yearly_costs'][2023]
specific_yield = year1_output / 3009.6 / input_params['num_of_inverter']

# %% ==================================================
# Generate Report

hist, edges = np.histogram(LCOE, density=True, bins=20)

