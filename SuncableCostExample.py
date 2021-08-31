import os.path
import os
import sys
import pandas as pd

# Set path to source code
sys.path.append(os.path.join(".\\src"))
import SuncableCost as SunCost


# Airtable Import
api_key = 'keyJSMV11pbBTdswc'
base_id='appjQftPtMrQK04Aw'

data_tables = SunCost.import_airtable_data(base_id=base_id, api_key=api_key)
scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list = data_tables


# Replacing some tables from csv - not needed if you already have some pandas dataframes
scenario_list_new = pd.read_csv('inputs/Scenariolist.csv')
print(scenario_list)
print(scenario_list_new)
scenario_system_link_new = pd.read_csv('inputs/SystemLink.csv')
print(scenario_system_link_new)
print(scenario_system_link)
new_data_tables = scenario_list_new, scenario_system_link_new, system_list, system_component_link, component_list, currency_list, costcategory_list

# Running the cost calculations
# outputs = SunCost.CalculateScenarios (data_tables, year_start=2024, analyse_years=30)
outputs = SunCost.CalculateScenarios (new_data_tables, year_start=2024, analyse_years=30)
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

    scenario_costs_maintenance = scenario_costs[scenario_costs['CostCategoryID'] == '7']
    scenario_costs_maintenance_by_year = pd.pivot_table(scenario_costs_maintenance, values='TotalCostAUDY',
                                                        index='Year', aggfunc=np.sum,
                                                        columns=['CostCategory_ShortName'])
    scenario_costs_maintenance_by_year.plot.bar(stacked=True, title='Maintenance Costs by Year - ' + title)
