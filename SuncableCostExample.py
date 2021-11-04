import os.path
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set path to source code
sys.path.append(os.path.join(".\\src"))
import SuncableCost as SunCost


# Options
option_use_airtable = True
option_use_custom_scenarios = False
option_use_monte_carlo = True

# Either import from airtable (takes longer, up to date data) or from BaselineDatabase excel.
if option_use_airtable:
    # Airtable Import
    api_key = 'keyJSMV11pbBTdswc'
    base_id='appjQftPtMrQK04Aw'
    data_tables = SunCost.import_airtable_data(base_id=base_id, api_key=api_key)
else:
    data_tables = SunCost.import_excel_data('BaselineDatabase.xlsx')




if option_use_custom_scenarios:
    scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list = data_tables
    # Replacing some tables from csv - not needed if you already have some pandas dataframes
    scenario_list_new = pd.read_csv(os.path.join('Data','CostData','Scenariolist.csv'))
    scenario_system_link_new = pd.read_csv(os.path.join('Data','CostData','SystemLink.csv'))
    data_tables = scenario_list_new, scenario_system_link_new, system_list, system_component_link, component_list, currency_list, costcategory_list


if option_use_monte_carlo:
    data_tables_iter = SunCost.create_iteration_tables(data_tables, 500, iteration_start=0)
    print('Iterations generated')
    outputs_iter = SunCost.CalculateScenariosIterations(data_tables_iter, year_start=2024, analyse_years=30)
    print('outputs calculated')
    component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, cash_flow_by_year_iter = outputs_iter

    # Basic graph for quick cross-check

    for (scenarios, title) in [
        # (['1'], 'MAV 14.4GW 2024'),(['2'],'SAT 10.5GW 2024'),(['3'],'MAV 14.4GW 5 yrs'),
        (['3','4'], 'SAT 10.5GW 5 yrs')
    ]:
        scenario_costs_iter = total_cost_y_iter[total_cost_y_iter['ScenarioID'].isin(scenarios)]
        scenario_costs_by_year_iter = pd.pivot_table(scenario_costs_iter, values='TotalCostAUDY', index=['Iteration','Year'], aggfunc=np.sum,
                                                columns=['CostCategory_ShortName'])
        scenario_costs_total_nodiscount = pd.pivot_table(scenario_costs_iter, values='TotalCostAUDY', index=['Iteration'], aggfunc=np.sum,
                                                columns=['ScenarioID'])
        scenario_costs_total_nodiscount.plot.hist(bins=50,histtype='step')
        plt.show()
        print(scenario_costs_total_nodiscount.loc[0, :])


        scenario_costs_by_year_iter[scenario_costs_by_year_iter['Iteration']==0].plot.bar(stacked=True, title='Total Costs by Year - ' + title)
        plt.show()


        scenario_costs_maintenance_iter = scenario_costs_iter[scenario_costs_iter['CostCategoryID'].astype('int64') == 7]
        # print(scenario_costs_maintenance.head())
        scenario_costs_maintenance_by_year_iter = pd.pivot_table(scenario_costs_maintenance_iter, values='TotalCostAUDY',
                                                            index='Year', aggfunc=np.sum,
                                                            columns=['CostCategory_ShortName'])
        scenario_costs_maintenance_by_year_iter.plot.bar(stacked=True, title='Maintenance Costs by Year - ' + title)
        plt.show()

else:
    # Running the cost calculations
    outputs = SunCost.CalculateScenarios(data_tables, year_start=2024, analyse_years=30)

    component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = outputs

    # Basic graph for quick cross-check

    for (scenarios, title) in [
        # (['1'], 'MAV 14.4GW 2024'),(['2'],'SAT 10.5GW 2024'),(['3'],'MAV 14.4GW 5 yrs'),
        (['4'], 'SAT 10.5GW 5 yrs')
    ]:
        scenario_costs = total_cost_y[total_cost_y['ScenarioID'].isin(scenarios)]
        scenario_costs_by_year = pd.pivot_table(scenario_costs, values='TotalCostAUDY', index='Year', aggfunc=np.sum,
                                                columns=['CostCategory_ShortName'])
        scenario_costs_by_year.plot.bar(stacked=True, title='Total Costs by Year - ' + title)
        plt.show()
        scenario_costs.to_csv('temp_scenario_costs.csv')

        scenario_costs_maintenance = scenario_costs[scenario_costs['CostCategoryID'].astype('int64') == 7]
        #print(scenario_costs_maintenance.head())
        scenario_costs_maintenance_by_year = pd.pivot_table(scenario_costs_maintenance, values='TotalCostAUDY',
                                                            index='Year', aggfunc=np.sum,
                                                            columns=['CostCategory_ShortName'])
        scenario_costs_maintenance_by_year.plot.bar(stacked=True, title='Maintenance Costs by Year - ' + title)
        plt.show()
