import pandas as pd
import numpy as np
import os
from Functions.cost_functions import get_airtable, generate_iterations

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

def generate_mc_timeseries(weather_dict, start_date, end_date, random_list):
    """"""

    dummy_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    generation_list = list(zip(dummy_range, random_list))
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

def get_yield_datatables():
    # First get data from Airtable
    api_key = 'keyJSMV11pbBTdswc'
    base_id = 'appjQftPtMrQK04Aw'
    table_name = 'YieldParameters'

    yield_variables = get_airtable(base_id, api_key, table_name, sort_by='YieldID')

    # Now generate iteration data. Note that all variables are assumed flat distribution in this case (unless specified otherwise in the airtable database).
    yield_variables_iter = generate_iterations(yield_variables, index_name='YieldID',
                                        index_description='YieldName', num_iterations=100,
                                        iteration_start=0, default_dist_type = 'flat')


    # Separate out the three sets of variables

    yield_variables_baseline = yield_variables_iter[yield_variables_iter['YieldID']==1].set_index('Iteration')
    yield_variables_MAV_adj = yield_variables_iter[yield_variables_iter['YieldID']==2].set_index('Iteration')
    yield_variables_SAT_adj = yield_variables_iter[yield_variables_iter['YieldID']==3].set_index('Iteration')

    # Generate the combined MAV or SAT variables

    yield_variables_MAV = yield_variables_baseline.copy()
    yield_variables_SAT = yield_variables_baseline.copy()
    for (new, adj, id, name) in [
        (yield_variables_MAV, yield_variables_MAV_adj, 4, 'Baseline + MAV'),
        (yield_variables_SAT, yield_variables_SAT_adj, 5, 'Baseline + SAT'),
    ]:

        new['YieldID'] = id
        new['YieldName'] = name

        for sum_variable in ['ave_temp_increase','degr_annual','non_avail','degr_yr1','tol_mismatch']:
            new[sum_variable] += adj[sum_variable]
        for mult_variable in ['bifaciality_modifier','soiling_modifier']:
            new[mult_variable] *= adj[mult_variable]

    return yield_variables_MAV, yield_variables_SAT