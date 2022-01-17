# %% Import
import pandas as pd
import numpy as np
import Simulation_functions as func
import airtable
import sizing
import Plotting as plot_func


def optimise_layout(weather_simulation, rack_type, module_type, install_year,
                     DCTotal, num_of_zones, zone_area, rack_interval_ratio, temp_model,
                     export_lim, storage_capacity, scheduled_price,
                     data_tables, discount_rate):

    """
    Optimise layout function converts the 'MAIN' script into a function form to run Monte Carlo simulations
    within 'MAIN_MonteCarlo' script. The use of variables are similar with the MAIN script.
    """

    # %% ======================================
    # Rack_module
    rack_params, module_params = func.rack_module_params(rack_type, module_type)

    # %%
    # Sizing/rack and module numbers
    # Call the constants from the database - unneeded if we just pass module class?
    rack_per_zone_num_range, module_per_zone_num_range, gcr_range = func.get_racks(DCTotal, num_of_zones, module_params,
                                                                                 rack_params, zone_area, rack_interval_ratio)
    # %% ========================================
    # DC yield

    dc_results, dc_df, dc_size = func.dc_yield(DCTotal, rack_params, module_params, temp_model, weather_simulation,
                                               rack_per_zone_num_range, module_per_zone_num_range, gcr_range, num_of_zones)


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
    LCOE, kWh_discounted = sizing.get_LCOE(cash_flow_by_year, kWh_series)
    # %% =======================================
    # Simulations to find optimum NPV according to number of racks per zone

    rack_interval = rack_per_zone_num_range[2]-rack_per_zone_num_range[1]
    num_of_zones_sim = 1  # find the results per zone for now
    npv_array = []
    npv_cost_array = []
    npv_revenue_array = []
    gcr_range_array = []
    rack_per_zone_num_range_array = []
    iteration = 1

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
        dc_results, dc_df, dc_size = func.dc_yield(DCpower_min, rack_params, module_params, temp_model, weather_simulation,
                                                   rack_per_zone_num_range, module_per_zone_num_range, gcr_range,
                                                   num_of_zones)
        kWh_export, direct_revenue, store_revenue, total_revenue = sizing.get_revenue(dc_df, export_lim, scheduled_price, storage_capacity)
        cost_outputs = sizing.get_costs(rack_per_zone_num_range, rack_params, module_params, data_tables, install_year=install_year)
        component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = cost_outputs
        kWh_series = sizing.align_cashflows(cash_flow_by_year, kWh_export)
        revenue_series = sizing.align_cashflows(cash_flow_by_year, total_revenue)
        npv, yearly_npv, npv_cost, npv_revenue, Yearly_NPV_revenue, Yearly_NPV_costs = sizing.get_npv(cash_flow_by_year, revenue_series, discount_rate)
        LCOE, kWh_discounted = sizing.get_LCOE(cash_flow_by_year, kWh_series)
        iteration += 1
        if iteration >= 11:
            break
    # %% ==========================================
    # Plotting NPV, GCR_range, NPV_cost, NPV_revenue
    plot_func.plot_npv(rack_per_zone_num_range_array, npv_array, gcr_range_array, npv_cost_array, npv_revenue_array,
                       rack_params['Modules_per_rack'], module_params['STC'])

    # %% ================================================
    # Find optimum number of racks and create tables for Monte Carlo Analysis
    racks_per_zone_max = npv.idxmax()
    rpzm_series = pd.Series(racks_per_zone_max)
    cost_outputs, table_outputs = sizing.get_costs_and_tables(rpzm_series, rack_params, module_params, data_tables, install_year=install_year)

    revenue_output = revenue_series[racks_per_zone_max]
    kWh_output = kWh_series[racks_per_zone_max]

    return table_outputs, revenue_output, kWh_output


def form_new_data_tables(data_tables, scenarios):
    """
    Transform two sets of scenario tables into a new set which includes both SAT and MAV (or more)
    :param data_tables:
    :param scenarios:
    :return:
    """
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
        combined_SCNcostdata = combined_SCNcostdata.append(SCNcostdata)
        combined_SYScostdata = combined_SYScostdata.append(SYScostdata)

    combined_SYScostdata['ScenarioSystemID'] = range(0, combined_SYScostdata.shape[0])

    # Replacing some tables from specified inputs
    new_data_tables = combined_SCNcostdata, combined_SYScostdata, system_list, system_component_link, component_list, currency_list, costcategory_list

    return new_data_tables









