""" This is the main script for the yield assessment. The script calls the functions below to calculate the Net Present Value
(NPV) of the solar farm

1) Weather:
Input: Weather file, year of simulation
Output: Weather dataframe in the required format for PVlib simulatins

2) Racks & modules:
Input: Type of module and rack
Output: Module and rack parameters required for PVlib PVsystem extracted from the module & rack database

3) Sizing
Input: DC size of the solar farm
Output: Configuration in terms of number of single-axis tracking (SAT) racks or 5B Maverick units (MAV)

4) DC/AC Yield:
Input: number of racks, number of MAVs, weather data, module name, mounting type (optional & future improvement:
temperature rack type, aoi model, back-tracking/optimal tilt angle)
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
During the optimisation process/simulations, cost function will give deterministic values. Once the optimum NPV is found
cost function also give the Monte-Carlo distribution.
"""

# %% Import
import pandas as pd
import numpy as np
import Simulation_functions as func
import airtable
import sizing
import Plotting as plot_func
import matplotlib.pyplot as plt
import matplotlib as mpl
import OptimiseLayout as optimise
import importlib
import SuncableCost as Suncost

# mpl.use('Qt5Agg')




# %%
# Set overall conditions for this analysis

# Weather
simulation_years = [2019]
weather_file = 'Solcast_PT60M.csv'
weather_simulation = func.weather(simulation_years, weather_file)

# Sizing/rack and module numbers
# Call the constants from the database - unneeded if we just pass module class?
DCTotal = 11000  # DC size in MW
num_of_zones = 267  # Number of smaller zones that will make up the solar farm
zone_area = 4e5   # Zone Area in m2
rack_interval_ratio = 0.04
module_type = 'HJT_2028_M10'  # Enter one of the modules from the SunCable module database
install_year = 2027

# Yield Assessment Inputs
temp_model = 'sapm'  # choose a temperature model either Sandia: 'sapm' or PVSyst: 'pvsyst'

# Revenue and storage behaviour
export_lim = 3.2e9/num_of_zones
storage_capacity = 4e7
scheduled_price = 0.00004  # 4c/kWh (conversion from Wh to kWh)

# Financial Parameters
discount_rate = 0.07

# cost data tables from airtable
data_tables = sizing.get_airtable()


################
# Optimise SATs
# %% ======================================
# Rack_module
rack_type = 'SAT_1'  # Choose rack_type from 5B_MAV or SAT_1 for maverick or single axis tracking respectively

scenario_tables_optimum_SAT, revenue_SAT, kWh_export_SAT = optimise.optimise_layout(weather_simulation, rack_type, module_type, install_year,
                     DCTotal, num_of_zones, zone_area, rack_interval_ratio, temp_model,
                     export_lim, storage_capacity, scheduled_price,
                     data_tables, discount_rate)

# %% =====================================
# Optimise MAVs
importlib.reload(optimise)
rack_type = '5B_MAV'
scenario_tables_optimum_MAV, revenue_MAV, kWh_export_MAV = optimise.optimise_layout(weather_simulation, rack_type, module_type, install_year,
                     DCTotal, num_of_zones, zone_area, rack_interval_ratio, temp_model,
                     export_lim, storage_capacity, scheduled_price,
                     data_tables, discount_rate)


# Do Monte Carlo Analysis simultaneously

#%% ==========================================

# Transform two sets of scenario tables into a new set which includes both SAT and MAV (or more)
scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list = data_tables
SCNcostdata_SAT, SYScostdata_SAT = scenario_tables_optimum_SAT
SCNcostdata_MAV, SYScostdata_MAV = scenario_tables_optimum_MAV

SCNcostdata = SCNcostdata_SAT.append(SCNcostdata_MAV)
SYScostdata = SYScostdata_SAT.append(SYScostdata_MAV)

SYScostdata['ScenarioSystemID'] = range(0, SYScostdata.shape[0])

# Replacing some tables from specified inputs
new_data_tables = SCNcostdata, SYScostdata, system_list, system_component_link, component_list, currency_list, costcategory_list


# Call Monte Carlo Cost analysis
# Run iterative monte-carlo analysis for specified system
data_tables_iter = Suncost.create_iteration_tables(new_data_tables, 500, iteration_start=0)

outputs_iter = Suncost.CalculateScenariosIterations(data_tables_iter, year_start=2024, analyse_years=30)

component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, cash_flow_by_year_iter = outputs_iter

# Calculate LCOE and/or NPV for each iteration, and plot these for each optimum scenario.

# Calculate delta_LCOE and delta NPV for each iteration and plot this.
# Sensitivity analysis / regression analysis to determine key uncertainties affecting these.



# %% ==========================================================

# %%



# %%

# %% ==========================================================
# Present data from probabalistic analysis

cash_flow_transformed = pd.pivot_table(cash_flow_by_year_iter.reset_index(), columns='Iteration', index='Year')
revmax_direct = direct_revenue[racks_per_zone_max]
revmax_store = store_revenue[racks_per_zone_max]
revmax_total = total_revenue[racks_per_zone_max]
kWh_iter = kWh_discounted[racks_per_zone_max]
revmax_total_df = pd.DataFrame(revmax_total)
revenue_series_iter = sizing.align_cashflows(cash_flow_transformed, revmax_total_df)
npv_iter, yearly_npv_iter, npv_cost_iter, npv_revenue_iter, Yearly_NPV_revenue_iter, Yearly_NPV_costs_iter \
    = sizing.get_npv(cash_flow_transformed, revenue_series_iter, discount_rate)
LCOE_iter = npv_cost_iter/kWh_iter*100

filename = rack_type + ' ' + module_type + ' install_' + str(install_year)
npv_iter.to_csv('.\\Data\\OutputData\\' + filename + ' NPV.csv')
LCOE_iter.to_csv('.\\Data\\OutputData\\' + filename + ' LCOE.csv')

# Todo : In the future temperature (rack type) and aoi and single axis tracking (tracking algorithm)
# Todo : New algorithm will have more optimal tilt angle as well as better tracking
