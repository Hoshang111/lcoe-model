import pandas as pd
import numpy as np
import os
import datetime as dt
import matplotlib.pyplot as plt
import pickle
import pytz


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

satellite_data_2017_path = os.path.join(data_path, "Feni_Himawari_2017.csv")
satellite_data_2018_path = os.path.join(data_path, "Feni_Himawari_2018.csv")
satellite_data_2019_path = os.path.join(data_path, "Feni_Himawari_2019.csv")
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
                                                'Wind Speed':'wind_speed',
                                                'Clearsky GHI':'clearsky ghi',
                                                'Cloud Type':'cloud type'})
satellite_data_aware = satellite_data_aware.rename(columns={'GHI':'ghi',
                                                'DHI':'dhi',
                                                'DNI':'dni',
                                                'Temperature':'temp',
                                                'Wind Speed':'wind_speed',
                                                'Clearsky GHI':'clearsky ghi',
                                                'Cloud Type':'cloud type'})

#%% determine clearness index for comparisons

clearness_index = satellite_data['ghi']/satellite_data['clearsky ghi']
clearness_index = clearness_index.fillna(value=0)
clearness_index = clearness_index.rename('CI')
satellite_data = pd.concat([satellite_data, clearness_index], axis=1)

clearness_index = satellite_data_aware['ghi']/satellite_data_aware['clearsky ghi']
clearness_index = clearness_index.fillna(value=0)
clearness_index = clearness_index.rename('CI')
satellite_data_aware = pd.concat([satellite_data_aware, clearness_index], axis=1)

#%% Align Data
# satellite_data_aligned =
ground_data_mod = ground_data.shift(periods=5, freq='T')
ground_data_hourly = ground_data_mod.resample('10T', axis=0).mean()
# ground_data_hourly = ground_data_hourlyA.shift(periods=-5, freq='T')
satellite_data_aligned = satellite_data.reindex(ground_data_hourly.index)

ground_dhi = ground_data_hourly['dhi']
ground_ghi = ground_data_hourly['ghi']
ground_dni = satellite_data_aligned['dni']

satellite_dhi = satellite_data_aligned['dhi']
satellite_ghi = satellite_data_aligned['ghi']
satellite_dni = satellite_data_aligned['dni']

#%% Group by month

def weather_sort(weather_file, sort_by):
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
            sorted_list = sorted(unsorted_list, key=lambda x: x[sort_by].mean())
            for j in range(len(sorted_list)):
                  weather[months_list[i]][j] = sorted_list[j]

      return weather

ground_weather_sorted = weather_sort(ground_data_hourly, 'ghi')
satellite_weather_sorted = weather_sort(satellite_data, 'ghi')
satellite_weather_sort = weather_sort(satellite_data_aware, 'ghi')

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
date1 = '2018-12-15'
date2 = '2018-12-22'
month = pd.to_datetime(date1).month

fig, ax = plt.subplots(figsize=(25, 20))
ax.plot(ground_ghi[date1:date2], linewidth=3, label='ground data')
ax.plot(satellite_ghi[date1:date2], linewidth=3, linestyle='--', label='satellite data')
ax.set_ylabel('GHI', **fontdict)
ax.legend()
# plt.show()
fig_name = 'LinePlot-Feni_GHI ' + date1

save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/" + fig_name
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.clf()

#%% Initial scatter plot

# scatter plot for uncorrected data with linear fit

def weather_nofit(ground, satellite, fig_name):
    """"""
    x = satellite
    y = ground
    fig, ax = plt.subplots(figsize=(25, 20))
    ax.scatter(x, y)
    ax.set_xlabel('Satellite', **fontdict)
    ax.set_ylabel('Ground', **fontdict)
    ax.set_title(fig_name)

    # plt.show()
    save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/" + fig_name
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return


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
    if not x.empty:
        c2, c1, c0 = np.polyfit(x, y, 2)
        correlation_matrix = np.corrcoef(x.values, y.values)
        correlation_xy = correlation_matrix[0, 1]
        r_squared = correlation_xy ** 2

        ax.plot(x, x * x * c2 + x * c1 + c0, linewidth=3, color='C1')
        # ax.set_ylim(0,1.25)
        # ax.set_xlim(0,1.25)
        plot_text = 'R-squared = %.2f' % r_squared
        plt.text(0.3, 0.3, plot_text, fontsize=25)
    else:
        c2, c1, c0 = [0, 0, 0]


    # plt.show()
    save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/" + fig_name
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return c0, c1, c2

c0_init, c1_init, c2_init = weather_scatter(ground_ghi, satellite_ghi, 'Uncorrected_Full')

#%% scatter plots for specific conditions

# Define conditions of interest: Cloud types
satellite_cloud0 = satellite_data_aligned.loc[satellite_data['cloud type'] == 0, ['ghi', 'dhi', 'dni']]
ground_cloud0 = ground_data_hourly.loc[satellite_data['cloud type'] == 0, ['ghi', 'dhi', 'dni']]

satellite_cloud1 = satellite_data_aligned.loc[satellite_data['cloud type'] == 1, ['ghi', 'dhi', 'dni']]
ground_cloud1 = ground_data_hourly.loc[satellite_data['cloud type'] == 1, ['ghi', 'dhi', 'dni']]

satellite_cloud2 = satellite_data_aligned.loc[satellite_data['cloud type'] == 2, ['ghi', 'dhi', 'dni']]
ground_cloud2 = ground_data_hourly.loc[satellite_data['cloud type'] == 2, ['ghi', 'dhi', 'dni']]

satellite_cloud3 = satellite_data_aligned.loc[satellite_data['cloud type'] == 3, ['ghi', 'dhi', 'dni']]
ground_cloud3 = ground_data_hourly.loc[satellite_data['cloud type'] == 3, ['ghi', 'dhi', 'dni']]

satellite_cloud4 = satellite_data_aligned.loc[satellite_data['cloud type'] == 4, ['ghi', 'dhi', 'dni']]
ground_cloud4 = ground_data_hourly.loc[satellite_data['cloud type'] == 4, ['ghi', 'dhi', 'dni']]

# satellite_cloud5 = satellite_data_aligned.loc[satellite_data['cloud type'] == 5, ['ghi']]
# ground_cloud5 = ground_data_hourly.loc[satellite_data['cloud type'] == 5, ['ghi']]

satellite_cloud6 = satellite_data_aligned.loc[satellite_data['cloud type'] == 6, ['ghi', 'dhi', 'dni']]
ground_cloud6 = ground_data_hourly.loc[satellite_data['cloud type'] == 6, ['ghi', 'dhi', 'dni']]

satellite_cloud7 = satellite_data_aligned.loc[satellite_data['cloud type'] == 7, ['ghi', 'dhi', 'dni']]
ground_cloud7 = ground_data_hourly.loc[satellite_data['cloud type'] == 7, ['ghi', 'dhi', 'dni']]

cloud_list_satellite = [satellite_cloud0, satellite_cloud1, satellite_cloud2, satellite_cloud3, satellite_cloud4,
              satellite_cloud6, satellite_cloud7]

cloud_list_ground = [ground_cloud0, ground_cloud1, ground_cloud2, ground_cloud3, ground_cloud4,
              ground_cloud6, ground_cloud7]

cloud_zip = list(zip(cloud_list_satellite, cloud_list_ground))

# scatter plot for uncorrected data with linear fit
for str in ['ghi', 'dhi', 'dni']:
    c0_cloud0, c1_cloud0, c2_cloud0 = weather_scatter(ground_cloud0[str], satellite_cloud0[str], 'Cloud 0' + str)
    c0_cloud1, c1_cloud1, c2_cloud1 = weather_scatter(ground_cloud1[str], satellite_cloud1[str], 'Cloud 1' + str)
    c0_cloud2, c1_cloud2, c2_cloud2 = weather_scatter(ground_cloud2[str], satellite_cloud2[str], 'Cloud 2' + str)
    c0_cloud3, c1_cloud3, c2_cloud3 = weather_scatter(ground_cloud3[str], satellite_cloud3[str], 'Cloud 3' + str)
    c0_cloud4, c1_cloud4, c2_cloud4 = weather_scatter(ground_cloud4[str], satellite_cloud4[str], 'Cloud 4' + str)
    # c0_cloud5, c1_cloud5, c2_cloud5 = weather_scatter(ground_cloud5['ghi'], satellite_cloud5['ghi'], 'Cloud 5')
    c0_cloud6, c1_cloud6, c2_cloud6 = weather_scatter(ground_cloud6[str], satellite_cloud6[str], 'Cloud 6' + str)
    c0_cloud7, c1_cloud7, c2_cloud7 = weather_scatter(ground_cloud7[str], satellite_cloud7[str], 'Cloud 7' + str)

#%%
# split each cloud by clearness index
satellite_cloud_high = satellite_data_aligned.loc[satellite_data['CI'] >= 0.7, ['ghi']]
ground_cloud_high = ground_data_hourly.loc[satellite_data['CI'] >= 0.7, ['ghi']]
satellite_cloud_med = satellite_data_aligned.loc[satellite_data['CI'].between(0.3, 0.7), ['ghi']]
ground_cloud_med = ground_data_hourly.loc[satellite_data['CI'].between(0.3, 0.7), ['ghi']]
satellite_cloud_low = satellite_data_aligned.loc[satellite_data['CI'] <= 0.3, ['ghi']]
ground_cloud_low = ground_data_hourly.loc[satellite_data['CI'] <= 0.3, ['ghi']]

c0_cloud_high, c1_cloud_high, c2_cloud_high = weather_scatter(ground_cloud_high['ghi'], satellite_cloud_high['ghi'], 'CI High')
c0_cloud_med, c1_cloud_med, c2_cloud_med = weather_scatter(ground_cloud_med['ghi'], satellite_cloud_med['ghi'], 'CI med')
c0_cloud_low, c1_cloud_low, c2_cloud_low = weather_scatter(ground_cloud_low['ghi'], satellite_cloud_low['ghi'], 'Ci low')

for satellite, ground in cloud_zip:
    for str in ['ghi', 'dhi', 'dni']:
        satellite_cloud_high = satellite.loc[satellite_data['CI'] >= 0.7, [str]]
        ground_cloud_high = ground.loc[satellite_data['CI'] >= 0.7, [str]]
        satellite_cloud_med = satellite.loc[satellite_data['CI'].between(0.3, 0.7), [str]]
        ground_cloud_med = ground.loc[satellite_data['CI'].between(0.3, 0.7), [str]]
        satellite_cloud_low = satellite.loc[satellite_data['CI'] <= 0.3, [str]]
        ground_cloud_low = ground.loc[satellite_data['CI'] <= 0.3, [str]]

        weather_nofit(ground_cloud_high[str], satellite_cloud_high[str],
                                                                  'CI High nofit ' + str)
        weather_nofit(ground_cloud_med[str], satellite_cloud_med[str],
                                                               'CI med nofit ' + str)
        weather_nofit(ground_cloud_low[str], satellite_cloud_low[str],
                                                               'Ci low nofit ' + str)




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
    month_percentile = weather_dict[month][int_num]

    return month_percentile

def generate_TMY(weather_dict):
    """"""

    months_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    TMY = pd.DataFrame()

    for month in months_list:
        month_data = weather_percentile(0.5, weather_dict, month)
        TMY = pd.concat([TMY, month_data], axis=0)

    measure_freq = pd.infer_freq(weather_dict['jan'][0].index)
    TMY_dummy = pd.date_range(start='1/1/1990', end='1/1/1991', freq=measure_freq, tz=pytz.UTC)
    TMY_index = TMY_dummy.delete(-1)
    TMY = TMY.set_index(TMY_index)


    return TMY

TMY_file = generate_TMY(satellite_weather_sorted)

#%%
# Fiddling with generating a full 30 year timeseries with randomly selected months

def generate_mc_timeseries(weather_dict, start_date, end_date):
    """"""

    dummy_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    ran_gen = np.random.random(len(dummy_range))
    generation_list = list(zip(dummy_range, ran_gen))
    months_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    mc_timeseries = pd.DataFrame()

    for single_date, num in generation_list:
        month_num = single_date.month
        month = months_list[month_num-1]
        weather_month = weather_percentile(num, weather_dict, month)
        mc_timeseries = pd.concat([mc_timeseries, weather_month], axis=0)

    mc_timeseries = mc_timeseries[~((mc_timeseries.index.month == 2) & (mc_timeseries.index.day == 29))]
    measure_freq = pd.infer_freq(weather_dict['jan'][0].index)
    index_dummy = pd.date_range(start=start_date, end=end_date, freq=measure_freq, tz=pytz.UTC)
    mc_timeseries_index = index_dummy[~((index_dummy.month == 2) & (index_dummy.day == 29))]
    mc_timeseries = mc_timeseries.set_index(mc_timeseries_index)

    return mc_timeseries

def gen_mcts(weather_dict, generation_list, start_date, end_date):
    """"""

    months_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    mc_timeseries = pd.DataFrame()

    for single_date, num in generation_list:
        month_num = single_date.month
        month = months_list[month_num-1]
        weather_month = weather_percentile(num, weather_dict, month)
        mc_timeseries = pd.concat([mc_timeseries, weather_month], axis=0)

    mc_timeseries = mc_timeseries[~((mc_timeseries.index.month == 2) & (mc_timeseries.index.day == 29))]
    measure_freq = pd.infer_freq(weather_dict['jan'][0].index)
    index_dummy = pd.date_range(start=start_date, end=end_date, freq=measure_freq, tz=pytz.UTC)
    mc_timeseries_index = index_dummy[~((index_dummy.month == 2) & (index_dummy.day == 29))]
    mc_timeseries = mc_timeseries.set_index(mc_timeseries_index)

    return mc_timeseries

test_timeseries = generate_mc_timeseries(satellite_weather_sort, '1/1/2023 00:00:00', '31/12/2025 23:59:00')

weather_dnv_file = 'Combined_Longi_570_Tracker-bifacial_FullTS_4m.csv'
current_path = os.getcwd()
weather_file = pd.read_csv(os.path.join(current_path, 'Data', 'WeatherData', weather_dnv_file), delimiter=';', index_col=0, parse_dates=True, dayfirst=True)
weather_file = weather_file.rename(columns={'GlobHor': 'ghi', 'T_Amb': 'T', 'EArray': 'DC_out'})
DC_series = pd.DataFrame(weather_file['DC_out'])

DC_dict = weather_sort(DC_series, 'DC_out')
test3 = pd.DataFrame()
DC_series.set_index(pd.to_datetime(DC_series.index), inplace=True)

for column in random_timeseries.T:
    generation_list=list(zip(month_series, column))
    test2 = gen_mcts(DC_dict, generation_list, start_date, end_date)
    test3 = pd.concat([test2, test3], axis=1)



