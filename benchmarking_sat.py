""" This is the benchmarking script for DC yield assessment for SATs.
"""
# %% Import
import pandas as pd
import numpy as np
import simulation_functions as func
import sizing
import plotting as plot_func
import matplotlib.pyplot as plt
import matplotlib as mpl
# mpl.use('Qt5Agg')
# %%
# Weather adjustment between DNV weather files and Solcast Weather files

# DNV weather data don't have dni data but it has bhi (beam horizontal radiation: horizontal component of dni)
# We need the cos theta (zenith angle) to derive dni from bhi (dni is needed by pvlib simulations). We are going to
# extract the cost theta from Solcast weather files and use it in DNV weather data for the corresponding timestamps.
simulation_years = np.arange(2007, 2022, 1)
weather_file = 'Solcast_PT60M.csv'
weather_solcast = func.weather(simulation_years, weather_file)
weather_solcast.set_index(weather_solcast.index.tz_convert('Australia/Darwin'), inplace=True, drop=True)

# Choose which module to benchmark
module_rating = 570
# Choose the benchmark csv
spacing = '8m'
cell_type = 'mono'  # choose between mono or bifacial
weather_dnv_file = 'Combined_Longi_%d_Tracker-%s_FullTS_%s.csv' % (module_rating, cell_type, spacing)

# Complete set of dnv weather data you can extract specific years for simulations later on
weather_dnv = func.weather_benchmark_adjustment(weather_solcast, weather_dnv_file)
# %% ======================================
# Rack_module
rack_type = 'SAT_1'  # Choose rack_type from 5B_MAV or SAT_1 for maverick or single axis tracking respectively

if cell_type == 'bifacial':
      module_type = 'Longi LR5-72HBD-%dM' % module_rating  # Enter one of the modules from the SunCable module database
else:
      module_type = 'Longi LR5-72HBD-%dM_mono' % module_rating

rack_params, module_params = func.rack_module_params(rack_type, module_type)
# %%
# Benchmarking parameters according to DNV
DCTotal = 1000  # DC size in MW
num_of_zones = 167  # Number of smaller zones that will make up the solar farm
                    # (this is equal number of SMA MV 6000 stations)
gcr = [0.56 if spacing == '4m' else 0.45 if spacing == '5m' else 0.38 if spacing == '6m' else 0.32 if spacing == '7m' else 0.28][0]
# %% ========================================
# DC yield
temp_model = 'pvsyst'  # choose a temperature model either Sandia: 'sapm' or PVSyst: 'pvsyst'

# Choose 10 year benchmarking/simulation period
weather_simulation = weather_dnv['2010-01-01':'2020-12-31']
# In order for PV-lib to work properly the weather data's index/time format needs to be time zone aware. Otherwise, it
# takes it as UTC and gives incorrect results.
# So options for this:
weather_simulation.index = weather_simulation.index.tz_localize('Australia/Darwin')
# Or you can manually shift by weather_simulation = weather_simulation.shift(9)

dc_results = func.dc_yield_benchmarking_sat(DCTotal, rack_params, module_params, temp_model, weather_simulation, module_rating, gcr)
dc_results_dnv = weather_simulation['dc_yield'] * num_of_zones  # dnv gives dc yield per zone
#%% Plot features
font_size = 25
rc = {'font.size': font_size, 'axes.labelsize': font_size, 'legend.fontsize': font_size,
      'axes.titlesize': font_size, 'xtick.labelsize': font_size, 'ytick.labelsize': font_size}
plt.rcParams.update(**rc)
plt.rc('font', weight='bold')
# For label titles
fontdict = {'fontsize': font_size, 'fontweight': 'bold'}
#%% Line plot
# Choose different dates for plotting
date1 = '2018-10-01'
date2 = '2018-10-07'

fig, ax = plt.subplots(figsize=(25, 20))
ax.plot(dc_results[date1:date2]/1e9, linewidth=3, label='UNSW (PVlib/Python)')
ax.plot(dc_results_dnv[date1:date2]/1e9, linewidth=3, linestyle='--', label='DNV (PVsyst)')
ax.set_ylabel('Instantaneous DC power (GW) \n 1GW DC rated power)', **fontdict)
ax.legend()
# plt.show()
fig_name = 'DC yield benchmark_MAV_Oct2018'
save_path = "C:/Users/baran/UNSW/LCOE( ) tool Project - Documents/General/Figures/Benchmarking/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')
#%% Scatter Plot
scatter_year = 2020
x = dc_results[str(scatter_year)]/1e9
y = dc_results_dnv[str(scatter_year)]/1e9
fig, ax = plt.subplots(figsize=(25, 20))
ax.scatter(x, y)
ax.set_xlabel('UNSW (PVlib/Python) MAV DC yield (GW)', **fontdict)
ax.set_ylabel('DNV (PVsyst) MAV DC yield (GW)', **fontdict)
ax.set_title('DC yield benchmarking-%d'%scatter_year, **fontdict)

# Best fit line
m, b = np.polyfit(x, y, 1)
correlation_matrix = np.corrcoef(x.values, y.values)
correlation_xy = correlation_matrix[0,1]
r_squared = correlation_xy**2

ax.plot(dc_results/1e9, dc_results/1e9 * m + b, linewidth=3, color='C1')
ax.set_ylim(0,1.25)
ax.set_xlim(0,1.25)
plot_text = 'R-squared = %.2f' %r_squared
plt.text(0.3, 0.3, plot_text, fontsize=25)

#plt.show()
fig_name = 'Scatter_%d'%scatter_year
save_path = "C:/Users/baran/UNSW/LCOE( ) tool Project - Documents/General/Figures/Benchmarking/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')
#%% Bar plot
annual_yield_unsw = [dc_results[str(year)].sum()/1e9 for year in np.arange(2010, 2021)]
annual_yield_dnv = [dc_results_dnv[str(year)].sum()/1e9 for year in np.arange(2010, 2021)]
fig, ax = plt.subplots(figsize=(25, 20))
labels = np.arange(2010, 2021)
x = np.arange(11)

ax.bar(x, annual_yield_unsw, width=0.3, label='UNSW (PVlib/Python)')
ax.bar(x + 0.3, annual_yield_dnv, width=0.3, label='DNV (PVsyst)')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel('Annual DC yield (GWh) of 1GW DC rated solar farm', **fontdict)
ax.legend()

ax2 = ax.twinx()
dc_yield_diff = np.abs((np.array(annual_yield_unsw) - np.array(annual_yield_dnv))/annual_yield_unsw * 100)
ax2.plot(dc_yield_diff, linestyle='--', linewidth=3, color='black')
ax2.set_ylabel('DC yield difference in percentage (%)', **fontdict)
ax2.set_ylim(0,10)

# plt.show()
fig_name = 'Bar plot annual yield comparison'
save_path = "C:/Users/baran/UNSW/LCOE( ) tool Project - Documents/General/Figures/Benchmarking/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')
