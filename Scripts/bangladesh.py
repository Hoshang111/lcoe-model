""" This is the benchmarking script for DC yield assessment for 5B MAVs.
"""
# %% Import
import sys
sys.path.append('../')
import pandas as pd
import numpy as np
import Functions.simulation_functions as func
import matplotlib.pyplot as plt
import os
import warnings
from pvlib.location import Location

# mpl.use('Qt5Agg')

# %%
# Weather adjustment between DNV weather files and Solcast Weather files

# DNV weather data don't have dni data but it has bhi (beam horizontal radiation: horizontal component of dni)
# We need the cos theta (zenith angle) to derive dni from bhi (dni is needed by pvlib simulations). We are going to
# extract the cost theta from Solcast weather files and use it in DNV weather data for the corresponding timestamps.
warnings.simplefilter(action='ignore', category=FutureWarning)

data_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data\Matarbari_tmy_2020.csv"
weather = pd.read_csv(data_path, skiprows=1, header=1)
weather.index = pd.to_datetime(weather[['Year', 'Month', 'Day', 'Hour', 'Minute']])
weather = weather.rename(columns={'GHI':'ghi', 'DNI':'dni', 'DHI': 'dhi', 'Temperature':'temp_air',
                                  'Precipitable Water':'precipitable_water', 'Wind speed':'wind_speed'})
weather.drop(columns=['Year', 'Month', 'Day', 'Hour', 'Minute'], inplace=True)

# %% ======================================
# Get headline numbers

# %% ======================================
# Rack_module
rack_type = '5B_MAV'  # Choose rack_type from 5B_MAV or SAT_1 for maverick or single axis tracking respectively
module_type = 'Longi LR5-72HBD-570M_mono'  # Enter one of the modules from the SunCable module database
rack_params, module_params = func.rack_module_params(rack_type, module_type)

# %% ========================================
# Location data
coordinates = [(21.986667, 90.241667, 'Patuakhali', 00, 'Asia/Dhaka')]  # Coordinates of the solar farm
latitude, longitude, name, altitude, timezone = coordinates[0]
location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)
acre2m = 4046.86
land_area = 400*acre2m

# %% ========================================
# DC yield
temp_model = 'pvsyst'  # choose a temperature model either Sandia: 'sapm' or PVSyst: 'pvsyst'



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
date1 = '2018-7-15'
date2 = '2018-7-22'
month = pd.to_datetime(date1).month

fig, ax = plt.subplots(figsize=(25, 20))
ax.plot(dc_results[date1:date2]/1e9, linewidth=3, label='UNSW (PVlib/Python)')
ax.plot(dc_results_dnv[date1:date2]/1e9, linewidth=3, linestyle='--', label='DNV (PVsyst)')
ax.set_ylabel('Instantaneous DC power (GW) \n 1GW DC rated power)', **fontdict)
ax.legend()
# plt.show()
fig_name = 'LinePlot-%s-%d-%d' %(rack_type,module_rating,month)

save_path = "C:/Users/phill/documents/suncable/figures/benchmarking/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')

#%% Scatter Plot
scatter_year = 2020
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
fig_name = 'Scatter-%s-%d-%d' %(rack_type,module_rating,scatter_year)
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
fig_name = 'Bar-%s-%d' %(rack_type,module_rating)
save_path = "C:/Users/phill/documents/suncable/figures/benchmarking/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')

#%% Generate Report for Comparison

global_horizontal = weather_simulation_mod.groupby(weather_simulation_mod.index.year)['ghi'].sum()
global_incident_east = mc.results.total_irrad[0].groupby(mc.results.total_irrad[0].index.year)['poa_global'].sum()
global_incident_east = global_incident_east.rename('poa_global_east')
global_incident_west = mc.results.total_irrad[1].groupby(mc.results.total_irrad[0].index.year)['poa_global'].sum()
global_incident_west = global_incident_west.rename('poa_global_west')
DC_output = dc_results.groupby(dc_results.index.year).sum()/1e3
DC_output = DC_output.rename('kWh_DC')
performance_ratio = DC_output/(global_incident_east+global_incident_west)/5e2
performance_ratio = performance_ratio.rename('PR')

summary_df = pd.DataFrame([global_horizontal, global_incident_east, global_incident_west,
                           DC_output, performance_ratio])
summary_df = summary_df.transpose()
save_path = "C:/Users/phill/documents/suncable/figures/benchmarking/summary.csv"
summary_df.to_csv(save_path)

timeseries_output = mc.results.weather
cell_temp_east = mc.results.cell_temperature[0]
cell_temp_east = cell_temp_east.rename('cell_temp_east')
cell_temp_west = mc.results.cell_temperature[1]
cell_temp_west = cell_temp_west.rename('cell_temp_west')
dc_results_unaligned = dc_results_unaligned.rename('Power (W)')
dc_results_east = mc.results.dc[0]
dc_results_east = dc_results_east.rename(columns={'i_sc':'i_sc_east', 'v_oc':'v_oc_east', 'i_mp':'i_mp_east',
                                                  'v_mp':'v_mp_east', 'p_mp':'p_mp_east', 'i_x':'i_x_east', 'i_xx':'i_xx_east'})
dc_results_west = mc.results.dc[1]
dc_results_west = dc_results_west.rename(columns={'i_sc':'i_sc_west', 'v_oc':'v_oc_west', 'i_mp':'i_mp_west',
                                                  'v_mp':'v_mp_west', 'p_mp':'p_mp_west', 'i_x':'i_x_west', 'i_xx':'i_xx_west'})
irradiance_east = mc.results.total_irrad[0]
irradiance_east = irradiance_east.rename(columns={'poa_global':'poa_global_east', 'poa_direct':'poa_direct_east',
                                                  'poa_diffuse':'poa_diffuse_east', 'poa_sky_diffuse':'poa_sky_diffuse_east',
                                                  'poa_ground_diffuse':'poa_ground_diffuse_east'})
irradiance_west = mc.results.total_irrad[1]
irradiance_west = irradiance_west.rename(columns={'poa_global':'poa_global_west', 'poa_direct':'poa_direct_west',
                                                  'poa_diffuse':'poa_diffuse_west', 'poa_sky_diffuse':'poa_sky_diffuse_west',
                                                  'poa_ground_diffuse':'poa_ground_diffuse_west'})
timeseries_output = timeseries_output.join([dc_results_unaligned, dc_results_east, cell_temp_east, irradiance_east,
                                            dc_results_west, cell_temp_west, irradiance_west], how='left')
timeseries_output = timeseries_output.shift(periods=-30, freq='T')
save_path = "C:/Users/phill/documents/suncable/figures/benchmarking/timeseries.csv"
timeseries_output.to_csv(save_path)