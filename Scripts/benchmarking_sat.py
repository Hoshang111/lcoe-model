""" This is the benchmarking script for DC yield assessment for SATs.
"""
# %% Import
import pandas as pd
import numpy as np
from Functions import simulation_functions as func
import matplotlib.pyplot as plt
import os
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

# Chwoose which module to benchmark
module_rating = 545
# Choose the benchmark csv
spacing = '8m'
cell_type = 'bifacial'  # choose between mono or bifacial
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
weather_simulation_dnv = weather_dnv['2010-01-01':'2020-12-31']
weather_simulation_solcast = weather_solcast['2010-01-01':'2020-12-31']
# In order for PV-lib to work properly the weather data's index/time format needs to be time zone aware. Otherwise, it
# takes it as UTC and gives incorrect results.
# So options for this:

weather_simulation_dnv.index = weather_simulation_dnv.index.tz_localize('Australia/Darwin')
# Todo : Below command ends up shifting the tstamp by half hour
#  (working in conjunction with the function in simulation_functions). This is due to one tstamp in UTC and other in
#  local. Can make further improvements for this part.
weather_simulation_solcast.index = weather_simulation_solcast.index.tz_localize('Australia/Darwin')
#%% Now create a new weather data for DNV with simulated dni and simulate with this weather data...
parent_path = os.path.dirname('.')
dni_dummy = pd.read_csv(os.path.join(parent_path, 'Data', 'WeatherData', 'dni_simulated.csv'), index_col=0)
dni_dummy.set_index(pd.to_datetime(dni_dummy.index, utc=False), drop=True, inplace=True)
dni_dummy.index = dni_dummy.index.tz_convert('Australia/Darwin')

weather_simulation_dnv.drop(['dni'],axis=1,inplace=True)
weather_simulation_dnv = weather_simulation_dnv.join(dni_dummy, how='left')
weather_simulation_dnv.rename(columns={"0": "dni"}, inplace=True)
weather_simulation_dnv = weather_simulation_dnv[['ghi','dni','dhi','temp_air','wind_speed','precipitable_water','dc_yield']]
weather_simulation_mod = weather_simulation_dnv.shift(periods=30, freq='T')
#%%
# Because of the lack of DNI data in DNV files and since SAT is quite sensitive to DNI, instead of stitching up DNI to
# DNV weather files, we will use Solcast weather for the simulations (this gives more consistent and sensible SAT output)
dc_results_unaligned, mc, mount = func.dc_yield_benchmarking_sat(DCTotal, rack_params, module_params, temp_model, weather_simulation_mod,
                                            module_rating, gcr, cell_type=cell_type)
dc_results = dc_results_unaligned.shift(periods=-30, freq='T')
dc_results_dnv = weather_simulation_dnv['dc_yield'] * num_of_zones  # dnv gives dc yield per zone
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
date1 = '2018-10-15'
date2 = '2018-10-22'
month = pd.to_datetime(date1).month

fig, ax = plt.subplots(figsize=(25, 20))
ax.plot(dc_results[date1:date2]/1e9, linewidth=3, label='UNSW (PVlib/Python)')
ax.plot(dc_results_dnv[date1:date2]/1e9, linewidth=3, linestyle='--', label='DNV (PVsyst)')
ax.set_ylabel('Instantaneous DC power (GW) \n 1GW DC rated power)', **fontdict)
ax.legend()
# plt.show()
fig_name = 'LinePlot-%s-%s-%d-%d' %(rack_type,cell_type,module_rating,month)

save_path = "C:/Users/phill/documents/suncable/figures/benchmarking/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')

#%% Scatter Plot
scatter_year = 2017
x = dc_results[str(scatter_year)]/1e9
y = dc_results_dnv[str(scatter_year)]/1e9
fig, ax = plt.subplots(figsize=(25, 20))
ax.scatter(x, y)
ax.set_xlabel('UNSW (PVlib/Python) SAT DC yield (GW)', **fontdict)
ax.set_ylabel('DNV (PVsyst) SAT DC yield (GW)', **fontdict)
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
fig_name = 'Scatter-%s-%s-%d-%d' %(rack_type,cell_type,module_rating,scatter_year)
save_path = "C:/Users/phill/documents/suncable/figures/benchmarking/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')

#%% bar plot
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

#plt.show()
fig_name = 'Bar-%s-%s-%d' %(rack_type,cell_type,module_rating)
save_path = "C:/Users/phill/documents/suncable/figures/benchmarking/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')