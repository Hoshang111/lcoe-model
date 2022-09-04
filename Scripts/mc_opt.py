
""" This is part 1 of 2 steps for Monte-Carlo Analysis. This step will calculate the
optimized layout for a set of default parameters and export this to a pickl file. This file
can then be used for full Monte-Carlo analysis including both yield and costs
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
# %%
# Set overall conditions for this analysis


use_previous_airtable_data = False

# Weather
simulation_years = np.arange(2007, 2022, 1)
weather_dnv_file = 'SunCable_TMY_HourlyRes_bifacial_545_4m_result.csv'
weather_file = 'Solcast_PT60M.csv'
weather_solcast = func.weather(simulation_years, weather_file)
weather_solcast_simulation = weather_solcast['2010-01-01':'2010-12-31']

# Complete set of dnv weather data you can extract specific years for simulations later on
weather_dnv = func.weather_benchmark_adjustment_mk2(weather_solcast_simulation, weather_dnv_file)

weather_dnv.index = weather_dnv.index.tz_localize('Australia/Darwin')


# %% Now create a new weather data for DNV with simulated dni and simulate with this weather data...
current_path = os.getcwd()
parent_path = os.path.dirname(current_path)
dni_dummy = pd.read_csv(os.path.join(parent_path, 'Data', 'WeatherData', 'TMY_dni_simulated_1minute.csv'), index_col=0)
dni_dummy.set_index(pd.to_datetime(dni_dummy.index, utc=False), drop=True, inplace=True)
dni_dummy.index = dni_dummy.index.tz_convert('Australia/Darwin')

weather_dnv.drop(['dni'],axis=1,inplace=True)
weather_dnv = weather_dnv.join(dni_dummy, how='left')
weather_dnv.rename(columns={"0": "dni"}, inplace=True)
weather_dnv = weather_dnv[['ghi','dni','dhi','temp_air','wind_speed','precipitable_water','dc_yield']]

# shift weather files 30 min so that solar position is calculated at midpoint of period
weather_dnv_mod = weather_dnv.shift(periods=30, freq='T')
weather_simulation = weather_dnv_mod


# Sizing/rack and module numbers
# Call the constants from the database - unneeded if we just pass module class?
DCTotal = 11000  # DC size in MW
num_of_zones = 720  # Number of smaller zones that will make up the solar farm
zone_area = 1.4e5   # Zone Area in m2
rack_interval_ratio = 0.01

# Yield Assessment Inputs
temp_model = 'pvsyst'  # choose a temperature model either Sandia: 'sapm' or PVSyst: 'pvsyst'

# Revenue and storage behaviour
export_lim = 3.2e9/num_of_zones # Watts per zone
storage_capacity = 5e7 # Wh per zone
scheduled_price = 0.000150  # AUD / Wh. Assumption: AUD 4c/kWh (conversion from Wh to kWh)

# Financial Parameters
discount_rate = 0.07

if use_previous_airtable_data:
    data_tables = import_excel_data('CostDatabaseFeb2022a.xlsx')
else:
    # cost data tables from airtable
    data_tables = get_airtable(save_tables=True)

input_data = [['temp_model', 'storage_capacity', 'scheduled_price', 'export_lim',
              'discount_rate', 'zone_area', 'num_of_zones'],
              [temp_model, storage_capacity, scheduled_price , export_lim,
              discount_rate, zone_area, num_of_zones]]

input_df = pd.DataFrame(input_data)
current_path = os.getcwd()
parent_path = os.path.dirname(current_path)
file_name = os.path.join(parent_path, 'OutputFigures', 'input_params.csv')
input_df.to_csv(file_name, index=False, header=False)

yield_datatables = get_yield_datatables()
MAV_loss_params = yield_datatables[0].iloc[0]
SAT_loss_params = yield_datatables[1].iloc[0]

   # %%
# Cycle through alternative analysis scenarios

def optimize (RACK_TYPE, MODULE_TYPE, INSTALL_YEAR, SCENARIO_LABEL, scenario_tables_combined, loss_params):
    module_type = MODULE_TYPE
    install_year = INSTALL_YEAR
    rack_type = RACK_TYPE

    scenario_tables_optimum, revenue, kWh_export, npv_output, rack_params, module_params = optimise_layout(
                                                                   weather_simulation, rack_type, module_type,
                                                                   install_year, DCTotal, num_of_zones, zone_area,
                                                                   rack_interval_ratio, temp_model, export_lim,
                                                                   storage_capacity, scheduled_price, data_tables,
                                                                   discount_rate, loss_params, fig_title=SCENARIO_LABEL)

    scenario_tables_combined.append((scenario_tables_optimum, SCENARIO_LABEL))

    return SCENARIO_LABEL, scenario_tables_optimum, revenue, kWh_export, npv_output, rack_params, module_params

# Create variables to hold the results of each analysis
SAT = 'SAT_1_update'
MAV = '5B_MAV_update'
PERC2023 = 'PERC_2023_M10'
TOP2023 = 'TOPCON_2023_M10'
HJT2023 = 'HJT_2023_M10'
PERC2025 = 'PERC_2025_M10'
TOP2025 = 'TOPCON_2025_M10'
HJT2025 = 'HJT_2025_M10'
PERC2028 = 'PERC_2028_M10'
TOP2028 = 'TOPCON_2028_M10'
HJT2028 = 'HJT_2028_M10'
PERC2031 = 'PERC_2031_M10'
TOP2031 = 'TOPCON_2031_M10'
HJT2031 = 'HJT_2031_M10'

#
# 2024 - assume modules PERC_2023_M10, etc
# 2024 - assume modules PERC_2025_M10, etc

# 2026 - assume modules PERC_2025_M10, etc
# 2026 - assume modules PERC_2028_M10, etc

# 2028 - assume modules PERC_2028_M10, etc
# 2028 - assume modules PERC_2031_M10, etc

# scenario_tables_2024 = []
# results_SAT_PERC_2024 = optimize (SAT, PERC2023, 2024, 'SAT PERC 2024', scenario_tables_2024)
# results_MAV_PERC_2024 = optimize (MAV, PERC2023, 2024, 'MAV PERC 2024', scenario_tables_2024)
# results_SAT_HJT_2024 = optimize (SAT, HJT2023, 2024, 'SAT HJT 2024', scenario_tables_2024)
# results_MAV_HJT_2024 = optimize (MAV, HJT2023, 2024, 'MAV HJT 2024', scenario_tables_2024)
# results_SAT_TOP_2024 = optimize (SAT, TOP2023, 2024, 'SAT TOP 2024', scenario_tables_2024)
# results_MAV_TOP_2024 = optimize (MAV, TOP2023, 2024, 'MAV TOP 2024', scenario_tables_2024)
# results_SAT_PERCa_2024 = optimize (SAT, PERC2025, 2024, 'SAT PERCa 2024', scenario_tables_2024)
# results_MAV_PERCa_2024 = optimize (MAV, PERC2025, 2024, 'MAV PERCa 2024', scenario_tables_2024)
# results_SAT_HJTa_2024 = optimize (SAT, HJT2025, 2024, 'SAT HJTa 2024', scenario_tables_2024)
# results_MAV_HJTa_2024 = optimize (MAV, HJT2025, 2024, 'MAV HJTa 2024', scenario_tables_2024)
# results_SAT_TOPa_2024 = optimize (SAT, TOP2025, 2024, 'SAT TOPa 2024', scenario_tables_2024)
# results_MAV_TOPa_2024 = optimize (MAV, TOP2025, 2024, 'MAV TOPa 2024', scenario_tables_2024)

# scenario_tables_2026 = []
# results_SAT_PERC_2026 = optimize (SAT, PERC2025, 2026, 'SAT PERC 2026',scenario_tables_2026)
# results_MAV_PERC_2026 = optimize (MAV, PERC2025, 2026, 'MAV PERC 2026',scenario_tables_2026)
# results_SAT_HJT_2026 = optimize (SAT, HJT2025, 2026, 'SAT HJT 2026',scenario_tables_2026)
# results_MAV_HJT_2026 = optimize (MAV, HJT2025, 2026, 'MAV HJT 2026',scenario_tables_2026)
# results_SAT_TOP_2026 = optimize (SAT, TOP2025, 2026, 'SAT TOP 2026',scenario_tables_2026)
# results_MAV_TOP_2026 = optimize (MAV, TOP2025, 2026, 'MAV TOP 2026',scenario_tables_2026)
# results_SAT_PERCa_2026 = optimize (SAT, PERC2028, 2026, 'SAT PERCa 2026',scenario_tables_2026)
# results_MAV_PERCa_2026 = optimize (MAV, PERC2028, 2026, 'MAV PERCa 2026',scenario_tables_2026)
# results_SAT_HJTa_2026 = optimize (SAT, HJT2028, 2026, 'SAT HJTa 2026',scenario_tables_2026)
# results_MAV_HJTa_2026 = optimize (MAV, HJT2028, 2026, 'MAV HJTa 2026',scenario_tables_2026)
# results_SAT_TOPa_2026 = optimize (SAT, TOP2028, 2026, 'SAT TOPa 2026',scenario_tables_2026)
# results_MAV_TOPa_2026 = optimize (MAV, TOP2028, 2026, 'MAV TOPa 2026',scenario_tables_2026)



scenario_tables_2028 = []
# results_SAT_PERC_2028 = optimize (SAT, PERC2028, 2028, 'SAT PERC 2028',scenario_tables_2028)
# results_MAV_PERC_2028 = optimize (MAV, PERC2028, 2028, 'MAV PERC 2028',scenario_tables_2028)
# results_SAT_HJT_2028 = optimize (SAT, HJT2028, 2028, 'SAT HJT 2028',scenario_tables_2028)
# results_MAV_HJT_2028 = optimize (MAV, HJT2028, 2028, 'MAV HJT 2028',scenario_tables_2028)
# results_SAT_TOP_2028 = optimize (SAT, TOP2028, 2028, 'SAT TOP 2028',scenario_tables_2028)
# results_MAV_TOP_2028 = optimize (MAV, TOP2028, 2028, 'MAV TOP 2028',scenario_tables_2028)
results_SAT_PERCa_2028 = optimize (SAT, PERC2031, 2028, 'SAT_PERCa_2028', scenario_tables_2028, SAT_loss_params)
results_MAV_PERCa_2028 = optimize (MAV, PERC2031, 2028, 'MAV_PERCa_2028', scenario_tables_2028, MAV_loss_params)
results_SAT_HJTa_2028 = optimize (SAT, HJT2031, 2028, 'SAT_HJTa_2028', scenario_tables_2028, SAT_loss_params)
results_MAV_HJTa_2028 = optimize (MAV, HJT2031, 2028, 'MAV_HJTa_2028', scenario_tables_2028, MAV_loss_params)
results_SAT_TOPa_2028 = optimize (SAT, TOP2031, 2028, 'SAT TOPa 2028',scenario_tables_2028)
results_MAV_TOPa_2028 = optimize (MAV, TOP2031, 2028, 'MAV TOPa 2028',scenario_tables_2028)

# %% Save and download optimized layouts, needs to be updated

output_data = []
output_dict = {}

for scenario_tables in [scenario_tables_2028]:
    for results in scenario_tables:
        index = results[1]
        install_dummy = results[0][1]['InstallNumber']
        install_dummy2 = install_dummy.reset_index()
        install_dummy3 = install_dummy2['InstallNumber']
        Racks = install_dummy3[0]
        W_zone = install_dummy3[3]
        # MW_per_zone = Modules*results[2]
        # Total_GW = MW_per_zone*num_of_zones/1000
        output_data.append([index, Racks, W_zone])
        results_string = 'results_' + index
        output_dict[index] = globals()[results_string]

optimised_tables = pd.DataFrame(data=output_data, columns=['scenario', 'racks', 'W_zone'])
optimised_tables.set_index('scenario', inplace=True)
current_path = os.getcwd()
parent_path = os.path.dirname(current_path)
file_name = os.path.join(parent_path, 'OutputFigures', 'Optimised_layouts.csv')
optimised_tables.to_csv(file_name)

# %% ========================================
# save results tables to pickl

pickle_path = os.path.join(parent_path, 'OutputFigures', 'scenario_tables_2028.p')
cpickle.dump(output_dict, open(pickle_path, "wb"))
