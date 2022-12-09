'''
Sizing functions to calculate LCOE
'''
# pylint: disable=W0612
# Code to spit out rack splits, technology agnostic
import pandas as pd
import numpy as np
from Functions.cost_functions import calculate_scenarios, calculate_scenarios_iterations, \
    create_iteration_tables, import_airtable_data

def get_racks(dc_total, number_of_zones, module_params, rack_params, zone_area, \
    rack_interval_ratio):
    '''
    Function that finds the number of racks and modules based on the
    parameters described below:
    According to info from SunCable
    Zone: 20 MW (can be MAV or SAT):
    Field: 20 zones make up a field (~400 MW)
    Solar Precinct: 36 fields make up the total array of SunCable
    Parameters
    ----------
    DCTotal: numeric
        Total DC rated power of the simulated solar farm in MW
    number_of_zones: numeric
        The number of zones that the solar farm consists of
    module_params: pandas series or dataframe
        Includes information such as modules_per_rack, rack_type, elevation, rear_shading, tilt,
        length, width, area
    rack_params: pandas series or dataframe
        Includes information such as modules_per_rack, rack_type, elevation, rear_shading, tilt,
        length, width, area
    zone_area: numeric
        The area of the zone to find the ground coverage ratio.
    rack_interval_ratio: float
        A ratio used to create a range of rack numbers within the zone for searching optimal NPV
        Must be between 0 to 1
        (No fixed size at 20 MW per zone)
    Returns
    -------
    rack_num_range: pd.series
        A range of values for number of racks
    module_num_range: pd.series
        A range of values for number of modules (based on the number of racks)
    gcr_range: pd.series
        A range of values for ground coverage ratio (based on the number of racks)
    '''

    rack_per_zone_float = dc_total/(number_of_zones*rack_params['Modules_per_rack']\
        *module_params['STC']/1e6)
    rack_per_zone_init = round(rack_per_zone_float)
    rack_interval = round(rack_per_zone_float*rack_interval_ratio)
    # Rack interval needs to be equal of greater than
    max(rack_interval, 1)
    rack_num_range = pd.Series(range(rack_per_zone_init - 5 * rack_interval, \
        rack_per_zone_init + 6 * rack_interval, rack_interval))

    rack_num_range.drop(rack_num_range.index[(rack_num_range < 0)], in_place=True)
    rack_num_range = rack_num_range.reindex()
    # drop any negative values which may result due to inappropriate rack_interval_ratio

    module_num_range = rack_num_range * rack_params['Modules_per_rack']

    # Raise an error if any of the gcr_range is more than 1.
    if rack_params['rack_type'] == 'SAT':
        gcr_range = module_params['A_c']*module_num_range/zone_area
    elif rack_params['rack_type'] == 'east_west':
        # multiply by cos(10)
        gcr_range = rack_num_range*rack_params['Area'] * np.cos(10 * np.pi/180)/zone_area
    else:
        raise ValueError('unrecognised rack type')

    return rack_num_range, module_num_range, gcr_range


def get_revenue(yield_series, export_limit, price_schedule, storage_capacity):
    '''
    Function to determine revenue generation from yield,
    At present very simple, future iterations will need storage
    capacity and operation
    The function assumes all DC power smaller than export limit is exported and all DC power
    greater than export limit is stored. This assumption may need to be revisited in the future as
    per info from SunCable.
    :param Yieldseries:
    :param Trans_limit:
    :param price_schedule:
    :return:
    '''

    direct_export = yield_series.clip(lower=None, upper=export_limit)
    store_avail = yield_series - direct_export
    daily_store_pot = store_avail.groupby(store_avail.index.date).sum()
    daily_store = daily_store_pot.clip(lower=None, upper=storage_capacity)
    daily_store.index = pd.to_datetime(daily_store.index)
    direct_revenue = direct_export*price_schedule
    store_revenue = daily_store*price_schedule*0.85
    store_revenue.index = pd.to_datetime(store_revenue.index)
    yearly_direct = direct_revenue.groupby(direct_revenue.index.year).sum()
    yearly_storage = store_revenue.groupby(store_revenue.index.year).sum()
    yearly_total = yearly_direct + yearly_storage
    kwh_export = direct_export.groupby(direct_export.index.year).sum()/1000\
                 + daily_store.groupby(daily_store.index.year).sum()/1000

    return kwh_export, yearly_direct, yearly_storage, yearly_total

def get_costs(num_of_racks, rack_params, module_params, data_tables, install_year=2025,end_year=2058, return_table_outputs=False):
    '''
    Function to return a yearly timeseries of costs
    for installing different numbers of racks
    param num_of_racks:
    param rack_params:
    param module_params:
    param install_year:
    return:
    '''
    old_code = False

    if old_code:
        #install_year=2025
        # Option 3 Call code directly and overwrite values as required
        scenario_list = {'Scenario_Name': num_of_racks, 'ScenarioID': num_of_racks,\
             'Scenario_Tag': num_of_racks}

        scn_cost_data = pd.DataFrame(scenario_list, columns=[
            'Scenario_Name', 'ScenarioID', 'Scenario_Tag'])

        system_link_racks = {'ScenarioID': num_of_racks, 'ScenarioSystemID': num_of_racks,\
            'InstallNumber': num_of_racks, 'SystemID': num_of_racks, 'InstallDate': num_of_racks}

        sys_cost_racks = pd.DataFrame(system_link_racks, columns=[
            'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])

        system_link_fixed = {'ScenarioID': num_of_racks, 'ScenarioSystemID': num_of_racks,\
            'InstallNumber': num_of_racks, 'SystemID': num_of_racks, 'InstallDate': num_of_racks}

        sys_cost_fixed = pd.DataFrame(system_link_fixed, columns=[
            'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])

        if rack_params['rack_type'] == 'SAT':
            sys_cost_racks['SystemID'] = 13
            sys_cost_fixed['SystemID'] = 14
            sys_cost_racks['InstallDate'] = install_year

            sys_cost_fixed['InstallDate'] = install_year
            sys_cost_fixed['InstallNumber'] = 1
            sys_cost_data = pd.concat([sys_cost_racks, sys_cost_fixed])
            sys_cost_data['ScenarioSystemID'] = range(1, 2 * len(num_of_racks) + 1)


        elif rack_params['rack_type'] == 'east_west':
            sys_cost_racks['SystemID'] = 17
            sys_cost_fixed['SystemID'] = 19
            sys_cost_racks['InstallDate'] = install_year
            sys_cost_fixed['InstallDate'] = install_year
            sys_cost_fixed['InstallNumber'] = 1
            sys_cost_data = pd.concat([sys_cost_racks, sys_cost_fixed])
            sys_cost_data['ScenarioSystemID'] = range(1, 2 * len(num_of_racks) + 1)




    else:
        # First setup the scenario_list
        scenario_list = {'Scenario_Name': num_of_racks, 'ScenarioID': num_of_racks, \
                         'Scenario_Tag': num_of_racks}
        try:
            scn_cost_data = pd.DataFrame(scenario_list, columns=[
                'Scenario_Name', 'ScenarioID', 'Scenario_Tag'])
        except ValueError:
            scn_cost_data = pd.DataFrame(scenario_list, index=[0], columns = ['Scenario_Name',
                                         'ScenarioID', 'Scenario_Tag'])
        # Now setup the sys_cost_data table that will replace the scenario_system_link table
        # First obtain a list of cost components that should be used
        component_list = rack_params['cost_components'] + module_params['cost_components']


        component_iteration_count = 0
        for (component_id, install_number_type) in component_list:

            system_link_racks = {'ScenarioID': num_of_racks, 'ScenarioSystemID': num_of_racks, \
                             'InstallNumber': num_of_racks, 'SystemID': num_of_racks, 'InstallDate': num_of_racks}
            try:
                sys_cost_component = pd.DataFrame(system_link_racks, columns=[
                    'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])
            except ValueError:
                sys_cost_component = pd.DataFrame(system_link_racks, index=[0], columns=[
                    'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])

            sys_cost_component['InstallDate'] = install_year
            sys_cost_component['SystemID'] = component_id
            if install_number_type == 'fixed':
                sys_cost_component['InstallNumber'] = 1
            elif install_number_type == 'rack':
                # No change in install number
                sys_cost_component['InstallNumber'] *= 1
            elif install_number_type == 'watt':
                # find number of watts
                sys_cost_component['InstallNumber'] *= rack_params['Modules_per_rack'] * module_params['STC']
            elif install_number_type == 'MW':
                # find number of MW
                sys_cost_component['InstallNumber'] *= rack_params['Modules_per_rack'] * module_params['STC'] / 1000/1000
            elif install_number_type == 'module':
                # find number of modules
                sys_cost_component['InstallNumber'] *= rack_params['Modules_per_rack']

            if component_iteration_count == 0:
                sys_cost_data = sys_cost_component
            else:
                sys_cost_data = pd.concat([sys_cost_data, sys_cost_component])
            component_iteration_count += 1

    sys_cost_data['ScenarioSystemID'] = range(0, sys_cost_data.shape[0])

    scenario_list, scenario_system_link, system_list, system_component_link, component_list,\
        currency_list, costcategory_list = data_tables

    # Replacing some tables from specified inputs
    new_data_tables = scn_cost_data, sys_cost_data, system_list, system_component_link,\
         component_list, currency_list, costcategory_list

    # Running the cost calculations
    cost_outputs = calculate_scenarios(new_data_tables, year_start=install_year, year_end =end_year)
    component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = cost_outputs

    if return_table_outputs:
        tableoutputs = scn_cost_data, sys_cost_data

        return cost_outputs, tableoutputs
    else:
        return cost_outputs





def get_airtable(save_tables=False):
    """
    :return:
    """

    # Airtable Import
    api_key = 'keyJSMV11pbBTdswc'
    base_id = 'appjQftPtMrQK04Aw'

    data_tables = import_airtable_data(base_id=base_id, api_key=api_key, save_tables=save_tables)

    return data_tables


def align_cashflows(yearly_costs, yearly_revenue, start_year = 2029):

    """
    Function to align cash flows out with incoming revenues when they may be different
    shapes. Aligns according to the cash flows out
    :param yearly_costs:
    :param yearly_revenues:
    :param start_date:
    :return:
    """
    cost_rows = yearly_costs.shape[0]
    revenue_rows = yearly_revenue.shape[0]
    repeats = cost_rows // revenue_rows + (cost_rows % revenue_rows > 0)
    revenue_dummy = pd.concat([yearly_revenue] * repeats, ignore_index=True)
    revenue_dummy.index = range(yearly_costs.index[0],
                                yearly_costs.index[0] + revenue_dummy.shape[0])
    revenue_series = revenue_dummy.reindex(yearly_costs.index)
    revenue_series = revenue_series.T

    for i in revenue_series.columns:
        if i < start_year:
            revenue_series[i] = np.zeros(revenue_series.shape[0])

    revenue_series = revenue_series.T

    return revenue_series


def get_npv(yearly_costs,
            yearly_revenue,
            discount_rate=0.07,
            start_year = 2029,
            end_year = 2058):
    """

    :param yearly_costs:
    :param yearly_revenue:
    :param discount_rate:
    :return:
    """

    net_cashflow = -yearly_costs+yearly_revenue.values

    start_date = '1/1/' + str(start_year) + ' 00:00'
    end_date = '12/31/' + str(end_year) + ' 23:59'
    dummy_series = pd.date_range(start=start_date, end=end_date, freq='YS')
    year_series = dummy_series.year
    year_offset = pd.Series(range(0, len(year_series)))
    year_offset.index = year_series

    yearly_factor = 1 / (1 + discount_rate) ** year_offset
    yearly_npv = net_cashflow.mul(yearly_factor, axis=0)
    yearly_npv_costs = yearly_costs.mul(yearly_factor, axis=0)
    yearly_npv_revenue = yearly_revenue.mul(yearly_factor, axis=0)

    npv = yearly_npv.sum(axis=0)
    npv_costs = yearly_npv_costs.sum(axis=0)
    npv_revenue = yearly_npv_revenue.sum(axis=0)

    return npv, yearly_npv, npv_costs, npv_revenue, yearly_npv_revenue, yearly_npv_costs

def get_npv_revenue(yearly_values,
                    discount_rate=0.07,
                    start_year = 2029,
                    end_year = 2058):
    """

    :param yearly_costs:
    :param yearly_revenue:
    :param discount_rate:
    :return:
    """

    start_date = '1/1/' + str(start_year) + ' 00:00'
    end_date = '12/31/' + str(end_year) + ' 23:59'
    dummy_series = pd.date_range(start=start_date, end=end_date, freq='YS')
    year_series = dummy_series.year()
    year_offset = pd.Series(range(0, len(year_series)))
    year_offset.index = year_series

    yearly_factor = 1 / (1 + discount_rate) ** year_offset
    yearly_npv = yearly_values.mul(yearly_factor, axis=0)

    npv = yearly_npv.sum(axis=0)

    return npv, yearly_npv

def get_mcanalysis(num_of_racks, rack_params, module_params, data_tables, install_year=2025, end_year=2058):

    """
    Function to return monte-carlo generated set of cost outputs and data
    :param num_of_racks:
    :param rack_params:
    :param module_params:
    :param data_tables:
    :param install_year:
    :return:
    """
    scenario_list = {'Scenario_Name': num_of_racks,
                    'ScenarioID': num_of_racks, 'Scenario_Tag': num_of_racks}

    scn_cost_data = pd.DataFrame(scenario_list, columns=[
        'Scenario_Name', 'ScenarioID', 'Scenario_Tag'])

    system_link_racks = {'ScenarioID': num_of_racks, 'ScenarioSystemID': num_of_racks,\
         'InstallNumber': num_of_racks, 'SystemID': num_of_racks, 'InstallDate': num_of_racks}

    sys_cost_racks = pd.DataFrame(system_link_racks, columns=[
        'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])

    system_link_fixed = {'ScenarioID': num_of_racks, 'ScenarioSystemID': num_of_racks,\
         'InstallNumber': num_of_racks, 'SystemID': num_of_racks, 'InstallDate': num_of_racks}

    sys_cost_fixed = pd.DataFrame(system_link_fixed, columns=[
        'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])

    if rack_params['rack_type'] == 'SAT':
        sys_cost_racks['SystemID'] = 13
        sys_cost_fixed['SystemID'] = 14
    elif rack_params['rack_type'] == 'east_west':
        sys_cost_racks['SystemID'] = 17
        sys_cost_fixed['SystemID'] = 19

    sys_cost_racks['InstallDate'] = install_year

    sys_cost_fixed['InstallDate'] = install_year
    sys_cost_fixed['InstallNumber'] = 1

    sys_cost_data = pd.concat([sys_cost_racks, sys_cost_fixed])

    sys_cost_data['ScenarioSystemID'] = range(1, 2 * len(num_of_racks) + 1)

    scenario_list, scenario_system_link, system_list, system_component_link, component_list,\
         currency_list, costcategory_list = data_tables

    # Replacing some tables from specified inputs
    new_data_tables = scn_cost_data, sys_cost_data, system_list, system_component_link,\
         component_list, currency_list, costcategory_list

    # Run iterative monte-carlo analysis for specified system
    data_tables_iter = create_iteration_tables(new_data_tables, 500, iteration_start=0)

    outputs_iter = calculate_scenarios_iterations(data_tables_iter,\
         year_start=install_year, year_end = end_year)

    component_usage_y_iter, component_cost_y_iter, total_cost_y_iter,\
         cash_flow_by_year_iter = outputs_iter

    return component_usage_y_iter, component_cost_y_iter, total_cost_y_iter,\
         cash_flow_by_year_iter, data_tables_iter

def get_lcoe(yearly_costs, kwh_series):
    """
    A function to determine discounted LCOE from yield and cost data
    :param yearly_costs:
    :param kWh_series:
    :return:
    """
    discount_rate = 0.07
    year_offset = pd.Series(range(0, len(yearly_costs)))
    year_offset.index = yearly_costs.index

    yearly_factor = 1 / (1 + discount_rate) ** year_offset
    discounted_kwh = kwh_series.mul(yearly_factor, axis=0)
    yearly_npv_costs = yearly_costs.mul(yearly_factor, axis=0)

    kwh_dis_sum = discounted_kwh.sum(axis=0)
    npv_costs = yearly_npv_costs.sum(axis=0)
    lcoe = npv_costs/kwh_dis_sum.values*1000

    return lcoe, kwh_dis_sum
