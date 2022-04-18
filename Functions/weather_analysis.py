import pandas as pd
import numpy as np
import os
import datetime as dt
import matplotlib as plt

data_path = "D:/Bangladesh Application/weather_data/"
ground_path = os.join(data_path, "feni_ground_measurements")
ground_data = pd.read_csv(ground_path, index_col=0)
ground_data.set_index(pd.to_datetime(ground_data.index, inplace=True))

satellite_path = os.join(data_path, "ninja_feni_joined")
satellite_data = pd.read_csv(satellite_path, index_col=0)
satellite_data.set_index(pd.to_datetime(satellite_data.index, inplace=True))

# satellite_data_aligned =
ground_data_hourly = ground_data.groupby(ground_data.index.dt.hour).sum()
ground_data_aligned = ground_data_hourly.reindex_like(satellite_data)

ground_dhi = ground_data_aligned['DHI_ThPyra2_Wm-2_avg']
ground_ghi = ground_data_aligned['GHI_ThPyra1_Wm-2_avg']

satellite_dhi = satellite_data['irradiance_diffuse']
satellite_ghi = satellite_data['irradiance_total']

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
ax.plot(ground_ghi[date1:date2], linewidth=3, label='UNSW (PVlib/Python)')
ax.plot(satellite_ghi[date1:date2], linewidth=3, linestyle='--', label='DNV (PVsyst)')
ax.set_ylabel('GHI', **fontdict)
ax.legend()
# plt.show()
fig_name = 'LinePlot-Feni_GHI'

save_path = "D:/Bangladesh Application/weather_data/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')

#%% Scatter Plot
scatter_year = 2020
x = satellite_ghi[str(scatter_year)]/1e9
y = ground_ghi[str(scatter_year)]/1e9
fig, ax = plt.subplots(figsize=(25, 20))
ax.scatter(x, y)
ax.set_xlabel('Satellite GHI', **fontdict)
ax.set_ylabel('Ground GHI', **fontdict)
ax.set_title('Weather Correction'%scatter_year, **fontdict)

# Best fit line
m, b = np.polyfit(x, y, 1)
correlation_matrix = np.corrcoef(x.values, y.values)
correlation_xy = correlation_matrix[0,1]
r_squared = correlation_xy**2

ax.plot(satellite_ghi, ground_ghi * m + b, linewidth=3, color='C1')
ax.set_ylim(0,1.25)
ax.set_xlim(0,1.25)
plot_text = 'R-squared = %.2f' %r_squared
plt.text(0.3, 0.3, plot_text, fontsize=25)

#plt.show()
fig_name = 'Scatter-2020_GHI'
save_path = "D:/Bangladesh Application/weather_data/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')

#%% bar plot
satellite_results = [satellite_ghi[str(month)].sum() for month in np.arange(2018, 2020)]
ground_results = [ground_ghi[str(month)].sum() for month in np.arange(2018, 2020)]
fig, ax = plt.subplots(figsize=(25, 20))
labels = np.arange(2010, 2021)
x = np.arange(11)

ax.bar(x, satellite_results, width=0.3, label='satellite')
ax.bar(x + 0.3, ground_results, width=0.3, label='ground')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel('monthly ghi', **fontdict)
ax.legend()

ax2 = ax.twinx()
dc_yield_diff = np.abs((np.array(satellite_results) - np.array(ground_results))/satellite_results * 100)
ax2.plot(dc_yield_diff, linestyle='--', linewidth=3, color='black')
ax2.set_ylabel('GHI difference in percentage (%)', **fontdict)
ax2.set_ylim(0,10)

#plt.show()
fig_name = 'Bar-Feni_GHI'
save_path = "D:/Bangladesh Application/weather_data/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')