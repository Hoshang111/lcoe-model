import pandas as pd
import numpy as np
import os
from Functions.cost_functions import get_airtable, generate_iterations
import Functions.simulation_functions as func
import pytz
import Functions.sizing_functions as sizing

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

def get_yield_datatables(iter_num):
    # First get data from Airtable
    api_key = 'keyJSMV11pbBTdswc'
    base_id = 'appjQftPtMrQK04Aw'
    table_name = 'YieldParameters'

    yield_variables = get_airtable(base_id, api_key, table_name, sort_by='YieldID')

    # Now generate iteration data. Note that all variables are assumed flat distribution in this case (unless specified otherwise in the airtable database).
    yield_variables_iter = generate_iterations(yield_variables, index_name='YieldID',
                                        index_description='YieldName', num_iterations=iter_num,
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

def dict_sort(dict_file, sort_by):
    """

    :param weather_file:
    :return:
    """

    dict_monthly = dict_file.groupby(dict_file.index.month)
    dict_list = [group for _, group in dict_monthly]
    months_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    ordered_dict = {}

    for i in range(len(months_list)):
        ordered_dict[months_list[i]] = {}
        unsorted_data = dict_list[i]
        split_data = unsorted_data.groupby(unsorted_data.index.year)
        unsorted_list = [group for _, group in split_data]
        sorted_list = sorted(unsorted_list, key=lambda x: x[sort_by].mean())
        for j in range(len(sorted_list)):
            ordered_dict[months_list[i]][j] = sorted_list[j]

    return ordered_dict

def dict_percentile(num, ordered_dict, month):
    """

    :param num: percentile (as fraction) of weather data desired
    :param weather_dict: dict containing ordered weather data for each month
    :param month: month desired in three letter format e.g. 'jan', 'jun'
    :return: returns a dataframe with weather data for selected month
    """

    ref_num = num*(len(ordered_dict[month])-1)
    int_num = round(ref_num)
    month_percentile = ordered_dict[month][int_num]

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

def gen_mcts(ordered_dict, generation_list, start_date, end_date):
    """"""

    months_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    mc_timeseries = pd.DataFrame()
    ordered_dict.pop('label', None)

    for single_date, num in generation_list:
        month_num = single_date.month
        month = months_list[month_num-1]
        dict_month = dict_percentile(num, ordered_dict, month)
        mc_timeseries = pd.concat([mc_timeseries, dict_month], axis=0)

    mc_timeseries = mc_timeseries[~((mc_timeseries.index.month == 2) & (mc_timeseries.index.day == 29))]
    measure_freq = pd.infer_freq(ordered_dict['jan'][0].index)
    index_dummy = pd.date_range(start=start_date, end=end_date, freq=measure_freq, tz=pytz.UTC)
    mc_timeseries_index = index_dummy[~((index_dummy.month == 2) & (index_dummy.day == 29))]
    mc_timeseries = mc_timeseries.set_index(mc_timeseries_index)

    return mc_timeseries

def mc_weather_import(weather_file):
    """"""

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    weather_dnv_dummy = pd.read_csv(os.path.join('../Data', 'WeatherData', weather_file),
                                    delimiter=';', index_col=0, parse_dates=True, dayfirst=True)
    weather_dnv_dummy = weather_dnv_dummy.rename(
        columns={'GlobHor': 'ghi', 'DiffHor': 'dhi', 'BeamHor': 'bhi', 'T_Amb': 'temp_air',
                 'WindVel': 'wind_speed', 'EArray': 'dc_yield'})

    weather_dnv = weather_dnv_dummy[['ghi', 'dhi', 'bhi', 'temp_air', 'wind_speed', 'dc_yield']].copy()
    weather_dnv.set_index(pd.to_datetime(weather_dnv.index, utc=False), inplace=True)
    weather_dnv.sort_index(inplace=True)
    weather_dnv.index = weather_dnv.index.tz_localize('Australia/Darwin')

    dni_dummy = pd.read_csv(os.path.join('../Data', 'WeatherData', 'dni_simulated_full.csv'),
                            index_col=0, parse_dates=True)
    dni_dummy.set_index(pd.to_datetime(dni_dummy.index, utc=False), drop=True, inplace=True)
    dni_dummy.index = dni_dummy.index.tz_convert('Australia/Darwin')

    pw_dummy = pd.read_csv(os.path.join('../Data', 'WeatherData', 'pw_full.csv'),
                            index_col=0, parse_dates=True)
    pw_dummy.set_index(pd.to_datetime(pw_dummy.index, utc=False), drop=True, inplace=True)
    pw_dummy.index = pw_dummy.index.tz_convert('Australia/Darwin')
    pw_mod = pw_dummy/10

    weather_dnv = weather_dnv.join(dni_dummy, how='left')
    weather_dnv.rename(columns={"0": "dni"}, inplace=True)
    weather_dnv = weather_dnv.join(pw_mod, how='left')
    weather_dnv.rename(columns={"PrecipitableWater": "precipitable_water"}, inplace=True)
    weather_dnv.drop(['bhi', 'dc_yield'], axis=1, inplace=True)

    # shift weather files 30 min so that solar position is calculated at midpoint of period
    weather_dnv_mod = weather_dnv.shift(periods=30, freq='T')

    return weather_dnv_mod

def mc_dc_yield(results, zone_area, temp_model, mc_weather_file, location):
    """"""

    module = results[5]
    rack = results[6]
    module_per_zone = results[?]
    gcr = (module_per_zone*module['A_c']) / zone_area
    dc_results = func.mc_dc(rack, module, temp_model, mc_weather_file,
                                               module_per_zone, gcr,
                                               location)
    # dc_df.rename(columns={0: "dc_out"}, inplace=True)
    # dc_df.rename(columns={'p_mp': "dc_out"}, inplace=True)

    return dc_results

def discount_ghi(ghi_series, discount_rate):

    """"""

    year_offset = pd.Series(range(0, len(ghi_series)))
    year_offset.index = ghi_series.index

    yearly_factor = 1 / (1 + discount_rate) ** year_offset
    yearly_discounted = ghi_series.mul(yearly_factor, axis=0)

    ghi_discounted = yearly_discounted.sum(axis=0)

    return ghi_discounted

def apply_degradation(ghi, first_year_degradation, degradation_rate):
    """"""

    delta_index = (ghi.index - ghi.index[0]).days
    delta_t = delta_index.to_frame(index=False)
    deg_list = []
    for deg_y1, deg_ann in list(zip(first_year_degradation, degradation_rate)):

        deg_factor = delta_t.copy(deep=True)
        deg_factor.loc[(deg_factor[0] <= 365)] = 1-deg_factor*deg_y1/3.65e4
        deg_factor.loc[(deg_factor[0] > 365)] = 1-deg_y1/100-deg_ann*deg_factor/3.65e4
        deg_list.append(deg_factor)

    deg_df = pd.concat(deg_list, axis=1, ignore_index=False)
    deg_df.index = ghi.index
    deg_df.columns = np.arange(len(deg_df.columns))

    return deg_df

def apply_soiling(soiling_var, weather, default_soiling):
    """"""

    month_timeseries = weather.index.month
    dummy = month_timeseries.to_frame(index=False)
    init_soiling = dummy.astype('float64', copy=True)
    for month, value in default_soiling:
        init_soiling.loc[init_soiling[0] == month, 0] = value


    soiling_list = []
    for soiling in soiling_var:
        total_soiling = 1-init_soiling*soiling
        soiling_list.append(total_soiling)

    soiling_df = pd.concat(soiling_list, axis=1, ignore_index=False)
    soiling_df.index = weather.index
    soiling_df.columns = np.arange(len(soiling_df.columns))

    return soiling_df

def apply_temp_loss(temp_var, ghi, coefficient):
    """"""

    temp_df = ghi.multiply(np.array(temp_var), axis='columns')
    temp_df *= coefficient
    temp_loss = 1+temp_df

    return temp_loss


def get_dcloss(loss_parameters, weather, default_soiling, temp_coefficient):
    """"""

    deg_df = apply_degradation(ghi=weather[0], first_year_degradation=loss_parameters['degr_yr1'],
                               degradation_rate=loss_parameters['degr_annual'])

    soiling_df = apply_soiling(soiling_var=loss_parameters['soiling_modifier'],
                               weather=weather[0], default_soiling=default_soiling)

    temp_df = apply_temp_loss(temp_var=loss_parameters['ave_temp_increase'], ghi=weather, coefficient=temp_coefficient)

    tol_mismatch = 1-loss_parameters['tol_mismatch']/100

    loss_df = deg_df.multiply(np.array(tol_mismatch))*soiling_df*temp_df

    return loss_df

def gen_revenue(yield_dict, scheduled_price, discount_rate):
    """"""
    mc_yield_outputs = {}

    for key in yield_dict:
        NPV_outputs = {}
        revenue = yield_dict*scheduled_price
        NPV_outputs['kWh_total'], NPV_outputs['kWh_yearly'] = sizing.get_npv_revenue(yield_dict, discount_rate=0)
        NPV_outputs['kWh_total_discounted'], NPV_outputs['kWh_yearly_discounted'] = sizing.get_npv_revenue(yield_dict, discount_rate)
        NPV_outputs['revenue_total'], NPV_outputs['revenue_yearly'] = sizing.get_npv_revenue(revenue, discount_rate=0)
        NPV_outputs['npv_revenue'], NPV_outputs['npv_yearly'] = sizing.get_npv_revenue(revenue, discount_rate)
        NPV_outputs['kWh_yearly'] = NPV_outputs['kWh_yearly'].T
        NPV_outputs['kWh_yearly_discounted'] = NPV_outputs['kWh_yearly_discounted'].T
        NPV_outputs['revenue_yearly'] = NPV_outputs['revenue_yearly'].T
        NPV_outputs['npv_yearly'] = NPV_outputs['npv_yearly'].T
        mc_yield_outputs[key] = NPV_outputs

    return mc_yield_outputs

def run_AC(combined_dc, inverter):
    """"""
    p_dc = combined_dc['p_mp']
    v_dc = combined_dc['v_mp']
    Paco = inverter['Paco']
    Pdco = inverter['Pdco']
    Vdco = inverter['Vdco']
    Pnt = inverter['Pnt']
    Pso = inverter['Pso']
    C0 = inverter['C0']
    C1 = inverter['C1']
    C2 = inverter['C2']
    C3 = inverter['C3']
    Pso = inverter['Pso']

    A = Pdco * (1 + C1 * (v_dc - Vdco))
    B = Pso * (1 + C2 * (v_dc - Vdco))
    C = C0 * (1 + C3 * (v_dc - Vdco))

    power_ac = (Paco / (A - B) - C * (A - B)) * (p_dc - B) + C * (p_dc - B) ** 2

    power_ac = np.minimum(Paco, power_ac)
    min_ac_power = -1.0 * abs(Pnt)
    below_limit = p_dc < Pso
    try:
        power_ac[below_limit] = min_ac_power
    except TypeError:  # power_ac is a float
        if below_limit:
            power_ac = min_ac_power

    if isinstance(p_dc, pd.Series):
        power_ac = pd.Series(power_ac, index=p_dc.index)

    return power_ac

def combine_variance(weather_dict, loss_df, results_dict):
    """"""

    combined_dc = loss_df.mul(weather_dict, axis=0)
    AC_outputs = run_AC(combined_dc, results_dict['Inverter'])
    combined_mc_dict = pd.concat([combined_dc, AC_outputs], axis=1)

    return combined_mc_dict

 # %% ===================================================

def run_yield_mc(results_dict, input_params, mc_weather_file, yield_datatables, location):
    """"""

    # %% ===========================================
    # first to get appropriate values from dataframe
    temp_model = str(input_params['temp_model'].values[0])
    scheduled_price = input_params['scheduled_price'].values[0]
    discount_rate = input_params['discount_rate'].values[0]
    zone_area = input_params['zone_area'].values[0]

    # %% ===========================================
    # create a dict of ordered dicts with dc output, including weather GHI as first column
    dc_ordered = {}
    ghi_timeseries = pd.DataFrame(mc_weather_file['ghi'])
    ghi_dict = dict_sort(ghi_timeseries, 'ghi')

    for key in results_dict:
        results = results_dict[key]
        yield_timeseries = mc_dc_yield(results, zone_area,
                                       temp_model, mc_weather_file, location)
        ghi_sort = pd.concat([yield_timeseries, ghi_timeseries], axis=1, ignore_index=False )
        dc_ordered[results[0]] = dict_sort(ghi_sort, 'ghi')

    for key in dc_ordered:
        for month in dc_ordered[key]:
            for df in dc_ordered[key][month].values():
                df.drop('ghi', axis=1, inplace=True)

    # %% ===========================================================
    # Create data tables for yield parameters

    start_date = '1/1/2022 00:00:00'
    end_date = '31/12/2052 23:59:00'
    month_series = pd.date_range(start=start_date, end=end_date, freq='MS')
    # need to create a wrapper function to call for each set of random numbers
    random_timeseries = np.random.random((len(month_series), len(yield_datatables)))
    random_timeseries[:, 0][:, None] = 0.5

    output_dict = {}
    ghi_interim = []

    # %%
    for column in random_timeseries.T:
        generation_list = list(zip(month_series, column))
        ghi_interim.append(gen_mcts(ghi_dict, generation_list, start_date, end_date))
    mc_ghi = pd.concat(ghi_interim, axis=1, ignore_index=False)
    mc_ghi.columns = np.arange(len(mc_ghi.columns))

    # need to check above for creation of dict and then combining into dataframe

    for key in dc_ordered:
        ordered_dict = dc_ordered[key]
        dc_output = []
        for column in random_timeseries.T:
            generation_list = list(zip(month_series, column))
            dc_output.append(gen_mcts(ordered_dict, generation_list, start_date, end_date))
        output_dict[key] = pd.concat(dc_output, axis=1, ignore_index=False)
        output_dict[key].columns = np.arange(len(output_dict[key].columns))

    # since GHI was first of our scenarios
    # %% ===========================================================
    # calculate discounted ghi
    yearly_ghi = mc_ghi.groupby(mc_ghi.index.year).sum()
    discounted_ghi = []

    for column in yearly_ghi:
        ghi_sum = discount_ghi(yearly_ghi[column], discount_rate=input_params['discount_rate'])
        discounted_ghi.append(ghi_sum)

    ghi_discount = pd.DataFrame(discounted_ghi)

    # Now apply losses, all to be applied through header functions
    # %%
    # TODO: check appropriate temperature coefficient of power
    default_soiling = [(1, 0.02), (2, 0.02), (3, 0.02), (4, 0.02), (5, 0.02), (6, 0.02), (7, 0.02), (8, 0.02),
                       (9, 0.02), (10, 0.02), (11, 0.02), (12, 0.02)]
    temp_coefficient = -0.0025
    loss_df = get_dcloss(yield_datatables, mc_ghi, default_soiling, temp_coefficient)

    # %% =========================================================
    # creating three different datatables
    combined_mc_dict = {}
    for key in results_dict:
        combined_mc_dict[key] = combine_variance(output_dict[key], loss_df, results_dict[key])

    # %% ==========================================================
    # calculate revenue from yield dictionary

    combined_mc_outputs = gen_revenue(combined_mc_dict['p_mp_AC'], scheduled_price, discount_rate)

    return combined_mc_outputs, ghi_discount,

def get_cost_dict(cash_flow, discount_rate, year):
    """"""

    install_year = int(year)
    cost_dict = {}
    for column in cash_flow:
        dummy_a = cash_flow[column]
        dummy = dummy_a.reset_index()
        dummy.columns = ['Iteration', 'Year', 'cost']
        discounted_cost = dummy['cost'] / (1 + discount_rate) ** \
                                                     (dummy['Year'] - install_year)
        dummy = pd.concat([dummy, discounted_cost], axis=1, ignore_index=True)
        dummy.columns = ['Iteration', 'Year', 'cost', 'discounted_cost']
        cost_total_list = []
        discounted_cost_total_list = []
        cost_list = []
        discounted_cost_list = []
        sub_dict = {}
        iteration_array = dummy['Iteration'].unique()
        for iteration in iteration_array:
            cost_iteration = dummy[dummy['Iteration'] == iteration]
            cost_iteration.index = cost_iteration['Year']
            cost_total = cost_iteration['cost'].sum()
            discounted_cost_total = cost_iteration['discounted_cost'].sum()
            cost_list.append(cost_iteration['cost'])
            discounted_cost_list.append(cost_iteration['discounted_cost'])
            cost_total_list.append(cost_total)
            discounted_cost_total_list.append(discounted_cost_total)

        cost_df = pd.DataFrame(cost_list)
        cost_df.reset_index(inplace=True)
        cost_df.drop(columns=['index'], inplace=True)
        sub_dict['cost'] = cost_df.T
        discounted_cost_df = pd.DataFrame(discounted_cost_list)
        discounted_cost_df.reset_index(inplace=True)
        discounted_cost_df.drop(columns=['index'], inplace=True)
        sub_dict['discounted_cost'] = discounted_cost_df.T
        sub_dict['discounted_cost_total'] = pd.Series(discounted_cost_total_list)
        sub_dict['cost_total'] = pd.Series(cost_total_list)

        cost_dict[column] = sub_dict

    return cost_dict



