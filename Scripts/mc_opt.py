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
    start_year = int(parameters[9])
    revenue_year = int(parameters[10])
    end_year = int(parameters[11])

    # Optimising Parameters
    year_sc1 = int(parameters[12])
    mount_tech_sc1 = str(parameters[13])
    module_tech_sc1 = str(parameters[14])
    try:
        set_racks1 = int(parameters[15])
    except ValueError:
        set_racks1 = None
    year_sc2 = int(parameters[16])
    mount_tech_sc2 = str(parameters[17])
    module_tech_sc2 = str(parameters[18])
    try:
        set_racks2 = int(parameters[19])
    except ValueError:
        set_racks2 = None
    year_sc3 = int(parameters[20])
    mount_tech_sc3 = str(parameters[21])
    module_tech_sc3 = str(parameters[22])
    try:
        set_racks3 = int(parameters[23])
    except ValueError:
        set_racks3 = None
    year_sc4 = int(parameters[24])
    mount_tech_sc4 = str(parameters[25])
    module_tech_sc4 = str(parameters[26])
    try:
        set_racks4 = int(parameters[27])
    except ValueError:
        set_racks4 = None
    year_sc5 = int(parameters[28])
    mount_tech_sc5 = str(parameters[29])
    module_tech_sc5 = str(parameters[30])
    try:
        set_racks5 = int(parameters[31])
    except ValueError:
        set_racks5 = None
    year_sc6 = int(parameters[32])
    mount_tech_sc6 = str(parameters[33])
    module_tech_sc6 = str(parameters[34])
    try:
        set_racks6 = int(parameters[35])
    except ValueError:
        set_racks6 = None
    year_sc7 = int(parameters[36])
    mount_tech_sc7 = str(parameters[37])
    module_tech_sc7 = str(parameters[38])
    try:
        set_racks7 = int(parameters[39])
    except ValueError:
        set_racks7 = None
    year_sc8 = int(parameters[40])
    mount_tech_sc8 = str(parameters[41])
    module_tech_sc8 = str(parameters[42])
    try:
        set_racks8 = int(parameters[43])
    except ValueError:
        set_racks3 = None
    year_sc9 = int(parameters[44])
    mount_tech_sc9 = str(parameters[45])
    module_tech_sc9 = str(parameters[46])
    try:
        set_racks9 = int(parameters[47])
    except ValueError:
        set_racks9 = None
    year_sc10 = int(parameters[48])
    mount_tech_sc10 = str(parameters[49])
    module_tech_sc10 = str(parameters[50])
    try:
        set_racks10 = int(parameters[51])
    except ValueError:
        set_racks10 = None
    year_sc11 = int(parameters[52])
    mount_tech_sc11 = str(parameters[53])
    module_tech_sc11 = str(parameters[54])
    try:
        set_racks11 = int(parameters[55])
    except ValueError:
        set_racks11 = None
    year_sc12 = int(parameters[56])
    mount_tech_sc12 = str(parameters[57])
    module_tech_sc12 = str(parameters[58])
    try:
        set_racks12 = int(parameters[59])
    except ValueError:
        set_racks12 = None
    year_sc13 = int(parameters[60])
    mount_tech_sc13 = str(parameters[61])
    module_tech_sc13 = str(parameters[62])
    try:
        set_racks13 = int(parameters[63])
    except ValueError:
        set_racks13 = None
    year_sc14 = int(parameters[64])
    mount_tech_sc14 = str(parameters[65])
    module_tech_sc14 = str(parameters[66])
    try:
        set_racks14 = int(parameters[67])
    except ValueError:
        set_racks14 = None
    year_sc15 = int(parameters[68])
    mount_tech_sc15 = str(parameters[69])
    module_tech_sc15 = str(parameters[70])
    try:
        set_racks15 = int(parameters[71])
    except ValueError:
        set_racks15 = None
    year_sc16 = int(parameters[72])
    mount_tech_sc16 = str(parameters[73])
    module_tech_sc16 = str(parameters[74])
    try:
        set_racks16 = int(parameters[75])
    except ValueError:
        set_racks16 = None
    year_sc17 = int(parameters[76])
    mount_tech_sc17 = str(parameters[77])
    module_tech_sc17 = str(parameters[78])
    try:
        set_racks17 = int(parameters[79])
    except ValueError:
        set_racks17 = None
    year_sc18 = int(parameters[80])
    mount_tech_sc18 = str(parameters[81])
    module_tech_sc18 = str(parameters[82])
    try:
        set_racks18 = int(parameters[83])
    except ValueError:
        set_racks18 = None
    year_sc19 = int(parameters[84])
    mount_tech_sc19 = str(parameters[85])
    module_tech_sc19 = str(parameters[86])
    try:
        set_racks19 = int(parameters[87])
    except ValueError:
        set_racks19 = None
    year_sc20 = int(parameters[88])
    mount_tech_sc20 = str(parameters[89])
    module_tech_sc20 = str(parameters[90])
    try:
        set_racks20 = int(parameters[91])
    except ValueError:
        set_racks20 = None
    year_sc21 = int(parameters[92])
    mount_tech_sc21 = str(parameters[93])
    module_tech_sc21 = str(parameters[94])
    try:
        set_racks21 = int(parameters[95])
    except ValueError:
        set_racks21 = None
    year_sc22 = int(parameters[96])
    mount_tech_sc22 = str(parameters[97])
    module_tech_sc22 = str(parameters[98])
    try:
        set_racks22 = int(parameters[99])
    except ValueError:
        set_racks22 = None
    year_sc23 = int(parameters[100])
    mount_tech_sc23 = str(parameters[101])
    module_tech_sc23 = str(parameters[102])
    try:
        set_racks23 = int(parameters[103])
    except ValueError:
        set_racks23 = None
    year_sc24 = int(parameters[104])
    mount_tech_sc24 = str(parameters[105])
    module_tech_sc24 = str(parameters[106])
    try:
        set_racks24 = int(parameters[107])
    except ValueError:
        set_racks24 = None
    year_sc25 = int(parameters[108])
    mount_tech_sc25 = str(parameters[109])
    module_tech_sc25 = str(parameters[110])
    try:
        set_racks25 = int(parameters[111])
    except ValueError:
        set_racks25 = None

    iter_limit = int(parameters[112])
    optimize_for = str(parameters[113])
    try:
        optimize_target = float(parameters[114])
    except ValueError:
        optimize_target = None
    projectID = str(parameters[115])

    print(parameters)
    print(optimize_for)
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

    def optimize(RACK_TYPE, MODULE_TYPE, INSTALL_YEAR, SCENARIO_LABEL, scenario_tables_combined, loss_params,
                 number_racks=None, optimize_for='NPV', optimize_target=None):
        module_type = MODULE_TYPE
        install_year = INSTALL_YEAR
        rack_type = RACK_TYPE

        scenario_tables_optimum, revenue, kWh_export, npv_output, rack_params, module_params = optimise_layout(
            weather_simulation, rack_type, module_type,
            install_year, start_year, revenue_year, end_year, DCTotal, num_of_zones, zone_area,
            rack_interval_ratio, temp_model, export_lim,
            storage_capacity, scheduled_price, data_tables,
            discount_rate, loss_params, number_racks, optimize_for,
            optimize_target, fig_title=SCENARIO_LABEL)

        scenario_tables_combined.append((scenario_tables_optimum, SCENARIO_LABEL))

        return SCENARIO_LABEL, scenario_tables_optimum, revenue, kWh_export, npv_output, rack_params, module_params, INSTALL_YEAR

    # Create variables to hold the results of each analysis
    SAT = 'SAT_1_update'
    MAV = '5B_MAV_update'
    MAV_6g_10 = '5B_MAV_6g_10'
    MAV_6g_12 = '5B_MAV_6g_12'
    SAT_84_600W = 'SAT_84module_600W'
    SAT_84_660W = 'SAT_84module_660W'
    MAV_5P13B = '5B_MAV_5P13B'
    #
    # 2024 - assume modules PERC_2023_M10, etc
    # 2024 - assume modules PERC_2025_M10, etc

    # 2026 - assume modules PERC_2025_M10, etc
    # 2026 - assume modules PERC_2028_M10, etc

    # 2028 - assume modules PERC_2028_M10, etc
    # 2028 - assume modules PERC_2031_M10, etc

    print(set_racks1)
    print(set_racks2)
    print(set_racks3)
    print(set_racks4)

    scenario_1 = [year_sc1, mount_tech_sc1, module_tech_sc1, set_racks1]
    scenario_2 = [year_sc2, mount_tech_sc2, module_tech_sc2, set_racks2]
    scenario_3 = [year_sc3, mount_tech_sc3, module_tech_sc3, set_racks3]
    scenario_4 = [year_sc4, mount_tech_sc4, module_tech_sc4, set_racks4]
    scenario_5 = [year_sc5, mount_tech_sc5, module_tech_sc5, set_racks5]
    scenario_6 = [year_sc6, mount_tech_sc6, module_tech_sc6, set_racks6]
    scenario_7 = [year_sc7, mount_tech_sc7, module_tech_sc7, set_racks7]
    scenario_8 = [year_sc8, mount_tech_sc8, module_tech_sc8, set_racks8]
    scenario_9 = [year_sc9, mount_tech_sc9, module_tech_sc9, set_racks9]
    scenario_10 = [year_sc10, mount_tech_sc10, module_tech_sc10, set_racks10]
    scenario_11 = [year_sc11, mount_tech_sc11, module_tech_sc11, set_racks11]
    scenario_12 = [year_sc12, mount_tech_sc12, module_tech_sc12, set_racks12]
    scenario_13 = [year_sc13, mount_tech_sc13, module_tech_sc13, set_racks13]
    scenario_14 = [year_sc14, mount_tech_sc14, module_tech_sc14, set_racks14]
    scenario_15 = [year_sc15, mount_tech_sc15, module_tech_sc15, set_racks15]
    scenario_16 = [year_sc16, mount_tech_sc16, module_tech_sc16, set_racks16]
    scenario_17 = [year_sc17, mount_tech_sc17, module_tech_sc17, set_racks17]
    scenario_18 = [year_sc18, mount_tech_sc18, module_tech_sc18, set_racks18]
    scenario_19 = [year_sc19, mount_tech_sc19, module_tech_sc19, set_racks19]
    scenario_20 = [year_sc20, mount_tech_sc20, module_tech_sc20, set_racks20]
    scenario_21 = [year_sc21, mount_tech_sc21, module_tech_sc21, set_racks21]
    scenario_22 = [year_sc22, mount_tech_sc22, module_tech_sc22, set_racks22]
    scenario_23 = [year_sc23, mount_tech_sc23, module_tech_sc23, set_racks23]
    scenario_24 = [year_sc24, mount_tech_sc24, module_tech_sc24, set_racks24]
    scenario_25 = [year_sc25, mount_tech_sc25, module_tech_sc25, set_racks25]
    scenario_params = [scenario_1, scenario_2, scenario_3, scenario_4, scenario_5,
                       scenario_6, scenario_7, scenario_8, scenario_9, scenario_10,
                       scenario_11, scenario_12, scenario_13, scenario_14, scenario_15,
                       scenario_16, scenario_17, scenario_18, scenario_19, scenario_20,
                       scenario_21, scenario_22, scenario_23, scenario_24, scenario_25,]
    scenario_tables = []
    scenario_dict = {}


    for scenario in scenario_params:
        year = scenario[0]
        mount_tech = scenario[1]
        module_tech = scenario[2]
        set_racks = scenario[3]

        if mount_tech == "SAT":
            label = "results_SAT_" + module_tech + "_" + str(year)
            if set_racks:
                results = optimize(SAT, module_tech, year, label, scenario_tables, SAT_loss_params,
                                   number_racks = set_racks,)
            else:
                results = optimize(SAT, module_tech, year, label, scenario_tables, SAT_loss_params,
                                   optimize_for=optimize_for, optimize_target=optimize_target)

        elif mount_tech == "SAT_84_600W":
            label = "results_SAT_600" + "_" + str(year)
            if set_racks:
                results = optimize(SAT_84_600W, module_tech, year, label, scenario_tables, SAT_loss_params,
                                   number_racks = set_racks)
            else:
                results = optimize(SAT_84_600W, module_tech, year, label, scenario_tables, SAT_loss_params,
                                   optimize_for=optimize_for, optimize_target=optimize_target)

        elif mount_tech == "SAT_84_660W":
            label = "results_SAT_660" + "_" + str(year)
            if set_racks:
                results = optimize(SAT_84_660W, module_tech, year, label, scenario_tables, SAT_loss_params,
                                   number_racks=set_racks)
            else:
                results = optimize(SAT_84_660W, module_tech, year, label, scenario_tables, SAT_loss_params,
                                   optimize_for=optimize_for, optimize_target=optimize_target)


        elif mount_tech == "MAV":
            label = "results_MAV_" + module_tech + "_" + str(year)
            if set_racks:
                results = optimize(MAV, module_tech, year, label, scenario_tables, MAV_loss_params,
                                   number_racks=set_racks)
            else:
                results = optimize(MAV, module_tech, year, label, scenario_tables, MAV_loss_params,
                                   optimize_for=optimize_for, optimize_target=optimize_target)

        elif mount_tech == "MAV_6g_10":
            label = "results_MAV_6g10" + "_" + str(year)
            if set_racks:
                results = optimize(MAV_6g_10, module_tech, year, label, scenario_tables, MAV_loss_params,
                                   number_racks = set_racks)
            else:
                results = optimize(MAV_6g_10, module_tech, year, label, scenario_tables, MAV_loss_params,
                                   optimize_for=optimize_for, optimize_target=optimize_target)

        elif mount_tech == "MAV_6g_12":
            label = "results_MAV_6g12" + "_" + str(year)
            if set_racks:
                results = optimize(MAV_6g_12, module_tech, year, label, scenario_tables, MAV_loss_params,
                                   number_racks = set_racks)
            else:
                results = optimize(MAV_6g_12, module_tech, year, label, scenario_tables, MAV_loss_params,
                                   optimize_for=optimize_for, optimize_target=optimize_target)

        elif mount_tech == "MAV_5P13B":
            label = "results_MAV_5P13B" + "_" + str(year)
            if set_racks:
                results = optimize(MAV_5P13B, module_tech, year, label, scenario_tables, MAV_loss_params,
                                   number_racks=set_racks)
            else:
                results = optimize(MAV_5P13B, module_tech, year, label, scenario_tables, MAV_loss_params,
                                   optimize_for=optimize_for, optimize_target=optimize_target)

        scenario_dict[label] = results

    # %% Save and download optimized layouts, needs to be updated

    output_data = []

 #   for results in scenario_tables:
 #       index = results[1]
 #       install_dummy = results[0][1]['InstallNumber']
 #       install_dummy2 = install_dummy.reset_index()
 #       install_dummy3 = install_dummy2['InstallNumber']
 #       Racks = install_dummy3[0]
 #       W_zone = install_dummy3[3]
        # MW_per_zone = Modules*results[2]
        # Total_GW = MW_per_zone*num_of_zones/1000
 #       output_data.append([index, Racks, W_zone])


 #   optimised_tables = pd.DataFrame(data=output_data, columns=['scenario', 'racks', 'W_zone'])
 #   optimised_tables.set_index('scenario', inplace=True)
 #   current_path = os.getcwd()
 #   parent_path = os.path.dirname(current_path)
 #   file_name = os.path.join(parent_path, 'OutputFigures', 'Optimised_layouts.csv')
 #   optimised_tables.to_csv(file_name)

    # %% ========================================
    # save results tables to pickl
    # TODO update save path to project folder
    file_tag = 'scenario_tables_' + projectID + '.p'
    pickle_path = os.path.join(parent_path, 'Data', 'mc_analysis', file_tag)
    cpickle.dump(scenario_dict, open(pickle_path, "wb"))

