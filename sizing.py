# Code to spit out rack splits, technology agnostic
import pandas as pd
import numpy as np
import airtable
import SuncableCost as Suncost


def get_racks(DCTotal,
              number_of_zones,
              module_params,
              rack_params,
              zone_area,
              rack_interval_ratio):
    """
        get_racks function finds the number of racks and modules based on the parameters described below:

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
            Includes information such as modules_per_rack, rack_type, elevation, rear_shading, tilt, length, width, area

        rack_params: pandas series or dataframe
            Includes information such as modules_per_rack, rack_type, elevation, rear_shading, tilt, length, width, area

        zone_area: numeric
            The area of the zone to find the ground coverage ratio.

        rack_interval_ratio: float
            A ratio used to create a range of rack numbers within the zone for searching optimal NPV.
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

    """

    rack_per_zone_float = DCTotal/(number_of_zones*rack_params['Modules_per_rack']*module_params['STC']/1e6)
    rack_per_zone_init = round(rack_per_zone_float)
    rack_interval = round(rack_per_zone_float*rack_interval_ratio)
    # Rack interval needs to be equal of greater than
    if rack_interval < 1:
        rack_interval = 1
    rack_num_range = pd.Series(range(rack_per_zone_init - 5 * rack_interval, rack_per_zone_init + 6 * rack_interval,
                                     rack_interval))

    rack_num_range.drop(rack_num_range.index[(rack_num_range < 0)], inplace=True)
    rack_num_range = rack_num_range.reindex()
    # drop any negative values which may result due to inappropriate rack_interval_ratio

    module_num_range = rack_num_range * rack_params['Modules_per_rack']

    # Raise an error if any of the gcr_range is more than 1.
    if rack_params['rack_type'] == 'SAT':
        gcr_range = module_params['A_c']*module_num_range/zone_area
    elif rack_params['rack_type'] == 'east_west':
        gcr_range = rack_num_range*rack_params['Area'] * np.cos(10 * np.pi/180)/zone_area  # multiply by cos(10)
    else:
        raise ValueError('unrecognised rack type')

    return rack_num_range, module_num_range, gcr_range


def get_revenue(Yieldseries,
                export_limit,
                price_schedule,
                storage_capacity):
    """
    Function to determine revenue generation from yield,
    At present very simple, future iterations will need storage
    capacity and operation
    The function assumes all DC power smaller than export limit is exported and all DC power greater than export limit
    is stored. This assumption may need to be revisited in the future as per info from SunCable.
    :param Yieldseries:
    :param Trans_limit:
    :param price_schedule:
    :return:
    """

    Direct_Export = Yieldseries.clip(lower=None, upper=export_limit)
    Store_Avail = Yieldseries-Direct_Export
    Daily_store_pot = Store_Avail.groupby(Store_Avail.index.date).sum()
    Daily_store = Daily_store_pot.clip(lower=None, upper=storage_capacity)
    Direct_Revenue = Direct_Export*price_schedule
    Store_Revenue = Daily_store*price_schedule*0.85
    Store_Revenue.index = pd.to_datetime(Store_Revenue.index)
    Yearly_direct = Direct_Revenue.groupby(Direct_Revenue.index.year).sum()
    Yearly_storage = Store_Revenue.groupby(Store_Revenue.index.year).sum()
    Yearly_total = Yearly_direct+Yearly_storage

    return Yearly_direct, Yearly_storage, Yearly_total

def get_costs(num_of_racks, rack_params, module_params, data_tables, install_year=2025):

   """
   Function to return a yearly timeseries of costs for installing different numbers of racks
   :param num_of_racks:
   :param rack_params:
   :param module_params:
   :param install_year:
   :return:
   """

   # Option 3 Call code directly and overwrite values as required
   ScenarioList = {'Scenario_Name': num_of_racks,
                   'ScenarioID': num_of_racks, 'Scenario_Tag': num_of_racks}

   SCNcostdata = pd.DataFrame(ScenarioList, columns=[
       'Scenario_Name', 'ScenarioID', 'Scenario_Tag'])

   SystemLinkracks = {'ScenarioID': num_of_racks, 'ScenarioSystemID': num_of_racks, 'InstallNumber': num_of_racks,
                      'SystemID': num_of_racks, 'InstallDate': num_of_racks}

   SYScostracks = pd.DataFrame(SystemLinkracks, columns=[
       'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])

   SystemLinkfixed = {'ScenarioID': num_of_racks, 'ScenarioSystemID': num_of_racks, 'InstallNumber': num_of_racks,
                      'SystemID': num_of_racks, 'InstallDate': num_of_racks}

   SYScostfixed = pd.DataFrame(SystemLinkfixed, columns=[
       'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])

   if rack_params['rack_type'] == 'SAT':
       SYScostracks['SystemID'] = 13
       SYScostfixed['SystemID'] = 14
   elif rack_params['rack_type'] == 'east_west':
       SYScostracks['SystemID'] = 17
       SYScostfixed['SystemID'] = 19

   SYScostracks['InstallDate'] = install_year

   SYScostfixed['InstallDate'] = install_year
   SYScostfixed['InstallNumber'] = 1

   SYScostData = SYScostracks.append(SYScostfixed)

   SYScostData['ScenarioSystemID'] = range(1, 2 * len(num_of_racks) + 1)

   # Airtable Import
   # api_key = 'keyJSMV11pbBTdswc'
   # base_id = 'appjQftPtMrQK04Aw'

   # data_tables = Suncost.import_airtable_data(base_id=base_id, api_key=api_key)
   scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list = data_tables

   # Replacing some tables from specified inputs
   new_data_tables = SCNcostdata, SYScostData, system_list, system_component_link, component_list, currency_list, costcategory_list

   # Running the cost calculations
   # outputs = SunCost.CalculateScenarios (data_tables, year_start=2024, analyse_years=30)
   costoutputs = Suncost.CalculateScenarios(new_data_tables, year_start=2024, analyse_years=30)
   component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = costoutputs

   return costoutputs


def get_airtable():
    """

    :return:
    """

    # Airtable Import
    api_key = 'keyJSMV11pbBTdswc'
    base_id = 'appjQftPtMrQK04Aw'

    data_tables = Suncost.import_airtable_data(base_id=base_id, api_key=api_key)

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
            discount_rate=0.07):
    """
    Function to determine the npv from a time series (yearly)
    of costs and revenue
    :param yearly_costs:
    :param yearly_revenue:
    :return:
    """
    net_cashflow = yearly_revenue-yearly_costs.values

    Yearoffset = pd.Series(range(0, len(net_cashflow)))
    Yearoffset.index = net_cashflow.index

    YearlyFactor = 1 / (1 + discount_rate) ** Yearoffset
    YearlyNPV = net_cashflow.mul(YearlyFactor, axis=0)
    Yearly_NPV_costs = yearly_costs.mul(YearlyFactor, axis=0)
    Yearly_NPV_revenue = yearly_revenue.mul(YearlyFactor, axis=0)

    NPV = YearlyNPV.sum(axis=0)
    NPV_costs = Yearly_NPV_costs.sum(axis=0)
    NPV_revenue = Yearly_NPV_revenue.sum(axis=0)

    return NPV, YearlyNPV, NPV_costs, NPV_revenue, Yearly_NPV_revenue, Yearly_NPV_costs

def get_mcanalysis(num_of_racks, rack_params, module_params, data_tables, install_year=2025):

    """
    Function to return monte-carlo generated set of cost outputs and data
    :param num_of_racks:
    :param rack_params:
    :param module_params:
    :param data_tables:
    :param install_year:
    :return:
    """
    ScenarioList = {'Scenario_Name': num_of_racks,
                    'ScenarioID': num_of_racks, 'Scenario_Tag': num_of_racks}

    SCNcostdata = pd.DataFrame(ScenarioList, columns=[
        'Scenario_Name', 'ScenarioID', 'Scenario_Tag'])

    SystemLinkracks = {'ScenarioID': num_of_racks, 'ScenarioSystemID': num_of_racks, 'InstallNumber': num_of_racks,
                       'SystemID': num_of_racks, 'InstallDate': num_of_racks}

    SYScostracks = pd.DataFrame(SystemLinkracks, columns=[
        'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])

    SystemLinkfixed = {'ScenarioID': num_of_racks, 'ScenarioSystemID': num_of_racks, 'InstallNumber': num_of_racks,
                       'SystemID': num_of_racks, 'InstallDate': num_of_racks}

    SYScostfixed = pd.DataFrame(SystemLinkfixed, columns=[
        'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])

    if rack_params['rack_type'] == 'SAT':
        SYScostracks['SystemID'] = 13
        SYScostfixed['SystemID'] = 14
    elif rack_params['rack_type'] == 'east_west':
        SYScostracks['SystemID'] = 17
        SYScostfixed['SystemID'] = 19

    SYScostracks['InstallDate'] = install_year

    SYScostfixed['InstallDate'] = install_year
    SYScostfixed['InstallNumber'] = 1

    SYScostData = SYScostracks.append(SYScostfixed)

    SYScostData['ScenarioSystemID'] = range(1, 2 * len(num_of_racks) + 1)

    scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list = data_tables

    # Replacing some tables from specified inputs
    new_data_tables = SCNcostdata, SYScostData, system_list, system_component_link, component_list, currency_list, costcategory_list

    # Run iterative monte-carlo analysis for specified system
    data_tables_iter = Suncost.create_iteration_tables(new_data_tables, 500, iteration_start=0)

    outputs_iter = Suncost.CalculateScenariosIterations(data_tables_iter, year_start=2024, analyse_years=30)

    component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, cash_flow_by_year_iter = outputs_iter

    return component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, cash_flow_by_year_iter, data_tables_iter


