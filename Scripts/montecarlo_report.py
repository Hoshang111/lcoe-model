
""" This is the main script for the yield assessment. The script calls the functions below to
calculate the Net Present Value (NPV) of the solar farm
1) Weather:
Input: Weather file, year of simulation
Output: Weather dataframe in the required format for PVlib simulations
2) Racks & modules:
Input: Type of module and rack
Output: Module and rack parameters required for PVlib PVsystem extracted from the
module & rack database
3) Sizing
Input: DC size of the solar farm
Output: Configuration in terms of number of single-axis tracking (SAT) racks or 5B Maverick
units (MAV)
4) DC/AC Yield:
Input: number of racks, number of MAVs, weather data, module name, mounting type
(optional & future improvement: temperature rack type, aoi model, back-tracking/optimal tilt angle)
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
During the optimisation process/simulations, cost function will give deterministic values.
Once the optimum NPV is found cost function also give the Monte-Carlo distribution.
"""

# %% Import
import random
import sys
sys.path.append( '..' )
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import Functions.simulation_functions as func
import Functions.mc_yield_functions as mc_func
from numpy.polynomial import Polynomial
from Functions.optimising_functions import form_new_data_tables, optimise_layout
from Functions.sizing_functions import get_airtable
from Functions.cost_functions import calculate_scenarios_iterations, create_iteration_tables, \
     generate_parameters, calculate_variance_contributions, import_excel_data
from Functions.mc_yield_functions import weather_sort, generate_mc_timeseries, get_yield_datatables

# %%
# Set overall conditions for this analysis


use_previous_airtable_data = False

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
dni_dummy = pd.read_csv(os.path.join(parent_path, 'Data', 'WeatherData', 'TMY_dni_simulated_1minute.csv'), index_col=0)
dni_dummy.set_index(pd.to_datetime(dni_dummy.index, utc=False), drop=True, inplace=True)
dni_dummy.index = dni_dummy.index.tz_convert('Australia/Darwin')

weather_dnv.drop(['dni'],axis=1,inplace=True)
weather_dnv = weather_dnv.join(dni_dummy, how='left')
weather_dnv.rename(columns={"0": "dni"}, inplace=True)
weather_dnv = weather_dnv[['ghi','dni','dhi','temp_air','wind_speed','precipitable_water','dc_yield']]

# shift weather files 30 min so that solar position is calculated at midpoint of period
weather_dnv_mod = weather_dnv.shift(periods=30, freq='T')
weather_simulation = weather_dnv_mod


# Sizing/rack and module numbers
# Call the constants from the database - unneeded if we just pass module class?
DCTotal = 11000  # DC size in MW
num_of_zones = 720  # Number of smaller zones that will make up the solar farm
zone_area = 1.4e5   # Zone Area in m2
rack_interval_ratio = 0.01

# Yield Assessment Inputs
temp_model = 'pvsyst'  # choose a temperature model either Sandia: 'sapm' or PVSyst: 'pvsyst'

# Revenue and storage behaviour
export_lim = 3.2e9/num_of_zones # Watts per zone
storage_capacity = 5e7 # Wh per zone
scheduled_price = 0.000150  # AUD / Wh. Assumption: AUD 4c/kWh (conversion from Wh to kWh)

# Financial Parameters
discount_rate = 0.07

if use_previous_airtable_data:
    data_tables = import_excel_data('CostDatabaseFeb2022a.xlsx')
else:
    # cost data tables from airtable
    data_tables = get_airtable(save_tables=True)

# %%
# Cycle through alternative analysis scenarios

def optimize (RACK_TYPE, MODULE_TYPE, INSTALL_YEAR, SCENARIO_LABEL, scenario_tables_combined):
    module_type = MODULE_TYPE
    install_year = INSTALL_YEAR
    rack_type = RACK_TYPE

    scenario_tables_optimum, revenue, kWh_export, npv_output = optimise_layout(weather_simulation, \
                                                                   rack_type, module_type, install_year, DCTotal,
                                                                   num_of_zones, zone_area, rack_interval_ratio, \
                                                                   temp_model, export_lim, storage_capacity,
                                                                   scheduled_price, data_tables, discount_rate,
                                                                   fig_title=SCENARIO_LABEL)

    scenario_tables_combined.append((scenario_tables_optimum, SCENARIO_LABEL))

    return SCENARIO_LABEL, scenario_tables_optimum, revenue, kWh_export, npv_output

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

# scenario_tables_2024 = []
# results_SAT_PERC_2024 = optimize (SAT, PERC2023, 2024, 'SAT PERC 2024', scenario_tables_2024)
# results_MAV_PERC_2024 = optimize (MAV, PERC2023, 2024, 'MAV PERC 2024', scenario_tables_2024)
# results_SAT_HJT_2024 = optimize (SAT, HJT2023, 2024, 'SAT HJT 2024', scenario_tables_2024)
# results_MAV_HJT_2024 = optimize (MAV, HJT2023, 2024, 'MAV HJT 2024', scenario_tables_2024)
# results_SAT_TOP_2024 = optimize (SAT, TOP2023, 2024, 'SAT TOP 2024', scenario_tables_2024)
# results_MAV_TOP_2024 = optimize (MAV, TOP2023, 2024, 'MAV TOP 2024', scenario_tables_2024)
# results_SAT_PERCa_2024 = optimize (SAT, PERC2025, 2024, 'SAT PERCa 2024', scenario_tables_2024)
# results_MAV_PERCa_2024 = optimize (MAV, PERC2025, 2024, 'MAV PERCa 2024', scenario_tables_2024)
# results_SAT_HJTa_2024 = optimize (SAT, HJT2025, 2024, 'SAT HJTa 2024', scenario_tables_2024)
# results_MAV_HJTa_2024 = optimize (MAV, HJT2025, 2024, 'MAV HJTa 2024', scenario_tables_2024)
# results_SAT_TOPa_2024 = optimize (SAT, TOP2025, 2024, 'SAT TOPa 2024', scenario_tables_2024)
# results_MAV_TOPa_2024 = optimize (MAV, TOP2025, 2024, 'MAV TOPa 2024', scenario_tables_2024)

# scenario_tables_2026 = []
# results_SAT_PERC_2026 = optimize (SAT, PERC2025, 2026, 'SAT PERC 2026',scenario_tables_2026)
# results_MAV_PERC_2026 = optimize (MAV, PERC2025, 2026, 'MAV PERC 2026',scenario_tables_2026)
# results_SAT_HJT_2026 = optimize (SAT, HJT2025, 2026, 'SAT HJT 2026',scenario_tables_2026)
# results_MAV_HJT_2026 = optimize (MAV, HJT2025, 2026, 'MAV HJT 2026',scenario_tables_2026)
# results_SAT_TOP_2026 = optimize (SAT, TOP2025, 2026, 'SAT TOP 2026',scenario_tables_2026)
# results_MAV_TOP_2026 = optimize (MAV, TOP2025, 2026, 'MAV TOP 2026',scenario_tables_2026)
# results_SAT_PERCa_2026 = optimize (SAT, PERC2028, 2026, 'SAT PERCa 2026',scenario_tables_2026)
# results_MAV_PERCa_2026 = optimize (MAV, PERC2028, 2026, 'MAV PERCa 2026',scenario_tables_2026)
# results_SAT_HJTa_2026 = optimize (SAT, HJT2028, 2026, 'SAT HJTa 2026',scenario_tables_2026)
# results_MAV_HJTa_2026 = optimize (MAV, HJT2028, 2026, 'MAV HJTa 2026',scenario_tables_2026)
# results_SAT_TOPa_2026 = optimize (SAT, TOP2028, 2026, 'SAT TOPa 2026',scenario_tables_2026)
# results_MAV_TOPa_2026 = optimize (MAV, TOP2028, 2026, 'MAV TOPa 2026',scenario_tables_2026)



scenario_tables_2028 = []
# results_SAT_PERC_2028 = optimize (SAT, PERC2028, 2028, 'SAT PERC 2028',scenario_tables_2028)
# results_MAV_PERC_2028 = optimize (MAV, PERC2028, 2028, 'MAV PERC 2028',scenario_tables_2028)
# results_SAT_HJT_2028 = optimize (SAT, HJT2028, 2028, 'SAT HJT 2028',scenario_tables_2028)
# results_MAV_HJT_2028 = optimize (MAV, HJT2028, 2028, 'MAV HJT 2028',scenario_tables_2028)
#results_SAT_TOP_2028 = optimize (SAT, TOP2028, 2028, 'SAT TOP 2028',scenario_tables_2028)
# results_MAV_TOP_2028 = optimize (MAV, TOP2028, 2028, 'MAV TOP 2028',scenario_tables_2028)
results_SAT_PERCa_2028 = optimize (SAT, PERC2031, 2028, 'SAT PERCa 2028',scenario_tables_2028)
results_MAV_PERCa_2028 = optimize (MAV, PERC2031, 2028, 'MAV PERCa 2028',scenario_tables_2028)
results_SAT_HJTa_2028 = optimize (SAT, HJT2031, 2028, 'SAT HJTa 2028',scenario_tables_2028)
results_MAV_HJTa_2028 = optimize (MAV, HJT2031, 2028, 'MAV HJTa 2028',scenario_tables_2028)
results_SAT_TOPa_2028 = optimize (SAT, TOP2031, 2028, 'SAT TOPa 2028',scenario_tables_2028)
results_MAV_TOPa_2028 = optimize (MAV, TOP2031, 2028, 'MAV TOPa 2028',scenario_tables_2028)

# %% Save and download optimized layouts

output_data = []
for scenario_tables in [scenario_tables_2028]:
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

optimised_tables = pd.DataFrame(data=output_data, columns=['scenario', 'racks', 'W_zone'])
optimised_tables.set_index('scenario', inplace=True)
current_path = os.getcwd()
parent_path = os.path.dirname(current_path)
file_name = os.path.join(parent_path, 'OutputFigures', 'Optimised_layouts.csv')
optimised_tables.to_csv(file_name)

# %% ===========================================================
# Monte Carlo for yield parameters
# first create ordered dict of weather and output
# need a weather file containing several years worth of data, no gaps allowed

mc_weather_name = 'Combined_Longi_570_Tracker-bifacial_FullTS_8m.csv'
mc_weather_file = mc_func.mc_weather_import(mc_weather_name)

# create a dict of ordered dicts with dc output, including weather GHI as first column
dc_ordered = {}
ghi_timeseries = pd.DataFrame(mc_weather_file['ghi'])
dc_ordered['ghi'] = mc_func.dict_sort(ghi_timeseries, 'ghi')

for results in scenario_tables:
    yield_timeseries = dc_yield_calc(layout_params, mc_weather_file)
    dc_ordered[results['SCENARIO_LABEL']] = mc_func.dict_sort(yield_timeseries)
    dc_ordered[results['SCENARIO_LABEL']]['label'] = results['SCENARIO_LABEL']

# %% ===========================================================
# Create data tables for yield parameters

start_date = '1/1/2029 00:00:00'
end_date = '31/12/2058 23:59:00'
month_series = pd.date_range(start=start_date, end=end_date, freq='MS')
yield_datatables = get_yield_datatables()
# need to create a wrapper function to call for each set of random numbers
random_timeseries = np.random.random((len(month_series), len(yield_datatables)))

output_dict = {}

for ordered_dict in dc_ordered:
    dc_output = pd.DataFrame()
    for column in random_timeseries.T:
        generation_list=list(zip(month_series, column))
        dummy = mc_func.gen_mcts(ordered_dict, generation_list, start_date, end_date)
        dc_output = pd.concat([dummy, dc_output], axis=1)
    output_dict[ordered_dict['label']] = dc_output

# since GHI was first of our scenarios
# %% ===========================================================
# Now apply losses

# %% ===========================================================
# Now calculate AC output (currently not used)



# %% ==========================================================
# Calculate LCOE and/or NPV for each iteration, and plot these for each optimum scenario.
# First generate a big table with index consisting of Iteration, Year, ScenarioID.

# %%
# Call Monte Carlo Cost analysis

for analysis_year in [
    # 2024,
    # 2026,
    2028
                      ]:


    if analysis_year == 2024:
        scenario_tables = scenario_tables_2024
    elif analysis_year == 2026:
        scenario_tables = scenario_tables_2026
    elif analysis_year == 2028:
        scenario_tables = scenario_tables_2028
    # First generate data tables with the ScenarioID changed to something more intuitive
    new_data_tables = form_new_data_tables(data_tables, scenario_tables)

    # Create iteration data
    data_tables_iter = create_iteration_tables(new_data_tables, 5000, iteration_start=0)

    # Calculate cost result
    outputs_iter = calculate_scenarios_iterations(data_tables_iter, year_start=analysis_year, analyse_years=30)
    component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, cash_flow_by_year_iter = outputs_iter

    combined_scenario_data = pd.DataFrame()

    if analysis_year == 2024:
        install_year = 2024
        results_list = [[results_SAT_PERC_2024,
                   results_MAV_PERC_2024,
                   results_SAT_HJT_2024,
                   results_MAV_HJT_2024,
                   results_SAT_TOP_2024,
                   results_MAV_TOP_2024],
                   [results_SAT_PERCa_2024,
                   results_MAV_PERCa_2024,
                   results_SAT_HJTa_2024,
                   results_MAV_HJTa_2024,
                   results_SAT_TOPa_2024,
                   results_MAV_TOPa_2024,
                   ]]

    elif analysis_year == 2026:
        install_year = 2026
        results_list = [[results_SAT_PERC_2026,
                   results_MAV_PERC_2026,
                   results_SAT_HJT_2026,
                   results_MAV_HJT_2026,
                   results_SAT_TOP_2026,
                   results_MAV_TOP_2026],
                   [results_SAT_PERCa_2026,
                   results_MAV_PERCa_2026,
                   results_SAT_HJTa_2026,
                   results_MAV_HJTa_2026,
                   results_SAT_TOPa_2026,
                   results_MAV_TOPa_2026,
                   ]]


    elif analysis_year == 2028:
        install_year = 2028
        results_list = [
                  # [results_SAT_PERC_2028,
                  # results_MAV_PERC_2028,
                  # results_SAT_HJT_2028,
                  # results_MAV_HJT_2028,
                  # results_SAT_TOP_2028,
                  #results_MAV_TOP_2028],
                   [results_SAT_PERCa_2028,
                   results_MAV_PERCa_2028,
                   results_SAT_HJTa_2028,
                   results_MAV_HJTa_2028,
                   results_SAT_TOPa_2028,
                   results_MAV_TOPa_2028,
                   ]]

    else:
        print('Error!')

#%%

    font_size = 14
    rc = {'font.size': font_size, 'axes.labelsize': font_size, 'legend.fontsize': font_size,
          'axes.titlesize': font_size, 'xtick.labelsize': font_size, 'ytick.labelsize': font_size}
    plt.rcParams.update(**rc)
    plt.rc('font', weight='bold')

    # For label titles
    fontdict = {'fontsize': font_size, 'fontweight': 'bold'}

    for results in results_list:
        for (scenario_id, scenario_tables_optimum, revenue_data, kWh_export_data, npv_output) in results:

            kWh_export_data.name = 'kWh'
            revenue_data.name = 'revenue'

            if len(cash_flow_by_year_iter[scenario_id])>0:
                scenario_data = cash_flow_by_year_iter[scenario_id]
                scenario_data.name = 'cost'

                scenario_data = scenario_data.reset_index().merge(
                    kWh_export_data.reset_index(), how='left', on='Year').merge(
                    revenue_data.reset_index(), how='left', on='Year')
                scenario_data['ScenarioID'] = scenario_id

                combined_scenario_data = combined_scenario_data.append(scenario_data)

                # Now discount the costs, etc
                for col_name in ['cost', 'kWh', 'revenue']:
                    combined_scenario_data[col_name + '_disc'] = combined_scenario_data[col_name] / (1 + discount_rate) ** \
                                                                 (combined_scenario_data['Year'] - install_year)

                # Create a new table that removes the year, adding all the discounted flows
                discounted_sum = pd.pivot_table(combined_scenario_data, index=['Iteration', 'ScenarioID'], values=['kWh_disc',
                                                                                                                   'cost_disc',
                                                                                                                   'revenue_disc'])

                # Now calculate LCOE and NPV

                discounted_sum['LCOE'] = discounted_sum['cost_disc'] / discounted_sum['kWh_disc']
                discounted_sum['NPV'] = discounted_sum['revenue_disc'] - discounted_sum['cost_disc']

                print(discounted_sum)

                # Plot the LCOE and NPV distributions. For each figure, show each scenario as its own distribution.

        for parameter in ['LCOE', 'NPV']:
            data = discounted_sum[parameter].reset_index()
            print(data)
            data = pd.pivot_table(data, index='Iteration', values=parameter, columns='ScenarioID')
            data.plot.hist(bins=50, histtype='step', fontsize=8)
            fig_title = parameter + ' - ' + str(install_year)
            plt.title(fig_title)
            # savefig.save_figure(fig_title)
            current_path = os.getcwd()
            parent_path = os.path.dirname(current_path)
            file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
            plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
            plt.close()
            # plt.show()

    if analysis_year == 2024:
        analysis_list = [(['SAT PERC 2024','MAV PERC 2024'], 'SAT vs MAV 2024')]
    elif analysis_year == 2026:
        analysis_list = [(['SAT PERC 2026', 'MAV PERC 2026'], 'SAT vs MAV 2026')]
    elif analysis_year == 2028:
        analysis_list = [(['SAT HJTa 2028', 'MAV HJTa 2028'], 'SAT vs MAV 2028')]
    else:
        analysis_list == []
    for (scenarios, title) in analysis_list:
        print(scenarios)
        scenario_costs_iter = total_cost_y_iter[total_cost_y_iter['ScenarioID'].isin(scenarios)]
        scenario_costs_nominal = scenario_costs_iter[scenario_costs_iter['Iteration']==0]

        # scenario_costs_by_year = pd.pivot_table(scenario_costs_nominal, values='TotalCostAUDY',
        #                                              index=['Year','ScenarioID'], aggfunc=np.sum,
        #                                              columns=['CostCategory_ShortName']).reset_index()
        # print(scenario_costs_by_year)
        # scenario_costs_by_year.plot.bar(stacked=True,title='Total Costs by Year - ' + title)
        # plt.show()

        scenario_costs_total_category = pd.pivot_table(scenario_costs_nominal, values='TotalCostAUDY',
                                                     index=['ScenarioID'], aggfunc=np.sum,
                                                     columns=['CostCategory_ShortName'])
        scenario_costs_total_category.to_csv('temp_category_costs' + str(analysis_year) + '.csv')
        scenario_costs_total_category.plot.bar(stacked=True, title='Total Costs by Category - ' + title)
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', 'Scenario Costs')
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()


        scenario_costs_total_nodiscount = pd.pivot_table(scenario_costs_iter, values='TotalCostAUDY',
                                                         index=['Iteration'], aggfunc=np.sum,
                                                         columns=['ScenarioID'])
        scenario_costs_total_nodiscount.plot.hist(bins=50, histtype='step')
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', 'Scenario Costs No Discount')
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()

    if analysis_year==2024:
        comparison_list = [('MAV HJT 2024','SAT HJT 2024', 'MAV vs SAT HJT 2024'),
                            ('MAV HJT 2024','MAV PERC 2024', 'HJT vs PERC MAV 2024'),
                                               ]

    elif analysis_year == 2026:
        comparison_list = [('MAV PERC 2026', 'SAT PERC 2026', 'MAV vs SAT PERC 2026'),
                           ('MAV HJT 2026', 'MAV PERC 2026', 'HJT vs PERC MAV 2026')]
    elif analysis_year == 2028:
        comparison_list = [('MAV HJTa 2028', 'SAT HJTa 2028', 'MAV vs SAT HJT 2028'),
                           ('MAV HJTa 2028', 'MAV PERCa 2028', 'HJT vs PERC MAV 2028'),
                           ('SAT HJTa 2028', 'SAT PERCa 2028', 'HJT vs PERC SAT 2028')]

    for (scenario_1, scenario_2, savename) in comparison_list:

        for parameter in ['LCOE', 'NPV']:
            data = discounted_sum[parameter].reset_index()
            data = pd.pivot_table(data, index='Iteration', values = parameter, columns='ScenarioID')

            data['Difference'] = data[scenario_2] - data[scenario_1]
            data['Difference'].plot.hist(bins=50, histtype='step')
            fig_title = 'Difference in ' + parameter + ' ' + savename
            plt.title(fig_title)
            # savefig.save_figure(fig_title)
            current_path = os.getcwd()
            parent_path = os.path.dirname(current_path)
            file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
            plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
            plt.close()
            # plt.show()

        def generate_difference_factor(df, parameter, scenario_1, scenario_2, parameter_name):
            data = df[parameter].reset_index()
            data = pd.pivot_table(data, index = 'Iteration', values= parameter, columns = 'ScenarioID')
            data[parameter_name] = data[scenario_2] - data[scenario_1]
            return data[parameter_name]


        # Sensitivity analysis / regression analysis to determine key uncertainties affecting these.
        parameters = generate_parameters(data_tables_iter)
        parameters_flat = parameters.copy()
        parameters_flat.columns = [group + ' ' + str(ID) + ' ' + var for (group, ID, var) in parameters_flat.columns.values]

        factor = generate_difference_factor(discounted_sum, 'LCOE', scenario_1, scenario_2, 'LCOE_Difference')
        parameters_flat = parameters_flat.join(factor)

        factor = generate_difference_factor(discounted_sum, 'NPV', scenario_1, scenario_2, 'NPV_Difference')
        parameters_flat = parameters_flat.join(factor)

        parameters_flat.to_csv('Tempparameters.csv')
        baseline_year = 2024
        parameters_flat['Module Cost'] = parameters_flat['ComponentID 33 BaselineCost'] * parameters_flat[
            'ComponentID 33 AnnualMultiplier'] ** (analysis_year - baseline_year)
        parameters_flat['HJT Premium'] = parameters_flat['ComponentID 35 BaselineCost'] * parameters_flat[
            'ComponentID 35 AnnualMultiplier'] ** (analysis_year - baseline_year)
        parameters_flat['TOPCon Premium'] = parameters_flat['ComponentID 34 BaselineCost'] * parameters_flat[
            'ComponentID 34 AnnualMultiplier'] ** (analysis_year - baseline_year)
        # parameters_flat['Onsite Labour Index'] = parameters_flat['ComponentID 45 BaselineCost'] * parameters_flat[
        #     'ComponentID 45 AnnualMultiplier'] ** (analysis_year - baseline_year)
        parameters_flat['Onsite Labour Index'] = parameters_flat[
            'ComponentID 45 AnnualMultiplier'] ** (analysis_year - baseline_year)


        parameters_flat = parameters_flat.rename(columns={
            'ComponentID 45 AnnualMultiplier': 'Onsite Labour Annual Multiplier',
            'ComponentID 33 AnnualMultiplier': 'Module cost Annual Multiplier',
            'SystemComponentID 163 UsageAnnualMultiplier': 'MAV Hardware Annual Multiplier',
            'SystemComponentID 164 UsageAnnualMultiplier': 'MAV Labour Annual Multiplier'
        })


        calculate_variance_contributions(parameters_flat, 'LCOE_Difference', savename=savename)

        x = parameters_flat['Module Cost']
        y = parameters_flat['Onsite Labour Index']
        z = parameters_flat['LCOE_Difference']
        title = 'Impact on LCOE difference'
        p1_description = 'Module Cost'
        p2_description = 'Labour Index'
        map = 'seismic'
        colorbartitle = 'Delta LCOE'
        fig, (ax0, ax1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [25, 1]})

        vmax = z.abs().max()
        vmin = -vmax

        scatterplot = ax0.scatter(x, y, c=z, cmap=map, vmin=vmin, vmax=vmax, s=None)
        plt.colorbar(scatterplot, cax=ax1)
        ax1.set_title(colorbartitle)

        ax0.set_xlabel(p1_description)
        ax0.set_ylabel(p2_description)
        ax0.set_title(title)

        fig_title = "Delta LCOE - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()

        x = parameters_flat['Module Cost']
        y = parameters_flat['Onsite Labour Index']
        z = parameters_flat['NPV_Difference']
        title = 'Impact on NPV difference'
        p1_description = 'Module Cost'
        p2_description = 'Labour Index'
        map = 'seismic_r'
        colorbartitle = 'Delta NPV'
        fig, (ax0, ax1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [25, 1]})

        vmax = z.abs().max()
        vmin = -vmax

        scatterplot = ax0.scatter(x, y, c=z, cmap=map, vmin=vmin, vmax=vmax, s=None)
        plt.colorbar(scatterplot, cax=ax1)
        ax1.set_title(colorbartitle)

        ax0.set_xlabel(p1_description)
        ax0.set_ylabel(p2_description)
        ax0.set_title(title)

        fig_title = "Delta NPV - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()

        x = parameters_flat['Module Cost']
        y = parameters_flat['MAV Hardware Annual Multiplier']
        z = parameters_flat['NPV_Difference']
        title = 'Impact on NPV difference'
        p1_description = 'Module Cost'
        p2_description = 'MAV Hardware Multiplier'
        map = 'seismic_r'
        colorbartitle = 'Delta NPV'
        fig, (ax0, ax1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [25, 1]})

        vmax = z.abs().max()
        vmin = -vmax

        scatterplot = ax0.scatter(x, y, c=z, cmap=map, vmin=vmin, vmax=vmax, s=None)
        plt.colorbar(scatterplot, cax=ax1)
        ax1.set_title(colorbartitle)

        ax0.set_xlabel(p1_description)
        ax0.set_ylabel(p2_description)
        ax0.set_title(title)

        fig_title = "Delta NPV hardware - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()

        x = parameters_flat['Module Cost']
        y = parameters_flat['MAV Labour Annual Multiplier']
        z = parameters_flat['NPV_Difference']
        title = 'Impact on NPV difference'
        p1_description = 'Module Cost'
        p2_description = 'MAV Labour Multiplier'
        map = 'seismic_r'
        colorbartitle = 'Delta NPV'
        fig, (ax0, ax1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [25, 1]})

        vmax = z.abs().max()
        vmin = -vmax

        scatterplot = ax0.scatter(x, y, c=z, cmap=map, vmin=vmin, vmax=vmax, s=None)
        plt.colorbar(scatterplot, cax=ax1)
        ax1.set_title(colorbartitle)

        ax0.set_xlabel(p1_description)
        ax0.set_ylabel(p2_description)
        ax0.set_title(title)

        fig_title = "Delta NPV labour - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        # plt.show()

        x = parameters_flat['MAV Labour Annual Multiplier'].astype(str).astype(float)
        y = parameters_flat['NPV_Difference'].astype(str).astype(float)
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.scatter(x, y)
        ax.set_xlabel('MAV Labour Multiplier', **fontdict)
        ax.set_ylabel('Difference in NPV', **fontdict)
        ax.set_title('Regression for MAV Labour')

        c1, c0 = Polynomial.fit(x, y, 1)
        correlation_matrix = np.corrcoef(x.values, y.values)
        correlation_xy = correlation_matrix[0, 1]
        r_squared = correlation_xy ** 2

        ax.plot(x, x * c1 + c0, linewidth=3, color='C1')
        # ax.set_ylim(0,1.25)
        # ax.set_xlim(0,1.25)
        plot_text = 'r = %.2f' % correlation_xy
        xt = (x.mean() - x.min()) / 2 + x.min()
        yt = (y.mean() / 2 - y.min()) / 2 + y.min()
        plt.text(xt, yt, plot_text, fontsize=25)

        fig_title = "Regression NPV labour - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()

        x = parameters_flat['MAV Hardware Annual Multiplier'].astype(str).astype(float)
        y = parameters_flat['NPV_Difference'].astype(str).astype(float)
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.scatter(x, y)
        ax.set_xlabel('MAV Hardware Multiplier', **fontdict)
        ax.set_ylabel('Difference in NPV', **fontdict)
        ax.set_title('Regression for MAV Hardware')

        c1, c0 = Polynomial.fit(x, y, 1)
        correlation_matrix = np.corrcoef(x.values, y.values)
        correlation_xy = correlation_matrix[0, 1]
        r_squared = correlation_xy ** 2

        ax.plot(x, x * c1 + c0, linewidth=3, color='C1')
        # ax.set_ylim(0,1.25)
        # ax.set_xlim(0,1.25)
        plot_text = 'r = %.2f' % correlation_xy
        xt = (x.mean()-x.min())/2+x.min()
        yt = (y.mean()-y.min())/2+y.min()
        plt.text(xt, yt, plot_text, fontsize=25)

        fig_title = "Regression NPV hardware - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()


# %%
#print(results_SAT_PERC_2024)

graph_data = pd.DataFrame(columns=['Year','NPV','Label'], index=[*range(0,1)])
i = 0
for (year, label, results) in [
#    (2024, 'MAV PERC', results_MAV_PERC_2024),
#    (2026, 'MAV PERC', results_MAV_PERC_2026),
#    (2028, 'MAV PERC', results_MAV_PERC_2028),
#    (2024, 'SAT PERC', results_SAT_PERC_2024),
#    (2026, 'SAT PERC', results_SAT_PERC_2026),
#    (2028, 'SAT PERC', results_SAT_PERC_2028),
#    (2024, 'MAV PERCa', results_MAV_PERCa_2024),
#    (2026, 'MAV PERCa', results_MAV_PERCa_2026),
    (2028, 'MAV PERCa', results_MAV_PERCa_2028),
#    (2024, 'SAT PERCa', results_SAT_PERCa_2024),
#    (2026, 'SAT PERCa', results_SAT_PERCa_2026),
    (2028, 'SAT PERCa', results_SAT_PERCa_2028),
#    (2024, 'MAV TOP', results_MAV_TOP_2024),
#    (2026, 'MAV TOP', results_MAV_TOP_2026),
#    (2028, 'MAV TOP', results_MAV_TOP_2028),
#    (2024, 'SAT TOP', results_SAT_TOP_2024),
#    (2026, 'SAT TOP', results_SAT_TOP_2026),
#    (2028, 'SAT TOP', results_SAT_TOP_2028),
#    (2024, 'MAV TOPa', results_MAV_TOPa_2024),
#    (2026, 'MAV TOPa', results_MAV_TOPa_2026),
    (2028, 'MAV TOPa', results_MAV_TOPa_2028),
#    (2024, 'SAT TOPa', results_SAT_TOPa_2024),
#    (2026, 'SAT TOPa', results_SAT_TOPa_2026),
    (2028, 'SAT TOPa', results_SAT_TOPa_2028),
#    (2024, 'MAV HJT', results_MAV_HJT_2024),
#    (2026, 'MAV HJT', results_MAV_HJT_2026),
#    (2028, 'MAV HJT', results_MAV_HJT_2028),
#    (2024, 'SAT HJT', results_SAT_HJT_2024),
#    (2026, 'SAT HJT', results_SAT_HJT_2026),
#    (2028, 'SAT HJT', results_SAT_HJT_2028),
#    (2024, 'MAV HJTa', results_MAV_HJTa_2024),
#    (2026, 'MAV HJTa', results_MAV_HJTa_2026),
    (2028, 'MAV HJTa', results_MAV_HJTa_2028),
#    (2024, 'SAT HJTa', results_SAT_HJTa_2024),
#    (2026, 'SAT HJTa', results_SAT_HJTa_2026),
    (2028, 'SAT HJTa', results_SAT_HJTa_2028)
    ]:
    SCENARIO_LABEL, scenario_tables_optimum, revenue, kWh_export, npv_output = results
    graph_data.loc[i,'Year'] = year
    graph_data.loc[i, 'NPV'] = npv_output / 1000000
    graph_data.loc[i, 'Label'] = label
    i += 1


print(graph_data)
graph_data = graph_data.pivot(columns='Label', values='NPV',index='Year')
print(graph_data)
graph_data.plot.line()
plt.gca().legend(bbox_to_anchor=(1.1, 1.05))
plt.gca().set_title('NPV AUD Million')
# plt.show()

for year in [2028]:
    graph_data_year = graph_data.loc[year,:].T
    graph_data_year.plot.bar()
    plt.gca().set_title('NPV for ' + str(year) + ' installation')
    plt.gca().set_xlabel('Scenario')
    plt.gca().set_ylabel('AUD Million')
    fig_title = "NPV - " + str(year)
    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)
    file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
    plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
    plt.close()




