
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
import importlib
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import simulation_functions as func
from layout_optimiser import form_new_data_tables, optimise_layout
import layout_optimiser as optimiser
from simulation_functions import weather
from plotting import plot_save
from sizing import get_airtable
from suncable_cost import calculate_scenarios_iterations, create_iteration_tables, \
     generate_parameters, calculate_variance_contributions, import_excel_data

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
dni_dummy = pd.read_csv(os.path.join('Data', 'WeatherData', 'TMY_dni_simulated_1minute.csv'), index_col=0)
dni_dummy.set_index(pd.to_datetime(dni_dummy.index, utc=False), drop=True, inplace=True)
dni_dummy.index = dni_dummy.index.tz_convert('Australia/Darwin')

weather_dnv.drop(['dni'],axis=1,inplace=True)
weather_dnv = weather_dnv.join(dni_dummy, how='left')
weather_dnv.rename(columns={"0": "dni"}, inplace=True)
weather_dnv = weather_dnv[['ghi','dni','dhi','temp_air','wind_speed','precipitable_water','dc_yield']]
weather_simulation = weather_dnv


# Sizing/rack and module numbers
# Call the constants from the database - unneeded if we just pass module class?
DCTotal = 11000  # DC size in MW
num_of_zones = 720  # Number of smaller zones that will make up the solar farm
zone_area = 1.4e5   # Zone Area in m2
rack_interval_ratio = 0.04

# Yield Assessment Inputs
temp_model = 'sapm'  # choose a temperature model either Sandia: 'sapm' or PVSyst: 'pvsyst'

# Revenue and storage behaviour
export_lim = 3.2e9/num_of_zones # Watts per zone
storage_capacity = 4e7 # Wh per zone
scheduled_price = 0.00004  # AUD / Wh. Assumption: AUD 4c/kWh (conversion from Wh to kWh)

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

scenario_tables_2024 = []
results_SAT_PERC_2024 = optimize (SAT, PERC2023, 2024, 'SAT PERC 2024', scenario_tables_2024)
results_MAV_PERC_2024 = optimize (MAV, PERC2023, 2024, 'MAV PERC 2024', scenario_tables_2024)
results_SAT_HJT_2024 = optimize (SAT, HJT2023, 2024, 'SAT HJT 2024', scenario_tables_2024)
results_MAV_HJT_2024 = optimize (MAV, HJT2023, 2024, 'MAV HJT 2024', scenario_tables_2024)
results_SAT_TOP_2024 = optimize (SAT, TOP2023, 2024, 'SAT TOP 2024', scenario_tables_2024)
results_MAV_TOP_2024 = optimize (MAV, TOP2023, 2024, 'MAV TOP 2024', scenario_tables_2024)
results_SAT_PERCa_2024 = optimize (SAT, PERC2025, 2024, 'SAT PERCa 2024', scenario_tables_2024)
results_MAV_PERCa_2024 = optimize (MAV, PERC2025, 2024, 'MAV PERCa 2024', scenario_tables_2024)
results_SAT_HJTa_2024 = optimize (SAT, HJT2025, 2024, 'SAT HJTa 2024', scenario_tables_2024)
results_MAV_HJTa_2024 = optimize (MAV, HJT2025, 2024, 'MAV HJTa 2024', scenario_tables_2024)
results_SAT_TOPa_2024 = optimize (SAT, TOP2025, 2024, 'SAT TOPa 2024', scenario_tables_2024)
results_MAV_TOPa_2024 = optimize (MAV, TOP2025, 2024, 'MAV TOPa 2024', scenario_tables_2024)

scenario_tables_2026 = []
results_SAT_PERC_2026 = optimize (SAT, PERC2025, 2026, 'SAT PERC 2026',scenario_tables_2026)
results_MAV_PERC_2026 = optimize (MAV, PERC2025, 2026, 'MAV PERC 2026',scenario_tables_2026)
results_SAT_HJT_2026 = optimize (SAT, HJT2025, 2026, 'SAT HJT 2026',scenario_tables_2026)
results_MAV_HJT_2026 = optimize (MAV, HJT2025, 2026, 'MAV HJT 2026',scenario_tables_2026)
results_SAT_TOP_2026 = optimize (SAT, TOP2025, 2026, 'SAT TOP 2026',scenario_tables_2026)
results_MAV_TOP_2026 = optimize (MAV, TOP2025, 2026, 'MAV TOP 2026',scenario_tables_2026)
results_SAT_PERCa_2026 = optimize (SAT, PERC2028, 2026, 'SAT PERCa 2026',scenario_tables_2026)
results_MAV_PERCa_2026 = optimize (MAV, PERC2028, 2026, 'MAV PERCa 2026',scenario_tables_2026)
results_SAT_HJTa_2026 = optimize (SAT, HJT2028, 2026, 'SAT HJTa 2026',scenario_tables_2026)
results_MAV_HJTa_2026 = optimize (MAV, HJT2028, 2026, 'MAV HJTa 2026',scenario_tables_2026)
results_SAT_TOPa_2026 = optimize (SAT, TOP2028, 2026, 'SAT TOPa 2026',scenario_tables_2026)
results_MAV_TOPa_2026 = optimize (MAV, TOP2028, 2026, 'MAV TOPa 2026',scenario_tables_2026)



scenario_tables_2028 = []
results_SAT_PERC_2028 = optimize (SAT, PERC2028, 2028, 'SAT PERC 2028',scenario_tables_2028)
results_MAV_PERC_2028 = optimize (MAV, PERC2028, 2028, 'MAV PERC 2028',scenario_tables_2028)
results_SAT_HJT_2028 = optimize (SAT, HJT2028, 2028, 'SAT HJT 2028',scenario_tables_2028)
results_MAV_HJT_2028 = optimize (MAV, HJT2028, 2028, 'MAV HJT 2028',scenario_tables_2028)
results_SAT_TOP_2028 = optimize (SAT, TOP2028, 2028, 'SAT TOP 2028',scenario_tables_2028)
results_MAV_TOP_2028 = optimize (MAV, TOP2028, 2028, 'MAV TOP 2028',scenario_tables_2028)
results_SAT_PERCa_2028 = optimize (SAT, PERC2031, 2028, 'SAT PERCa 2028',scenario_tables_2028)
results_MAV_PERCa_2028 = optimize (MAV, PERC2031, 2028, 'MAV PERCa 2028',scenario_tables_2028)
results_SAT_HJTa_2028 = optimize (SAT, HJT2031, 2028, 'SAT HJTa 2028',scenario_tables_2028)
results_MAV_HJTa_2028 = optimize (MAV, HJT2031, 2028, 'MAV HJTa 2028',scenario_tables_2028)
results_SAT_TOPa_2028 = optimize (SAT, TOP2031, 2028, 'SAT TOPa 2028',scenario_tables_2028)
results_MAV_TOPa_2028 = optimize (MAV, TOP2031, 2028, 'MAV TOPa 2028',scenario_tables_2028)

# %%
# Call Monte Carlo Cost analysis

for analysis_year in [
    #2024,
    #2026,
    2028

                      ]:


    if analysis_year == 2024:
        scenario_tables = scenario_tables_2024
    elif analysis_year == 2026:
        scenario_tables = scenario_tables_2026
    elif analysis_year == 2028:
        scenario_tables = scenario_tables_2028
    # First generate data tables with the ScenarioID changed to something more intuitive
    new_data_tables = form_new_data_tables(data_tables,scenario_tables)

    # Create iteration data
    data_tables_iter = create_iteration_tables(new_data_tables, 5000, iteration_start=0)

    # Calculate cost result
    outputs_iter = calculate_scenarios_iterations(data_tables_iter, year_start=analysis_year, analyse_years=30)
    component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, cash_flow_by_year_iter = outputs_iter

    # %% ==========================================================
    # Calculate LCOE and/or NPV for each iteration, and plot these for each optimum scenario.
    # First generate a big table with index consisting of Iteration, Year, ScenarioID.
    combined_scenario_data = pd.DataFrame()



    if analysis_year == 2024:
        install_year = 2024
        results = [[results_SAT_PERC_2024,
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
        results_list = [[results_SAT_PERC_2028,
                  results_MAV_PERC_2028,
                  results_SAT_HJT_2028,
                  results_MAV_HJT_2028,
                  results_SAT_TOP_2028,
                  results_MAV_TOP_2028],
                   [results_SAT_PERCa_2028,
                   results_MAV_PERCa_2028,
                   results_SAT_HJTa_2028,
                   results_MAV_HJTa_2028,
                   results_SAT_TOPa_2028,
                   results_MAV_TOPa_2028,
                   ]]

    else:
        print('Error!')


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
            # file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'OutputFigures/', fig_title)
            # plt.savefig(file_name)
            plt.show()

    # %%

    if analysis_year == 2024:
        analysis_list = [(['SAT PERC 2024','MAV PERC 2024'], 'SAT vs MAV 2024')]
    elif analysis_year == 2026:
        analysis_list = [(['SAT PERC 2026', 'MAV PERC 2026'], 'SAT vs MAV 2026')]
    elif analysis_year == 2028:
        analysis_list = [(['SAT PERC 2028', 'MAV PERC 2028'], 'SAT vs MAV 2028')]
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
        scenario_costs_total_category.plot.bar(stacked=True,title='Total Costs by Category - ' + title)
        plt.show()


        scenario_costs_total_nodiscount = pd.pivot_table(scenario_costs_iter, values='TotalCostAUDY',
                                                         index=['Iteration'], aggfunc=np.sum,
                                                         columns=['ScenarioID'])
        scenario_costs_total_nodiscount.plot.hist(bins=50, histtype='step')
        plt.show()



    # %%

    if analysis_year==2024:
        comparison_list = [('MAV HJT 2024','SAT HJT 2024', 'MAV vs SAT HJT 2024'),
                            ('MAV HJT 2024','MAV PERC 2024', 'HJT vs PERC MAV 2024'),
                                               ]

    elif analysis_year == 2026:
        comparison_list = [('MAV PERC 2026', 'SAT PERC 2026', 'MAV vs SAT PERC 2026'),
                           ('MAV HJT 2026', 'MAV PERC 2026', 'HJT vs PERC MAV 2026')]
    elif analysis_year == 2028:
        comparison_list = [('MAV PERC 2028', 'SAT PERC 2028', 'MAV vs SAT PERC 2028'),
                           ('MAV HJT 2028', 'MAV PERC 2028', 'HJT vs PERC MAV 2028')]

    for (scenario_1, scenario_2, savename) in comparison_list:

        for parameter in ['LCOE', 'NPV']:
            data = discounted_sum[parameter].reset_index()
            data = pd.pivot_table(data, index='Iteration', values = parameter, columns='ScenarioID')

            data['Difference'] = data[scenario_2] - data[scenario_1]
            data['Difference'].plot.hist(bins=50, histtype='step')
            fig_title = 'Difference in '+ parameter + ': ' + scenario_2 + ' - ' + scenario_1
            plt.title(fig_title)
            # savefig.save_figure(fig_title)
            # file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)),'OutputFigures/', fig_title)
            # plt.savefig(file_name)
            plt.show()

        font_size = 8
        rc = {'font.size': font_size, 'axes.labelsize': font_size, 'legend.fontsize': font_size,
              'axes.titlesize': font_size, 'xtick.labelsize': font_size, 'ytick.labelsize': font_size}
        plt.rcParams.update(**rc)
        plt.rc('font', weight='bold')

        # For label titles
        fontdict = {'fontsize': font_size, 'fontweight': 'bold'}

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
            'ComponentID 33 AnnualMultiplier': 'Module cost Annual Multiplier'
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

        plt.show()





# %%
#print(results_SAT_PERC_2024)

graph_data = pd.DataFrame(columns=['Year','NPV','Label'], index=[*range(0,1)])
i = 0
for (year, label, results) in [
    (2024, 'MAV PERC', results_MAV_PERC_2024),
    (2026, 'MAV PERC', results_MAV_PERC_2026),
    (2028, 'MAV PERC', results_MAV_PERC_2028),
    (2024, 'SAT PERC', results_SAT_PERC_2024),
    (2026, 'SAT PERC', results_SAT_PERC_2026),
    (2028, 'SAT PERC', results_SAT_PERC_2028),
    (2024, 'MAV PERCa', results_MAV_PERCa_2024),
    (2026, 'MAV PERCa', results_MAV_PERCa_2026),
    (2028, 'MAV PERCa', results_MAV_PERCa_2028),
    (2024, 'SAT PERCa', results_SAT_PERCa_2024),
    (2026, 'SAT PERCa', results_SAT_PERCa_2026),
    (2028, 'SAT PERCa', results_SAT_PERCa_2028),
    (2024, 'MAV TOP', results_MAV_TOP_2024),
    (2026, 'MAV TOP', results_MAV_TOP_2026),
    (2028, 'MAV TOP', results_MAV_TOP_2028),
    (2024, 'SAT TOP', results_SAT_TOP_2024),
    (2026, 'SAT TOP', results_SAT_TOP_2026),
    (2028, 'SAT TOP', results_SAT_TOP_2028),
    (2024, 'MAV TOPa', results_MAV_TOPa_2024),
    (2026, 'MAV TOPa', results_MAV_TOPa_2026),
    (2028, 'MAV TOPa', results_MAV_TOPa_2028),
    (2024, 'SAT TOPa', results_SAT_TOPa_2024),
    (2026, 'SAT TOPa', results_SAT_TOPa_2026),
    (2028, 'SAT TOPa', results_SAT_TOPa_2028),
    (2024, 'MAV HJT', results_MAV_HJT_2024),
    (2026, 'MAV HJT', results_MAV_HJT_2026),
    (2028, 'MAV HJT', results_MAV_HJT_2028),
    (2024, 'SAT HJT', results_SAT_HJT_2024),
    (2026, 'SAT HJT', results_SAT_HJT_2026),
    (2028, 'SAT HJT', results_SAT_HJT_2028),
    (2024, 'MAV HJTa', results_MAV_HJTa_2024),
    (2026, 'MAV HJTa', results_MAV_HJTa_2026),
    (2028, 'MAV HJTa', results_MAV_HJTa_2028),
    (2024, 'SAT HJTa', results_SAT_HJTa_2024),
    (2026, 'SAT HJTa', results_SAT_HJTa_2026),
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
plt.show()

for year in [2024, 2026, 2028]:
    graph_data_year = graph_data.loc[year,:].T
    graph_data_year.plot.bar()
    plt.gca().set_title('NPV for ' + str(year) + ' installation')
    plt.gca().set_xlabel('Scenario')
    plt.gca().set_ylabel('AUD Million')

    plt.show()


# %%

x = parameters_flat['Module Cost']
y = parameters_flat['Onsite Labour Index']
z = parameters_flat['LCOE_Difference']
title = 'Impact on LCOE difference'
p1_description = 'Module Cost'
p2_description = 'Labour Index'
map = 'seismic'
colorbartitle = 'Delta LCOE'
fig, (ax0, ax1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [25, 1]})


scatterplot = ax0.scatter(x, y, c=z, cmap=map, vmin=None, vmax=None, s=None)
plt.colorbar(scatterplot, cax=ax1)
ax1.set_title(colorbartitle)

ax0.set_xlabel(p1_description)
ax0.set_ylabel(p2_description)
ax0.set_title(title)


plt.show()
