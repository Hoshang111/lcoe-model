# %% Import
import pandas as pd
import Functions.simulation_functions as func
import Functions.sizing_functions as sizing
import Functions.plotting_functions as plot_func
import Functions.testing as testing

def get_tilts():
    """"""



def optimise_layout(weather_simulation, rack_params, module_params, land_area,
                    temp_model, export_lim, storage_capacity, scheduled_price,
                    data_tables, discount_rate, fig_title=None):


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
    LCOE, kWh_discounted = sizing.get_lcoe(cash_flow_by_year, kWh_series)
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
        LCOE, kWh_discounted = sizing.get_lcoe(cash_flow_by_year, kWh_series)
        iteration += 1
        if iteration >= 11:
            break