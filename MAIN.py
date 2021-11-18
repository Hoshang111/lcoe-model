""" This is the main script for the yield assessment. The script calls the functions below to calculate the Net Present Value
(NPV) of the solar farm

1) Sizing
Input: DC size of the solar farm
Output: Configuration in terms of number of single-axis tracking (SAT) racks or 5B Maverick units (MAV)

2) Weather:
Input: Weather file, year of simulation
Output: Weather dataframe in the required format for PVlib simulatins

3) Racks & modules:
Input: Type of module and rack
Output: Module and rack parameters required for PVlib PVsystem extracted from the module & rack database

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
import PyQt5
import matplotlib as mpl
import matplotlib.pyplot as plt

# mpl.use('Qt5Agg')
# mpl.use('TkAgg')


# ================== Global parameters for fonts & sizes =================
font_size = 30
rc = {'font.size': font_size, 'axes.labelsize': font_size, 'legend.fontsize': font_size,
      'axes.titlesize': font_size, 'xtick.labelsize': font_size, 'ytick.labelsize': font_size}
plt.rcParams.update(**rc)
plt.rc('font', weight='bold')

# For label titles
fontdict = {'fontsize': font_size, 'fontweight': 'bold'}
# can add in above dictionary: 'verticalalignment': 'baseline'

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
    annual_yield = dc_results.sum()/1e9  # annual yield in GWh
    annual_yield_mav = annual_yield.copy()
else:
    annual_yield = np.array([y.sum()/1e9 for y in dc_results])  # annual yield in GWh
    annual_yield_per_module = annual_yield * 1e6 / module_per_zone_num_range / num_of_zones  # annual yield per module in kWh
    annual_yield_sat = annual_yield.copy()

# %% =========================================
# Assign the results of sat to annual_yield_sat and assign the results of mav to annual_yield_mav


# Plotting
fig, ax = plt.subplots(figsize=(25, 20))
labels = round(gcr_range, 2)
x = np.arange(11)
ax.bar(x, annual_yield_sat, label='SAT')
ax.bar(x[-1] + 1, annual_yield_mav, label='MAV')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel('Annual yield (GWh)', **fontdict)
ax.set_xlabel('Ground coverage ratio (GCR)', **fontdict)
ax.grid(b=True, which='major', color='gray', linestyle='-')
ax.legend()

ax2 = ax.twinx()
ax2.plot(dc_size, '*-', color= 'red')
ax2.set_ylabel('DC rated of the system (MW)', **fontdict)
ax2.set_ylim(DCTotal*0.6, DCTotal*1.4)
# dc_size.append(DCTotal)
plt.show()

# %%
# Plotting per module output for SAT
fig, ax = plt.subplots(figsize=(25, 20))
labels = round(gcr_range, 2)
x = np.arange(11)
ax.bar(x, annual_yield_sat/module_per_zone_num_range/num_of_zones * 1e6, label='SAT')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel('Annual yield per module(kWh)', **fontdict)
ax.set_xlabel('Ground coverage ratio (GCR)', **fontdict)
ax.grid(b=True, which='major', color='gray', linestyle='-')
ax.legend()
# ax.set_ylabel()

plt.show()
# %%
# Plotting performance difference between temperature models

fig, ax = plt.subplots(figsize=(25, 20))
x = np.arange(2)
ax.bar(x, [annual_yield_sapm, annual_yield_pvsyst])
ax.set_xticks(x)
ax.set_xticklabels(['Sandia', 'PVSyst'], **fontdict)
ax.set_ylabel('Annual yield (GWh)', **fontdict)
ax.text(x[0], annual_yield_sapm + 50, str(np.round(annual_yield_sapm,0)))
ax.text(x[1], annual_yield_pvsyst + 50, str(np.round(annual_yield_pvsyst,0)))
ax.set_title('Annual yield for 1GW east-west calculated with different temperature models', **fontdict)
plt.show()

# %%
figname='Annual yield comparison_with size'
path="C:/Users/baran/UNSW/LCOE( ) tool Project - Documents/General/Figures" + figname
# path="C:/Users/baran/cloudstor/SunCable/Figures/"+ figname
plt.savefig(path, dpi=300, bbox_inches='tight')

#%% ==========================================
# Revenue and storage behaviour
export_lim = 3.2e9/num_of_zones
storage_capacity = 4e7
direct_revenue, store_revenue, total_revenue = sizing.get_revenue(dc_df, export_lim, 0.00004, storage_capacity)

#%% ==========================================
# Cost
cost_outputs = sizing.get_costs(rack_per_zone_num_range, rack_params, module_params)
component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = cost_outputs

#%% ==========================================
# Net present value (NPV)
# resize yield output to match cost time series

revenue_series = sizing.align_cashflows(cash_flow_by_year, total_revenue)

# ==========================================
npv, yearly_npv, npv_cost, npv_revenue = sizing.get_npv(cash_flow_by_year, revenue_series)


#%% ==========================================
# find minimum npv and grid search

rack_interval = rack_per_zone_num_range[2]-rack_per_zone_num_range[1]
fig, (ax1, ax2, ax3) = plt.subplots(1, 3)

while rack_interval > 1:
    print(npv)
    ax1.scatter(rack_per_zone_num_range, npv)
    ax2.scatter(rack_per_zone_num_range, gcr_range)
    ax3.scatter(rack_per_zone_num_range, npv_cost)
    ax3.scatter(rack_per_zone_num_range, npv_revenue)
    index_max = npv.idxmax()
    DCpower_min = index_max * rack_params['Modules_per_rack'] * module_params['STC'] / 1e6
    new_interval_ratio = rack_interval / index_max / 5
    if index_max == npv.index[0] or index_max == npv.index[10]:
        new_interval_ratio = 0.04

    rack_per_zone_num_range, module_per_zone_num_range, gcr_range = func.get_racks(DCpower_min, 1,
                                                                 module_params, rack_params,
                                                                 zone_area, new_interval_ratio)
    rack_interval = rack_per_zone_num_range[2] - rack_per_zone_num_range[1]
    dc_results, dc_df, dc_size = func.dc_yield(DCpower_min, rack_params, module_params, temp_model, weather_simulation,
                                               rack_per_zone_num_range, module_per_zone_num_range, gcr_range,
                                               num_of_zones)
    direct_revenue, store_revenue, total_revenue = sizing.get_revenue(dc_df, export_lim, 0.00004, storage_capacity)
    cost_outputs = sizing.get_costs(rack_per_zone_num_range, rack_params, module_params)
    component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = cost_outputs
    revenue_series = sizing.align_cashflows(cash_flow_by_year, total_revenue)
    npv, yearly_npv, npv_cost, npv_revenue = sizing.get_npv(cash_flow_by_year, revenue_series)

plt.show()
# Todo : In the future temperature (rack type) and aoi and single axis tracking (tracking algorithm)
# Todo : New algorithm will have more optimal tilt angle as well as better tracking