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
# mpl.use('Qt5Agg')

# TODO: OPTIMISATION FOR MAVS (FIXED EXPORT LIMIT 3.3 GW) CHANGE SIZE TO SEE THE NPV & LCOE.
# %%
# Weather
simulation_years = [2019]
weather_file = 'Solcast_PT60M.csv'
weather_simulation = func.weather(simulation_years, weather_file)

# %% ======================================
# Rack_module
rack_type = 'SAT_1'  # Choose rack_type from 5B_MAV or SAT_1 for maverick or single axis tracking respectively
module_type = 'LPERC_2023_M10'  # Enter one of the modules from the SunCable module database
rack_params, module_params = func.rack_module_params(rack_type, module_type)

# %%
# Sizing/rack and module numbers
# Call the constants from the database - unneeded if we just pass module class?
DCTotal = 11000  # DC size in MW
num_of_zones = 267  # Number of smaller zones that will make up the solar farm
zone_area = 4e5   # Zone Area in m2
rack_interval_ratio = 0.04
rack_per_zone_num_range, module_per_zone_num_range, gcr_range = func.get_racks(DCTotal, num_of_zones, module_params,
                                                                             rack_params, zone_area, rack_interval_ratio)
# %% ========================================
# DC yield
temp_model = 'sapm'  # choose a temperature model either Sandia: 'sapm' or PVSyst: 'pvsyst'
dc_results, dc_df, dc_size = func.dc_yield(DCTotal, rack_params, module_params, temp_model, weather_simulation,
                                           rack_per_zone_num_range, module_per_zone_num_range, gcr_range, num_of_zones)

if rack_type == '5B_MAV':
    annual_yield = np.array([y.sum()/1e9 for y in dc_results]) # annual yield in GWh
    annual_yield_mav = annual_yield.copy()
else:
    annual_yield = np.array([y.sum()/1e9 for y in dc_results])  # annual yield in GWh
    annual_yield_per_module = annual_yield * 1e6 / module_per_zone_num_range / num_of_zones  # annual yield per module in kWh
    annual_yield_sat = annual_yield.copy()

#%% Plotting

# Un hash the lines below for desired plots...

# plot_func.plot_yield(annual_yield_sat, annual_yield_mav, gcr_range, DCTotal, dc_size)
# plot_func.plot_yield_per_module(annual_yield_sat, module_per_zone_num_range, num_of_zones, gcr_range)
# plot_func.plot_temp_models(annual_yield_sapm, annual_yield_pvsyst, dc_size)  # run simulations with sapm, and pvsyst
# and assign to annual_yield_sapm and annual_yield_pvsyst respectively for this line to work

# fig_name =  #  enter the figure name
# save_path = "C:/Users/baran/cloudstor/SunCable/Figures/"+ figname
# plot_func.plot_save(fig_name, save_path)
#%% ==========================================
# Revenue and storage behaviour
export_lim = 3.2e9/num_of_zones
storage_capacity = 4e7
scheduled_price = 0.00004  # 4c/kWh (conversion from Wh to kWh)
direct_revenue, store_revenue, total_revenue = sizing.get_revenue(dc_df, export_lim, scheduled_price, storage_capacity)
    #%% ==========================================
# Cost
data_tables = sizing.get_airtable()
cost_outputs = sizing.get_costs(rack_per_zone_num_range, rack_params, module_params, data_tables)
component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = cost_outputs
#%% ==========================================
# Net present value (NPV)
# resize yield output to match cost time series
revenue_series = sizing.align_cashflows(cash_flow_by_year, total_revenue)

# ==========================================
npv, yearly_npv, npv_cost, npv_revenue, Yearly_NPV_revenue, Yearly_NPV_costs = sizing.get_npv(cash_flow_by_year, revenue_series)

# %% =======================================
# Simulations to find optimum NPV according to number of racks per zone

rack_interval = rack_per_zone_num_range[2]-rack_per_zone_num_range[1]
num_of_zones_sim = 1  # find the results per zone for now
scheduled_price = 0.00004
npv_array = []
npv_cost_array = []
npv_revenue_array = []
gcr_range_array = []
rack_per_zone_num_range_array = []
iteration = 1

while rack_interval > 1:
    print('Max NPV is %d' % npv.max())
    print('Iteration = %d' % iteration)
    npv_array.append(npv)
    npv_cost_array.append(npv_cost)
    npv_revenue_array.append(npv_revenue)
    gcr_range_array.append(gcr_range)
    rack_per_zone_num_range_array.append(rack_per_zone_num_range)
    index_max = npv.idxmax()
    DCpower_min = index_max * rack_params['Modules_per_rack'] * module_params['STC'] / 1e6
    new_interval_ratio = rack_interval / index_max / 5
    if index_max == npv.index[0] or index_max == npv.index[10]:
        new_interval_ratio = 0.04

    rack_per_zone_num_range, module_per_zone_num_range, gcr_range = func.get_racks(DCpower_min, num_of_zones_sim,
                                                                                   module_params, rack_params, zone_area,
                                                                                   new_interval_ratio)
    rack_interval = rack_per_zone_num_range[2] - rack_per_zone_num_range[1]
    dc_results, dc_df, dc_size = func.dc_yield(DCpower_min, rack_params, module_params, temp_model, weather_simulation,
                                               rack_per_zone_num_range, module_per_zone_num_range, gcr_range,
                                               num_of_zones)
    direct_revenue, store_revenue, total_revenue = sizing.get_revenue(dc_df, export_lim, scheduled_price, storage_capacity)
    cost_outputs = sizing.get_costs(rack_per_zone_num_range, rack_params, module_params, data_tables)
    component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = cost_outputs
    revenue_series = sizing.align_cashflows(cash_flow_by_year, total_revenue)
    npv, yearly_npv, npv_cost, npv_revenue, Yearly_NPV_revenue, Yearly_NPV_costs = sizing.get_npv(cash_flow_by_year, revenue_series)
    iteration += 1
    if iteration >= 11:
        break
# %% ==========================================
# Plotting NPV, GCR_range, NPV_cost, NPV_revenue
plot_func.plot_npv(rack_per_zone_num_range_array, npv_array, gcr_range_array, npv_cost_array, npv_revenue_array)
# %% ==========================================================
# Perform probabalistic analysis: Part 1 - Costs
racks_per_zone_max = npv.idxmax()
rpzm_series = pd.Series(racks_per_zone_max)
component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, cash_flow_by_year_iter, data_tables_iter \
    = sizing.get_mcanalysis(rpzm_series, rack_params, module_params, data_tables)


# %% ==========================================================
# Present data from probabalistic analysis

cash_flow_transformed = pd.pivot_table(cash_flow_by_year_iter.reset_index(), columns='Iteration', index='Year')
revmax_direct = direct_revenue[racks_per_zone_max]
revmax_store = store_revenue[racks_per_zone_max]
revmax_total = total_revenue[racks_per_zone_max]
revmax_total_df = pd.DataFrame(revmax_total)
revenue_series_iter = sizing.align_cashflows(cash_flow_transformed, revmax_total_df)
npv_iter, yearly_npv_iter, npv_cost_iter, npv_revenue_iter, Yearly_NPV_revenue_iter, Yearly_NPV_costs_iter \
    = sizing.get_npv(cash_flow_transformed, revenue_series_iter)

filename = rack_type + ' ' + module_type
npv_iter.to_csv('.\\Data\\OutputData\\' + filename + '.csv')

# Todo : In the future temperature (rack type) and aoi and single axis tracking (tracking algorithm)
# Todo : New algorithm will have more optimal tilt angle as well as better tracking
