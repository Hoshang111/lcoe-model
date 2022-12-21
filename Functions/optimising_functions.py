


""" This is the main script for the yield assessment. The script calls the functions below to calculate the Net Present Value
(NPV) of the solar farm
1) Weather:
Input: Weather file, year of simulation
Output: Weather dataframe in the required format for PVlib simulatins
2) Racks & modules:
Input: Type of module and rack
Output: Module and rack parameters required for PVlib PVsystem extracted from the module & rack database
3) Sizing
Input: DC size of the solar farm
Output: Configuration in terms of number of single-axis tracking (SAT) racks or 5B Maverick units (MAV)
4) DC/AC Yield:
Input: number of racks, number of MAVs, weather data, module name, mounting type (optional & future improvement:
temperature rack type, aoi model, back-tracking/optimal tilt angle)
Output: DC/AC yield
5) Revenue and storage behaviour
Input: DC yield, export limit
Output: Revenue
6) Cost (get deterministic or monte-carlo cost distribution of the solar farm)
Input: DC size pf the solar farm
Output: Cost
7) Net present value (NPV)
Input: Revenue, Cost
Output: NPV
Initially, we will write the Main script to call out all these functions to give a NPV
Later, we will convert this to an optimization process which will give the optimum NPV based on:
- Configuration
- Mounting
- Other parameters (more advanced params like back tracking algo, temp/racking type etc.)
During the optimisation process/simulations, cost function will give deterministic values. Once the optimum NPV is found
cost function also give the Monte-Carlo distribution.
"""

# %% Import
import pandas as pd
import numpy as np
import Functions.simulation_functions as func
import Functions.sizing_functions as sizing
import Functions.plotting_functions as plot_func
import Functions.testing as testing

# mpl.use('Qt5Agg')

def optimise_layout(weather_simulation, rack_type, module_type, install_year,
                     DCTotal, num_of_zones, zone_area, rack_interval_ratio, temp_model,
                     export_lim, storage_capacity, scheduled_price,
                     data_tables, discount_rate, loss_params, set_racks=False, number_racks=0,
                     fig_title=None):

    # %% ======================================
    # Rack_module
    rack_params, module_params = func.rack_module_params(rack_type, module_type)

    # %% =======================================
    # statement to allow users to define number of racks
    if set_racks:
        rack_per_zone_num_range = number_racks
        module_per_zone_num_range = rack_per_zone_num_range * rack_params['Modules_per_rack']
        if rack_params['rack_type'] == 'SAT':
            gcr_range = module_params['A_c'] * module_per_zone_num_range / zone_area
        elif rack_params['rack_type'] == 'east_west':
            gcr_range = rack_per_zone_num_range * rack_params['Area'] * np.cos(
                10 * np.pi / 180) / zone_area  # edited to have values as mucks up later graphs
        elif rack_params['rack_type'] == 'east_west_future':  # if we start taking inter-row spacing into acount for mav
            # in the future
            gcr_range = rack_per_zone_num_range * rack_params['Area'] * np.cos(
                10 * np.pi / 180) / zone_area  # multiply by cos(10)
        else:
            raise ValueError('unrecognised rack type')
    else:
        rack_per_zone_num_range, module_per_zone_num_range, gcr_range = func.get_racks(DCTotal, num_of_zones, module_params,
                                                                                 rack_params, zone_area, rack_interval_ratio)
    # %% ========================================
    # DC yield

    dc_results, dc_initial, dc_size = func.dc_yield(DCTotal, rack_params, module_params, temp_model, weather_simulation,
                                               rack_per_zone_num_range, module_per_zone_num_range, gcr_range, num_of_zones)

    # %% =========================================
    # Apply losses to dc timeseries
    default_soiling = [(1, 0.001), (2, 0.002), (3, 0.004), (4, 0.007), (5, 0.011), (6, 0.015), (7, 0.02), (8, 0.026),
                       (9, 0.027), (10, 0.027), (11, 0.015), (12, 0.002)]
    temp_coefficient = -0.01
    loss_factor = func.get_dcloss(loss_params, weather_simulation, default_soiling, temp_coefficient)
    dc_df = dc_initial.mul(loss_factor, axis=0)

    #%% ==========================================
    # Revenue and storage behaviour

    kWh_export, direct_revenue, store_revenue, total_revenue = sizing.get_revenue(dc_df, export_lim, scheduled_price, storage_capacity)

    #%% ==========================================
    # Cost

    cost_outputs = sizing.get_costs(rack_per_zone_num_range, rack_params, module_params, data_tables, install_year=install_year)
    component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = cost_outputs
    #%% ==========================================
    # Net present value (NPV)
    # resize yield output to match cost time series
    kWh_series = sizing.align_cashflows(cash_flow_by_year, kWh_export)
    revenue_series = sizing.align_cashflows(cash_flow_by_year, total_revenue)

    # ==========================================
    npv, yearly_npv, npv_cost, npv_revenue, Yearly_NPV_revenue, Yearly_NPV_costs = sizing.get_npv(cash_flow_by_year, revenue_series, discount_rate)
    LCOE, kWh_discounted = sizing.get_lcoe(cash_flow_by_year, kWh_series)
    # %% =======================================
    # Simulations to find optimum NPV according to number of racks per zone

    if set_racks:
        rack_interval = 0.1
    else:
        rack_interval = rack_per_zone_num_range[2]-rack_per_zone_num_range[1]

    num_of_zones_sim = 1  # find the results per zone for now
    npv_array = []
    npv_cost_array = []
    npv_revenue_array = []
    gcr_range_array = []
    rack_per_zone_num_range_array = []
    iteration = 1

    if set_racks:
        rack_interval = 0.1

    while rack_interval > 1:
        print('Max NPV is %d' % npv.max())
        print('Iteration = %d' % iteration)
        npv_array.append(npv)
        npv_cost_array.append(npv_cost)
        npv_revenue_array.append(npv_revenue)
        gcr_range_array.append(gcr_range)
        rack_per_zone_num_range_array.append(rack_per_zone_num_range)
        index_max = npv.idxmax()
        DCpower_min = index_max * rack_params['Modules_per_rack'] * module_params['STC'] / 1e6
        new_interval_ratio = rack_interval / index_max / 5
        if index_max == npv.index[0] or index_max == npv.index[10]:
            new_interval_ratio = 0.04

        rack_per_zone_num_range, module_per_zone_num_range, gcr_range = func.get_racks(DCpower_min, num_of_zones_sim,
                                                                                       module_params, rack_params, zone_area,
                                                                                       new_interval_ratio)
        rack_interval = rack_per_zone_num_range[2] - rack_per_zone_num_range[1]
        dc_results, dc_initial, dc_size = func.dc_yield(DCpower_min, rack_params, module_params, temp_model, weather_simulation,
                                                   rack_per_zone_num_range, module_per_zone_num_range, gcr_range,
                                                   num_of_zones)
        loss_factor = func.get_dcloss(loss_params, weather_simulation, default_soiling, temp_coefficient)
        dc_df = dc_initial.mul(loss_factor, axis=0)
        kWh_export, direct_revenue, store_revenue, total_revenue = sizing.get_revenue(dc_df, export_lim, scheduled_price, storage_capacity)
        cost_outputs = sizing.get_costs(rack_per_zone_num_range, rack_params, module_params, data_tables, install_year=install_year)
        component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = cost_outputs
        kWh_series = sizing.align_cashflows(cash_flow_by_year, kWh_export)
        revenue_series = sizing.align_cashflows(cash_flow_by_year, total_revenue)
        npv, yearly_npv, npv_cost, npv_revenue, Yearly_NPV_revenue, Yearly_NPV_costs = sizing.get_npv(cash_flow_by_year, revenue_series, discount_rate)
        LCOE, kWh_discounted = sizing.get_lcoe(cash_flow_by_year, kWh_series)
        iteration += 1
        if iteration >= 11:
            break
    # %% ==========================================
    # Plotting NPV, GCR_range, NPV_cost, NPV_revenue
    plot_func.plot_npv(rack_per_zone_num_range_array, npv_array, gcr_range_array, npv_cost_array, npv_revenue_array,
                       rack_params['Modules_per_rack'], module_params['STC'], fig_title=fig_title)

    # %% ================================================
    # Find optimum number of racks and create tables for Monte Carlo Analysis
    racks_per_zone_max = npv.idxmax()

    rpzm_series = pd.Series(racks_per_zone_max)
    #cost_outputs, table_outputs = sizing.get_costs_and_tables(rpzm_series, rack_params, module_params, data_tables, install_year=install_year)
    cost_outputs, table_outputs = sizing.get_costs(rpzm_series, rack_params, module_params, data_tables,
                                                   install_year=install_year, return_table_outputs = True)

    revenue_output = revenue_series[racks_per_zone_max]
    kWh_output = kWh_series[racks_per_zone_max]
    npv_output = npv[racks_per_zone_max]
    return table_outputs, revenue_output, kWh_output, npv_output, module_params, rack_params


def form_new_data_tables(data_tables, scenarios):
    # Transform two sets of scenario tables into a new set which includes both SAT and MAV (or more)
    scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list = data_tables

    combined_SCNcostdata = pd.DataFrame()
    combined_SYScostdata = pd.DataFrame()
    for (data, scenario_label) in scenarios:
        SCNcostdata, SYScostdata = data
        # Find the old ScenarioID
        if SCNcostdata.shape[0] == 1:
            old_scenario_ID = SCNcostdata['ScenarioID'].values[0]
            SCNcostdata['ScenarioID'] = scenario_label

            # Check if SYScostdata has any other scenarios
            if SYScostdata[SYScostdata['ScenarioID']==old_scenario_ID].shape[0] == SYScostdata.shape[0]:
                SYScostdata['ScenarioID'] = scenario_label
            else:
                print('Error! SYScostdata has multiple scenarios')
        else:
            print('Error! Zero or Multiple Scenarios')
        combined_SCNcostdata = pd.concat([combined_SCNcostdata,SCNcostdata])
        combined_SYScostdata = pd.concat([combined_SYScostdata,SYScostdata])

    combined_SYScostdata['ScenarioSystemID'] = range(0, combined_SYScostdata.shape[0])

    # Replacing some tables from specified inputs
    new_data_tables = combined_SCNcostdata, combined_SYScostdata, system_list, system_component_link, component_list, currency_list, costcategory_list

    return new_data_tables

def extract_cost_tables(scenarios):
    # Transform two sets of scenario tables into a new set which includes both SAT and MAV (or more)


    extracted_scenario_list = pd.DataFrame()
    extracted_scenario_system_link = pd.DataFrame()
    for (data, scenario_label) in scenarios:
        SCNcostdata, SYScostdata = data
        # Find the old ScenarioID
        if SCNcostdata.shape[0] == 1:
            old_scenario_ID = SCNcostdata['ScenarioID'].values[0]
            SCNcostdata['ScenarioID'] = scenario_label

            # Check if SYScostdata has any other scenarios
            if SYScostdata[SYScostdata['ScenarioID']==old_scenario_ID].shape[0] == SYScostdata.shape[0]:
                SYScostdata['ScenarioID'] = scenario_label
            else:
                print('Error! SYScostdata has multiple scenarios')
        else:
            print('Error! Zero or Multiple Scenarios')
        extracted_scenario_list = pd.concat([extracted_scenario_list, SCNcostdata])
        extracted_scenario_system_link = pd.concat([extracted_scenario_system_link,SYScostdata])

    extracted_scenario_system_link['ScenarioSystemID'] = range(0, extracted_scenario_system_link.shape[0])


    return extracted_scenario_list, extracted_scenario_system_link

def analyse_layout(weather_simulation, rack_type, module_type, install_year,
                     DCTotal, num_of_zones, zone_area, temp_model,
                     export_lim, storage_capacity, scheduled_price,
                     data_tables, discount_rate, first_year_degradation,
                     degradation_rate, fig_title=None):
    """
    :param weather_simulation:
    :param rack_type:
    :param module_type:
    :param install_year:
    :param DCTotal:
    :param num_of_zones:
    :param zone_area:
    :param temp_model:
    :param export_lim:
    :param storage_capacity:
    :param scheduled_price:
    :param data_tables:
    :param discount_rate:
    :param first_year_degradation:
    :param degradation_rate:
    :param fig_title:
    :return:
    """

    # %% ======================================
    # Rack_module
    rack_params, module_params = func.rack_module_params(rack_type, module_type)

    # %%
    # Sizing/rack and module numbers
    # Call the constants from the database - unneeded if we just pass module class?
    rack_per_zone_num_range, module_per_zone_num_range, gcr_range = func.get_racks(DCTotal, num_of_zones, module_params,
                                                                                 rack_params, zone_area, 0.1)
    # %% ========================================
    # DC yield

    dc_results, dc_df, dc_size = func.dc_yield(DCTotal, rack_params, module_params, temp_model, weather_simulation,
                                               rack_per_zone_num_range, module_per_zone_num_range, gcr_range, num_of_zones)


    #%% ==========================================
    # Cost

    cost_outputs = sizing.get_costs(rack_per_zone_num_range, rack_params, module_params, data_tables, install_year=install_year)
    component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = cost_outputs

    #%% ==========================================
    # resize yield output to match cost time series and apply degradation
    kWh_series, test_index = testing.align_years(dc_df, cash_flow_by_year)
    degradation_factor, kWh_degraded = testing.apply_degradation(kWh_series, first_year_degradation, degradation_rate)

    # %% ==========================================
    # Revenue and storage behaviour
    kWh_export, direct_revenue, store_revenue, revenue_series = sizing.get_revenue(kWh_degraded, export_lim, scheduled_price, storage_capacity)

    # %% ==========================================
    # Net present value (NPV)

    npv, yearly_npv, npv_cost, npv_revenue, Yearly_NPV_revenue, Yearly_NPV_costs = sizing.get_npv(cash_flow_by_year, revenue_series, discount_rate)
    LCOE, kWh_discounted = sizing.get_lcoe(cash_flow_by_year, kWh_export)

    return kWh_series, test_index, dc_df, kWh_degraded, degradation_factor, LCOE, kWh_export, revenue_series









