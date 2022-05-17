import pandas as pd
import numpy as np
import os
import datetime as dt
import matplotlib.pyplot as plt
import pickle


#%% import ground and satellite data

data_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data"
ground_path = os.path.join(data_path, "ground_measurements_feni.csv")
ground_data_a = pd.read_csv(ground_path, index_col=0, header=1)
ground_data_a.set_index(pd.to_datetime(ground_data_a.index), inplace=True)
ground_data_a = ground_data_a.rename(columns = {'DHI_ThPyra2_Wm-2_avg':'dhi',
                                                 'GHI_ThPyra1_Wm-2_avg':'ghi',
                                                 'DNI_ThPyrh1_Wm-2_avg':'dni',
                                                 'Temp_ThPyra1_degC_avg':'temp',
                                                 'WindSpeed_Anemo1_ms_avg':'wind_speed',
                                                  'RH_ThHyg1_per100_avg':'relative_humidity'})
ground_data = ground_data_a.tz_localize("UTC")

# satellite_path = os.path.join(data_path, "PVGIS_2017_2020.csv")
# satellite_data = pd.read_csv(satellite_path, index_col=0, header=0)
# satellite_data.set_index(pd.to_datetime(satellite_data.index, format='%Y%m%d:%H%M'), inplace=True)

satellite_data_2017_path = os.path.join(data_path, "Himawari_2017.csv")
satellite_data_2018_path = os.path.join(data_path, "Himawari_2018.csv")
satellite_data_2019_path = os.path.join(data_path, "Himawari_2019.csv")
satellite_data_2017 = pd.read_csv(satellite_data_2017_path, header=2)
satellite_data_2018 = pd.read_csv(satellite_data_2018_path, header=2)
satellite_data_2019 = pd.read_csv(satellite_data_2019_path, header=2)
satellite_data_2017.set_index(pd.to_datetime(satellite_data_2017[["Year", "Month", "Day", "Hour", "Minute"]]), inplace=True)
satellite_data_2018.set_index(pd.to_datetime(satellite_data_2018[["Year", "Month", "Day", "Hour", "Minute"]]), inplace=True)
satellite_data_2019.set_index(pd.to_datetime(satellite_data_2019[["Year", "Month", "Day", "Hour", "Minute"]]), inplace=True)
satellite_data_localtz = pd.concat([satellite_data_2017, satellite_data_2018, satellite_data_2019], axis=0)
satellite_data_aware = satellite_data_localtz.tz_localize("Asia/Dhaka")
satellite_data = satellite_data_aware.tz_convert("UTC")
satellite_data = satellite_data.rename(columns={'GHI':'ghi',
                                                'DHI':'dhi',
                                                'DNI':'dni',
                                                'Temperature':'temp',
                                                'Wind Speed':'wind_speed'})

#%% Align Data
# satellite_data_aligned =
ground_data_mod = ground_data.shift(periods=5, freq='T')
ground_data_hourly = ground_data_mod.resample('10T', axis=0).mean()
# ground_data_hourly = ground_data_hourlyA.shift(periods=-5, freq='T')
satellite_data_aligned = satellite_data.reindex(ground_data_hourly.index)

ground_dhi = ground_data_hourly['dhi']
ground_ghi = ground_data_hourly['ghi']

satellite_dhi = satellite_data_aligned['dhi']
satellite_ghi = satellite_data_aligned['ghi']

#%% Group by month

def weather_sort(weather_file):
      """

      :param weather_file:
      :return:
      """

      weather_monthly = weather_file.groupby(weather_file.index.month)
      weather_list = [group for _, group in weather_monthly]
      months_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
      weather = {}

      for i in range(len(months_list)):
            weather[months_list[i]] = {}
            unsorted_data = weather_list[i]
            split_data = unsorted_data.groupby(unsorted_data.index.year)
            unsorted_list = [group for _, group in split_data]
            sorted_list = sorted(unsorted_list, key=lambda x: x['ghi'].sum())
            for j in range(len(sorted_list)):
                  weather[months_list[i]][j] = sorted_list[j]

      return weather

ground_weather_sorted = weather_sort(ground_data_hourly)
satellite_weather_sorted = weather_sort(satellite_data)

#%% pickle data for use elsewhere
save_path = os.path.join(data_path, "ground_weather.p")
pickle.dump(ground_weather_sorted, open(save_path, "wb"))

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
ax.plot(ground_ghi[date1:date2], linewidth=3, label='ground data')
ax.plot(satellite_ghi[date1:date2], linewidth=3, linestyle='--', label='satellite data')
ax.set_ylabel('GHI', **fontdict)
ax.legend()
# plt.show()
fig_name = 'LinePlot-Feni_GHI'

save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.clf()

#%% Initial scatter plot

# scatter plot for uncorrected data with linear fit

def weather_scatter(ground, satellite, fig_name):
    """"""

    x = satellite
    y = ground
    fig, ax = plt.subplots(figsize=(25, 20))
    ax.scatter(x, y)
    ax.set_xlabel('Satellite', **fontdict)
    ax.set_ylabel('Ground', **fontdict)
    ax.set_title(fig_name)

    # Best fit line - edit changed to second order
    # m, b = np.polyfit(x, y, 1)
    c2, c1, c0 = np.polyfit(x, y, 2)
    correlation_matrix = np.corrcoef(x.values, y.values)
    correlation_xy = correlation_matrix[0, 1]
    r_squared = correlation_xy ** 2

    ax.plot(x, x * x * c2 + x * c1 + c0, linewidth=3, color='C1')
    # ax.set_ylim(0,1.25)
    # ax.set_xlim(0,1.25)
    plot_text = 'R-squared = %.2f' % r_squared
    plt.text(0.3, 0.3, plot_text, fontsize=25)

    # plt.show()
    save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/" + fig_name
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return c0, c1, c2

c0_init, c1_init, c2_init = weather_scatter(ground_ghi, satellite_ghi, 'Uncorrected_Full')

#%% Comparing and correcting satellite file

def weather_compare(ground_file, satellite_file):
      """"""
      satellite_file_aligned = satellite_file.reindex(ground_file.index)
      satellite_monthly = satellite_file_aligned.groupby(satellite_file_aligned.index.month)
      ground_monthly = ground_file.groupby(ground_file.index.month)
      satellite_list = [group for _, group in satellite_monthly]
      ground_list = [group for _, group in ground_monthly]
      months_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
      satellite_dict = {}
      ground_dict = {}

      for i in range(len(months_list)):
          ground_dict[months_list[i]] = {}
          satellite_dict[months_list[i]] = {}
          unsorted_data = ground_list[i]
          split_data = unsorted_data.groupby(unsorted_data.index.year)
          ground_unsorted = [group for _, group in split_data]
          unsorted_data = satellite_list[i]
          split_data = unsorted_data.groupby(unsorted_data.index.year)
          satellite_unsorted = [group for _, group in split_data]

          for j in range(len(ground_unsorted)):
              ground_dict[months_list[i]][j] = ground_unsorted[j]
              satellite_dict[months_list[i]][j] = satellite_unsorted[j]

      return ground_dict, satellite_dict

def weather_correction(ground, satellite, parameter_key, month):
    """"""

    fig_name = 'Uncorrected_' + parameter_key + '_' + month
    c0, c1, c2 = weather_scatter(ground[parameter_key], satellite[parameter_key], fig_name)

    satellite_dummy = satellite[parameter_key] ** 2 * c2 + satellite[parameter_key] * c1 + c0
    satellite_corr = satellite_dummy.clip(lower=0, upper=None)

    # re-plot with corrected data
    fig_name = 'Corrected_' + parameter_key + '_' + month
    c0_a, c1_a, c2_a = weather_scatter(ground[parameter_key], satellite_corr, fig_name)

    return c0, c1, c2, satellite_corr

ground_dict, satellite_dict = weather_compare(ground_data_hourly, satellite_data)
months_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

ground_concat = {}
satellite_concat = {}
correction_factors = {}
satellite_corrected = {}

for month in months_list:
    ground_concat_dummy = pd.concat(ground_dict[month], axis=0)
    ground_concat[month] = ground_concat_dummy.droplevel(level=0)
    satellite_concat_dummy = pd.concat(satellite_dict[month], axis=0)
    satellite_concat[month] = satellite_concat_dummy.droplevel(level=0)
    c0, c1, c2, satellite_corrected[month] = weather_correction(ground_concat[month], satellite_concat[month], 'ghi', month)
    correction_factors[month] = [c0, c1, c2]

satellite_corrected_dummy = pd.concat(satellite_corrected, axis=0)
satellite_corrected_full = satellite_corrected_dummy.droplevel(level=0)
satellite_corrected_series = satellite_corrected_full.sort_index()

c0_final, c1_final, c2_final = weather_scatter(ground_ghi, satellite_corrected_series, 'Corrected_Full')


#%% DNI Generation

def dni_generation(location, weather_file):
      """

      :param location:
      :param weather_file:
      :return:
      """

def weather_percentile(num, weather_dict, month):
    """

    :param num: percentile (as fraction) of weather data desired
    :param weather_dict: dict containing ordered weather data for each month
    :param month: month desired in three letter format e.g. 'jan', 'jun'
    :return: returns a dataframe with weather data for selected month
    """

    ref_num = num*(len(weather_dict[month])-1)
    int_num = round(ref_num)
    return weather_dict[month][int_num]

def generate_TMY(weather_dict):
    """"""

    months_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    TMY = pd.DataFrame()

    for month in months_list:
        month_data = weather_percentile(0.5, weather_dict, month)
        pd.concat(TMY, month_data, axis=0)

    return TMY

TMY = generate_TMY(satellite_weather_sorted)
