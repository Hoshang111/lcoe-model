""" This is part 1 of 2 steps for Monte-Carlo Analysis. This step will calculate the
optimized layout for a set of default parameters and export this to a pickl file. This file
can then be used for full Monte-Carlo analysis including both yield and costs
"""

# %% Import
import random
import sqlite3
import sys

sys.path.append('..')
import pandas as pd
import numpy as np
import os
import Functions.simulation_functions as func
from Functions.optimising_functions import form_new_data_tables, optimise_layout
from Functions.sizing_functions import get_airtable, get_npv
from Functions.cost_functions import calculate_scenarios_iterations, create_iteration_tables, \
    generate_parameters, calculate_variance_contributions, import_excel_data
import warnings
from Functions.mc_yield_functions import weather_sort, generate_mc_timeseries, get_yield_datatables
import _pickle as cpickle

# This suppresses a divide be zero warning message that occurs in pvlib tools.py.
warnings.filterwarnings(action='ignore',
                        message='divide by zero encountered in true_divide*')
# %%
# Set overall conditions for this analysis

use_previous_airtable_data = False


def run(file_name):
    # Get inputs from filename
    parameters = []
    conn = sqlite3.connect(file_name)
    cur = conn.cursor()
    cur.execute("SELECT INPUT FROM INPUTS")
    inputs = cur.fetchall()
    for i in inputs:
        parameters.append(i[0])

    # Sizing/rack and module numbers
    # Call the constants from the database - unneeded if we just pass module class?
    DCTotal = int(parameters[0])  # DC size in MW
    num_of_zones = int(parameters[1])  # Number of smaller zones that will make up the solar farm
    zone_area = int(parameters[2])  # Zone Area in m2
    rack_interval_ratio = float(parameters[3])
    # Yield Assessment Inputs
    temp_model = str(parameters[4])  # choose a temperature model either Sandia: 'sapm' or PVSyst: 'pvsyst'

    # Revenue and storage behaviour
    export_lim = float(parameters[5])  # Watts per zone
    storage_capacity = int(parameters[6])  # Wh per zone
    scheduled_price = float(parameters[7])  # AUD / Wh. Assumption: AUD 4c/kWh (conversion from Wh to kWh)

    # Financial Parameters
    discount_rate = float(parameters[8])

    # Optimising Parameters
    year_sc1 = int(parameters[9])
    mount_tech_sc1 = str(parameters[10])
    module_tech_sc1 = str(parameters[11])
    year_sc2 = int(parameters[12])
    mount_tech_sc2 = str(parameters[13])
    module_tech_sc2 = str(parameters[14])
    iter_limit = int(parameters[15])

    # Weather
    simulation_years = np.arange(2007, 2022, 1)
    weather_dnv_file = 'SunCable_TMY_HourlyRes_bifacial_545_4m_result.csv'
    weather_file = 'Solcast_PT60M.csv'
    weather_solcast = func.weather(simulation_years, weather_file)
    weather_solcast_simulation = weather_solcast['2010-01-01':'2010-12-31']

    # Complete set of dnv weather data you can extract specific years for simulations later on
    weather_dnv = func.weather_benchmark_adjustment_mk2(weather_solcast_simulation, weather_dnv_file)

    weather_dnv.index = weather_dnv.index.tz_localize('Australia/Darwin')

    # %% Now create a new weather data for DNV with simulated dni and simulate with this weather data...
    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)
    dni_dummy = pd.read_csv(os.path.join(parent_path, 'Data', 'WeatherData', 'TMY_dni_simulated_1minute.csv'),
                            index_col=0)
    dni_dummy.set_index(pd.to_datetime(dni_dummy.index, utc=False), drop=True, inplace=True)
    dni_dummy.index = dni_dummy.index.tz_convert('Australia/Darwin')

    weather_dnv.drop(['dni'], axis=1, inplace=True)
    weather_dnv = weather_dnv.join(dni_dummy, how='left')
    weather_dnv.rename(columns={"0": "dni"}, inplace=True)
    weather_dnv = weather_dnv[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed', 'precipitable_water', 'dc_yield']]

    # shift weather files 30 min so that solar position is calculated at midpoint of period
    weather_dnv_mod = weather_dnv.shift(periods=30, freq='T')
    weather_simulation = weather_dnv_mod

    if use_previous_airtable_data:
        data_tables = import_excel_data('CostDatabaseFeb2022a.xlsx')
    else:
        # cost data tables from airtable
        data_tables = get_airtable(save_tables=True)

    input_data = [['temp_model', 'storage_capacity', 'scheduled_price', 'export_lim',
                   'discount_rate', 'zone_area', 'num_of_zones'],
                  [temp_model, storage_capacity, scheduled_price, export_lim,
                   discount_rate, zone_area, num_of_zones]]

    input_df = pd.DataFrame(input_data)
    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)
    file_name = os.path.join(parent_path, 'OutputFigures', 'input_params.csv')
    input_df.to_csv(file_name, index=False, header=False)

    yield_datatables = get_yield_datatables(10)
    MAV_loss_params = yield_datatables[0].iloc[0]
    SAT_loss_params = yield_datatables[1].iloc[0]

    # %%
    # Cycle through alternative analysis scenarios

    def optimize(RACK_TYPE, MODULE_TYPE, INSTALL_YEAR, SCENARIO_LABEL, scenario_tables_combined, loss_params):
        module_type = MODULE_TYPE
        install_year = INSTALL_YEAR
        rack_type = RACK_TYPE

        scenario_tables_optimum, revenue, kWh_export, npv_output, rack_params, module_params = optimise_layout(
            weather_simulation, rack_type, module_type,
            install_year, DCTotal, num_of_zones, zone_area,
            rack_interval_ratio, temp_model, export_lim,
            storage_capacity, scheduled_price, data_tables,
            discount_rate, loss_params, fig_title=SCENARIO_LABEL)

        scenario_tables_combined.append((scenario_tables_optimum, SCENARIO_LABEL))

        return SCENARIO_LABEL, scenario_tables_optimum, revenue, kWh_export, npv_output, rack_params, module_params

    # Create variables to hold the results of each analysis
    SAT = 'SAT_1_update'
    MAV = '5B_MAV_update'
    PERC2023 = 'PERC_2023_M10'
    TOP2023 = 'TOPCON_2023_M10'
    HJT2023 = 'HJT_2023_M10'
    PERC2025 = 'PERC_2025_M10'
    TOP2025 = 'TOPCON_2025_M10'
    HJT2025 = 'HJT_2025_M10'
    PERC2028 = 'PERC_2028_M10'
    TOP2028 = 'TOPCON_2028_M10'
    HJT2028 = 'HJT_2028_M10'
    PERC2031 = 'PERC_2031_M10'
    TOP2031 = 'TOPCON_2031_M10'
    HJT2031 = 'HJT_2031_M10'

    #
    # 2024 - assume modules PERC_2023_M10, etc
    # 2024 - assume modules PERC_2025_M10, etc

    # 2026 - assume modules PERC_2025_M10, etc
    # 2026 - assume modules PERC_2028_M10, etc

    # 2028 - assume modules PERC_2028_M10, etc
    # 2028 - assume modules PERC_2031_M10, etc

    scenario_1 = [year_sc1, mount_tech_sc1, module_tech_sc2]
    scenario_2 = [year_sc2, mount_tech_sc2, module_tech_sc2]
    scenario_params = [scenario_1, scenario_2]
    scenario_tables_2024 = []
    scenario_tables_2026 = []
    scenario_tables_2028 = []


    for scenario in scenario_params:
        year = scenario[0]
        mount_tech = scenario[1]
        module_tech = scenario[2]
        if year == 2024:
            if mount_tech == "SAT":
                if module_tech == "PERC":
                    results_SAT_PERC_2024 = optimize(SAT, PERC2023, 2024, 'SAT_PERC_2024', scenario_tables_2024,
                                                     SAT_loss_params)
                    results_SAT_PERCa_2024 = optimize(SAT, PERC2025, 2024, 'SAT_PERCa_2024', scenario_tables_2024,
                                                      SAT_loss_params)
                elif module_tech == "HJT":
                    results_SAT_HJT_2024 = optimize(SAT, HJT2023, 2024, 'SAT_HJT_2024', scenario_tables_2024,
                                                    SAT_loss_params)
                    results_SAT_HJTa_2024 = optimize(SAT, HJT2025, 2024, 'SAT_HJTa_2024', scenario_tables_2024,
                                                     SAT_loss_params)
                elif module_tech == "TOPCON":
                    results_SAT_TOP_2024 = optimize(SAT, TOP2023, 2024, 'SAT_TOP_2024', scenario_tables_2024,
                                                    SAT_loss_params)
                    results_SAT_TOPa_2024 = optimize(SAT, TOP2025, 2024, 'SAT_TOPa_2024', scenario_tables_2024,
                                                     SAT_loss_params)
            elif mount_tech == "MAV":
                if module_tech == "PERC":
                    results_MAV_PERC_2024 = optimize(MAV, PERC2023, 2024, 'MAV_PERC_2024', scenario_tables_2024,
                                                     MAV_loss_params)
                    results_MAV_PERCa_2024 = optimize(MAV, PERC2025, 2024, 'MAV_PERCa_2024', scenario_tables_2024,
                                                      MAV_loss_params)
                if module_tech == "HJT":
                    results_MAV_HJT_2024 = optimize(MAV, HJT2023, 2024, 'MAV_HJT_2024', scenario_tables_2024,
                                                    MAV_loss_params)
                    results_MAV_HJTa_2024 = optimize(MAV, HJT2025, 2024, 'MAV_HJTa_2024', scenario_tables_2024,
                                                     MAV_loss_params)
                if module_tech == "TOPCON":
                    results_MAV_TOP_2024 = optimize(MAV, TOP2023, 2024, 'MAV_TOP_2024', scenario_tables_2024,
                                                    MAV_loss_params)
                    results_MAV_TOPa_2024 = optimize(MAV, TOP2025, 2024, 'MAV_TOPa_2024', scenario_tables_2024,
                                                     MAV_loss_params)
        elif year == 2026:
            if mount_tech == "SAT":
                if module_tech == "PERC":
                    results_SAT_PERC_2026 = optimize(SAT, PERC2025, 2026, 'SAT_PERC_2026', scenario_tables_2026,
                                                     SAT_loss_params)
                    results_SAT_PERCa_2026 = optimize(SAT, PERC2028, 2026, 'SAT_PERCa_2026', scenario_tables_2026,
                                                      SAT_loss_params)
                elif module_tech == "HJT":
                    results_SAT_HJT_2026 = optimize(SAT, HJT2025, 2026, 'SAT_HJT_2026', scenario_tables_2026,
                                                    SAT_loss_params)
                    results_SAT_HJTa_2026 = optimize(SAT, HJT2028, 2026, 'SAT_HJTa_2026', scenario_tables_2026,
                                                     SAT_loss_params)
                elif module_tech == "TOPCON":
                    results_SAT_TOP_2026 = optimize(SAT, TOP2025, 2026, 'SAT_TOP_2026', scenario_tables_2026,
                                                    SAT_loss_params)
                    results_SAT_TOPa_2026 = optimize(SAT, TOP2028, 2026, 'SAT_TOPa_2026', scenario_tables_2026,
                                                     SAT_loss_params)
            elif mount_tech == "MAV":
                if module_tech == "PERC":
                    results_MAV_PERC_2026 = optimize(MAV, PERC2025, 2026, 'MAV_PERC_2026', scenario_tables_2026,
                                                     MAV_loss_params)
                    results_MAV_PERCa_2026 = optimize(MAV, PERC2028, 2026, 'MAV_PERCa_2026', scenario_tables_2026,
                                                      MAV_loss_params)
                if module_tech == "HJT":
                    results_MAV_HJT_2026 = optimize(MAV, HJT2025, 2026, 'MAV_HJT_2026', scenario_tables_2026,
                                                    MAV_loss_params)
                    results_MAV_HJTa_2026 = optimize(MAV, HJT2028, 2026, 'MAV_HJTa_2026', scenario_tables_2026,
                                                     MAV_loss_params)
                if module_tech == "TOPCON":
                    results_MAV_TOP_2026 = optimize(MAV, TOP2025, 2026, 'MAV_TOP_2026', scenario_tables_2026,
                                                    MAV_loss_params)
                    results_MAV_TOPa_2026 = optimize(MAV, TOP2028, 2026, 'MAV_TOPa_2026', scenario_tables_2026,
                                                     MAV_loss_params)
        elif year == 2028:
            if mount_tech == "SAT":
                if module_tech == "PERC":
                    results_SAT_PERCa_2028 = optimize(SAT, PERC2031, 2028, 'SAT_PERCa_2028', scenario_tables_2028,
                                                      SAT_loss_params)
                elif module_tech == "HJT":
                    results_SAT_HJTa_2028 = optimize(SAT, HJT2031, 2028, 'SAT_HJTa_2028', scenario_tables_2028,
                                                     SAT_loss_params)
                elif module_tech == "TOPCON":
                    results_SAT_TOPa_2028 = optimize(SAT, TOP2031, 2028, 'SAT_TOPa_2028', scenario_tables_2028,
                                                     SAT_loss_params)
            elif mount_tech == "MAV":
                if module_tech == "PERC":
                    results_MAV_PERCa_2028 = optimize(MAV, PERC2031, 2028, 'MAV_PERCa_2028', scenario_tables_2028,
                                                      MAV_loss_params)
                if module_tech == "HJT":
                    results_MAV_HJTa_2028 = optimize(MAV, HJT2031, 2028, 'MAV_HJTa_2028', scenario_tables_2028,
                                                     MAV_loss_params)
                if module_tech == "TOPCON":
                    results_MAV_TOPa_2028 = optimize(MAV, TOP2031, 2028, 'MAV_TOPa_2028', scenario_tables_2028,
                                                     MAV_loss_params)

    # %% Save and download optimized layouts, needs to be updated

    output_data = []
    output_dict = {}

    for year in ['2028']:
        scenario_tables = locals()['scenario_tables_' + year]
        output_dict[year] = {}
        for results in scenario_tables:
            index = results[1]
            install_dummy = results[0][1]['InstallNumber']
            install_dummy2 = install_dummy.reset_index()
            install_dummy3 = install_dummy2['InstallNumber']
            Racks = install_dummy3[0]
            W_zone = install_dummy3[3]
            # MW_per_zone = Modules*results[2]
            # Total_GW = MW_per_zone*num_of_zones/1000
            output_data.append([index, Racks, W_zone])
            results_string = 'results_' + index
            output_dict[year][index] = locals()[results_string]

    optimised_tables = pd.DataFrame(data=output_data, columns=['scenario', 'racks', 'W_zone'])
    optimised_tables.set_index('scenario', inplace=True)
    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)
    file_name = os.path.join(parent_path, 'OutputFigures', 'Optimised_layouts.csv')
    optimised_tables.to_csv(file_name)

    # %% ========================================
    # save results tables to pickl

    for year in ['2028']:
        file_tag = 'scenario_tables_' + year + '.p'
        pickle_path = os.path.join(parent_path, 'Data', 'mc_analysis', file_tag)
        cpickle.dump(output_dict[year], open(pickle_path, "wb"))
    return year, iter_limit
