""" This is the main script for the yield assessment. The script calls the functions below to
calculate the Net Present Value (NPV) of the solar farm
1) Weather:
Input: Weather file, year of simulation
Output: Weather dataframe in the required format for PVlib simulations
2) Racks & modules:
Input: Type of module and rack
Output: Module and rack parameters required for PVlib PVsystem extracted from the
module & rack database
3) Sizing
Input: DC size of the solar farm
Output: Configuration in terms of number of single-axis tracking (SAT) racks or 5B Maverick
units (MAV)
4) DC/AC Yield:
Input: number of racks, number of MAVs, weather data, module name, mounting type
(optional & future improvement: temperature rack type, aoi model, back-tracking/optimal tilt angle)
Output: DC/AC yield
5) Revenue and storage behaviour
Input: DC yield, export limit
Output: Revenue
6) Cost (get deterministic or monte-carlo cost distribution of the solar farm)
Input: DC size pf the solar farm
Output: Cost
7) Net present value (NPV)
Input: Revenue, Cost
Output: NPV
Initially, we will write the Main script to call out all these functions to give a NPV
Later, we will convert this to an optimization process which will give the optimum NPV based on:
- Configuration
- Mounting
- Other parameters (more advanced params like back tracking algo, temp/racking type etc.)
During the optimisation process/simulations, cost function will give deterministic values.
Once the optimum NPV is found cost function also give the Monte-Carlo distribution.
"""

# %% Import
import sys
sys.path.append( '..' )
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import Functions.simulation_functions as func
from Functions.optimising_functions import form_new_data_tables, optimise_layout, analyse_layout
from Functions.sizing_functions import get_airtable
from Functions.cost_functions import calculate_scenarios_iterations, create_iteration_tables, \
     generate_parameters, calculate_variance_contributions, import_excel_data

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
dni_dummy = pd.read_csv(os.path.join('../Data', 'WeatherData', 'TMY_dni_simulated_1minute.csv'), index_col=0)
dni_dummy.set_index(pd.to_datetime(dni_dummy.index, utc=False), drop=True, inplace=True)
dni_dummy.index = dni_dummy.index.tz_convert('Australia/Darwin')

weather_dnv.drop(['dni'],axis=1,inplace=True)
weather_dnv = weather_dnv.join(dni_dummy, how='left')
weather_dnv.rename(columns={"0": "dni"}, inplace=True)
weather_dnv = weather_dnv[['ghi','dni','dhi','temp_air','wind_speed','precipitable_water','dc_yield']]
weather_simulation = weather_dnv


# Sizing/rack and module numbers
# Call the constants from the database - unneeded if we just pass module class?
DCTotal = 11000  # DC size in MW
num_of_zones = 720  # Number of smaller zones that will make up the solar farm
zone_area = 1.4e5   # Zone Area in m2
rack_interval_ratio = 0.04
first_year_degradation = 0.02
degradation_rate = 0.01

# Yield Assessment Inputs
temp_model = 'sapm'  # choose a temperature model either Sandia: 'sapm' or PVSyst: 'pvsyst'

# Revenue and storage behaviour
export_lim = 3.2e9/num_of_zones # Watts per zone
storage_capacity = 4e7 # Wh per zone
scheduled_price = 0.00004  # AUD / Wh. Assumption: AUD 4c/kWh (conversion from Wh to kWh)

# Financial Parameters
discount_rate = 0.07

if use_previous_airtable_data:
    data_tables = import_excel_data('CostDatabaseFeb2022a.xlsx')
else:
    # cost data tables from airtable
    data_tables = get_airtable(save_tables=True)



# %%
# Cycle through alternative analysis scenarios


module_type = 'TOPCON_2028_M10'
install_year = 2028
rack_type = 'SAT_1_update'



kWh_series, dt_index , dc_df = analyse_layout(weather_simulation, \
                                                               rack_type, module_type, install_year, DCTotal,
                                                               num_of_zones, zone_area, \
                                                               temp_model, export_lim, storage_capacity,
                                                               scheduled_price, data_tables, discount_rate,
                                                               first_year_degradation, degradation_rate,
                                                               fig_title="dummy")