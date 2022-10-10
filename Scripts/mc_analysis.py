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
import matplotlib.pyplot as plt
import Functions.simulation_functions as func
import Functions.mc_yield_functions as mc_func
from numpy.polynomial import Polynomial
from Functions.optimising_functions import form_new_data_tables, optimise_layout
from Functions.sizing_functions import get_airtable, get_npv
from Functions.cost_functions import calculate_scenarios_iterations, create_iteration_tables, \
     generate_parameters, calculate_variance_contributions, import_excel_data, generate_iterations
import warnings
from Functions.mc_yield_functions import weather_sort, generate_mc_timeseries, get_yield_datatables
import _pickle as cpickle
import pytz
from pvlib.location import Location
import ast

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

def get_dni(location, ghi, dhi):
    dt_lookup = pd.date_range(start=ghi.index[0],
                              end=ghi.index[-1], freq='T', tz=pytz.UTC)
    solpos_lookup = location.get_solarposition(dt_lookup)
    clearsky_lookup = location.get_clearsky(dt_lookup)
    zenith_to_rad = np.radians(solpos_lookup)
    cos_lookup = np.cos(zenith_to_rad)
    cos_lookup[cos_lookup > 30] = 30
    cos_lookup[cos_lookup < 0] = 0
    horizontal_dni_lookup = cos_lookup['apparent_zenith'] * clearsky_lookup['dni']
    horizontal_dni_lookup[horizontal_dni_lookup < 0] = 0
    hz_dni_lookup = horizontal_dni_lookup
 #   hz_dni_lookup.index = horizontal_dni_lookup.index.tz_convert('Asia/Dhaka')
  #  hz_dni_lookup.index = hz_dni_lookup.index.shift(periods=30)
    hourly_lookup = hz_dni_lookup.resample('H').mean()
    clearsky_dni_lookup = clearsky_lookup['dni']
 #   clearsky_dni_lookup.index = clearsky_lookup.index.tz_convert('Asia/Dhaka')
  #  clearsky_dni_lookup.index = clearsky_dni_lookup.index.shift(periods=30)
    hourly_dni_lookup = clearsky_dni_lookup.resample('H').mean()
    dni_lookup = hourly_dni_lookup / hourly_lookup
    dni_lookup[dni_lookup > 30] = 30
    #dni_lookup.index = dni_lookup.index.shift(periods=-30, freq='T')
    dni_simulated = (ghi-dhi)*dni_lookup
    dni_simulated.rename('dni', inplace=True)

    return dni_simulated

def weather_correct(weather_file, corrections, location):
    """"""

    # Define conditions of interest: Cloud types

    cloud_list = []
    for i in range(9):
        label = 'cloud' + str(i)
        if i in weather_file['cloud type'].values:
            locals()[label] = weather_file.loc[weather_file['cloud type'] == i, ['ghi', 'dhi', 'dni']]
        else:
            locals()[label] = pd.DataFrame()

        cloud_list.append(locals()[label])

    labels = ['cloud0', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'cloud5', 'cloud6', 'cloud7', 'cloud8', 'cloud9']

    cloud_zip = list(zip(cloud_list, labels))

    dhi_corrected = []
    ghi_corrected = []

    for data, id in cloud_zip:
        if len(data.index) > 0:
            ghi_label = id + '_ghi'
            dhi_label = id + '_dhi'

            if ghi_label in corrections.keys():
                ghi_factors = corrections[ghi_label][0:3]
            else:
                ghi_factors = [0, 1, 0]
            if dhi_label in corrections.keys():
                dhi_factors = corrections[dhi_label][0:3]
            else:
                dhi_factors = [0, 1, 0]

            ghi_correction = data['ghi'] ** 2 * ghi_factors[2] + data['ghi'] * ghi_factors[1] \
                             + ghi_factors[0]
            dhi_correction = data['dhi'] ** 2 * dhi_factors[2] + data['dhi'] * dhi_factors[1] \
                             + dhi_factors[0]
            ghi_corrected.append(ghi_correction)
            dhi_corrected.append(dhi_correction)

    df_ghi_corrected = pd.concat(ghi_corrected)
    df_ghi_corrected.sort_index(inplace=True)

    df_dhi_corrected = pd.concat(dhi_corrected)
    df_dhi_corrected.sort_index(inplace=True)

    corrected_full = pd.concat([df_ghi_corrected, df_dhi_corrected], axis=1)

    df_dhi_corrected.loc[(df_dhi_corrected < 0)] = 0
    df_ghi_corrected.loc[(df_ghi_corrected < 0)] = 0
    site = Location(latitude=location['latitude'],
                    longitude=location['longitude'],
                    name=location['name'],
                    altitude=location['altitude'],
                    tz=location['timezone']
                    )

    df_dni_corrected = get_dni(location=site, ghi=df_ghi_corrected, dhi=df_dhi_corrected)

    weather_dummy = weather_file.drop(['ghi', 'dhi', 'dni'], axis=1)
    weather_corrected = pd.concat([weather_dummy, df_ghi_corrected, df_dhi_corrected, df_dni_corrected], axis=1)

    return weather_corrected

def get_module(module_type):
    """
        rack_module_params function extracts the relevant rack and module variables for simulations

        Parameters
        ----------
        rack_type: str
            Type of rack to be used in solar farm. Two options: '5B_MAV' or 'SAT_1'

        module_type: str
            Type of module to be used in solar farm

        Returns
        -------
        rack_params, module_params : Dataframe
            Rack and module parameters to be used in PVlib simulations
    """
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Change the directory to the current folder
    # Note that for the cost_components columns, the text needs to be converted into a list of tuples. ast.literal_eval does this.

    suncable_modules = pd.read_csv(os.path.join('../Data', 'SystemData', 'Suncable_module_database.csv'), index_col=0,
                                   skiprows=[1, 2], converters={"cost_components": lambda x: ast.literal_eval(str(x))}).T

    module_params = suncable_modules[module_type]

    return module_params

def get_inverter():
    """
        rack_module_params function extracts the relevant rack and module variables for simulations

        Parameters
        ----------
        rack_type: str
            Type of rack to be used in solar farm. Two options: '5B_MAV' or 'SAT_1'

        module_type: str
            Type of module to be used in solar farm

        Returns
        -------
        rack_params, module_params : Dataframe
            Rack and module parameters to be used in PVlib simulations
    """
    invdb = pvlib.pvsystem.retrieve_sam('CECInverter')
    inverter_params = invdb.SMA_America__SC_2500_EV_US__550V_

    return inverter_params

def gen_costs(cost_tables, MWp, Area):
    """"""

    start_date = '1/1/2022 00:00:00'
    end_date = '31/12/2052 23:59:00'
    year_series = pd.date_range(start=start_date, end=end_date, freq='YS')
    cost_capitatl_pMW = cost_tables['DC_Cables-pMW']+cost_tables['Installation_pMW']\
                    +cost_tables["Inverter_pMW"]+cost_tables['Mounting_pMW']\
                    +cost_tables['modules_pMW']+cost_tables['ac_cables_pMW']\
                    +cost_tables['substation_pMW']
    cost_capital_other = cost_tables['transmission_site'] + cost_tables['site_prep_pm2']*Area
    ongoing_costs_pMW = cost_tables['om_pMWpy']



    return

 # %% ===========================================================
 # define iteration scenarios

iter_num = 20
iter_limit = 10

 # %% ===========================================================
 # define input and scenario data

input_params = {}
input_params['temp_model'] = 'pvsyst'
input_params['albedo'] = 0.2
input_params['bdt_to_usd'] = 0.0096
input_params['scheduled_price'] = 10
input_params['zone_area'] = 19000
input_params['num_of_zones'] = 152
input_params['discount_rate'] = 0.07
input_params['MW_rating'] = 460.964
input_params['site_area'] = 4046.86*562

location = {}
location['latitude'] = 21.706871
location['longitude'] = 91.890997
location['name'] = 'singapore_site'
location['altitude'] = 0
location['timezone'] = 'Asia/Dhaka'

scenario_dict = {}
scenario_dict['scenario_ID'] = 'Singapore'
scenario_dict['module'] = get_module('Trina_TSM_DEG21C_20')
scenario_dict['inverter'] = get_inverter()
scenario_dict['strings_per_inverter'] = 24
scenario_dict['modules_per_string'] = 196
scenario_dict['modules_per_inverter'] = 4704
scenario_dict['rack'] = 'fixed'

 # %% ==========================================================
 #code to define number of zones from provided land area

 # %% ===========================================================
 # define cost breakdown and generate cost datatables

cost_path = 'C:\\Users\phill\Documents\Bangladesh Application\input_files\\bang_costs.csv'
cost_tables = pd.read_csv(cost_path)
cost_datatables = generate_iterations(cost_tables, index_name='ScenarioID',
                                        index_description='ScenarioName', num_iterations=iter_num,
                                        iteration_start=0, default_dist_type = 'flat')

 # %% ===========================================================
 # code defining loss factors and generating mc dataframe

loss_path = 'C:\\Users\phill\Documents\Bangladesh Application\input_files\\bang_loss.csv'
loss_tables = pd.read_csv(loss_path)
loss_datatables = generate_iterations(loss_tables, index_name='YieldID',
                                        index_description='YieldName', num_iterations=iter_num,
                                        iteration_start=0, default_dist_type = 'flat')

 # %% ===========================================================
# Monte Carlo for yield parameters
# first create ordered dict of weather and output
# need a weather file containing several years worth of data, no gaps allowed
# All time stamps should be UTC

def weather_import(file_name, location, corrections):
    """"""

    weather_folder = 'C:\\Users\phill\Documents\Bangladesh Application\input_files\weather'
    weather_path = os.path.join(weather_folder, file_name)
    weather_file_init = pd.read_csv(weather_path, index_col=0)
    weather_file_init.index = pd.to_datetime(weather_file_init.index, utc=True)
    weather_file = weather_correct(weather_file_init, corrections, location)

    return weather_file

mc_weather_name = 'sing_joined.csv'
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
            mc_func.run_yield_mc(scenario_dict, input_params, mc_weather_file, loss_datatables, location)
        dump_iter(combined_mc_dict, i, scenario_dict['scenario_ID'])
else:
    combined_mc_dict, ghi_df = \
        mc_func.run_yield_mc(scenario_dict, input_params, mc_weather_file, loss_datatables, location)

# %% ==================================================
# Generate costs


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
