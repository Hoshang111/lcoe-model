""" This is the main script for the yield assessment. The script calls the functions below to calculate the Net Present Value
(NPV) of the solar farm

1) Set overall conditions and parameters for the analysis:

2) Optimise number of racks for SAT

3) Optimise number of racks for MAV

4) Monte Carlo cost analysis

5) Calculate LCOE/NPV for each iteration and plot findings

6) Calculate delta LCOE/NPV for each iteration and plot findings
"""

# %% Import
import pandas as pd
import numpy as np
import Simulation_functions as func
import airtable
import sizing
import Plotting as plot_func
import matplotlib.pyplot as plt
import OptimiseLayout as optimise
import importlib
import SuncableCost as Suncost
# %%
# Set overall conditions and simulation parameters for this analysis

# Weather
simulation_years = [2019]
weather_file = 'Solcast_PT60M.csv'
weather_simulation = func.weather(simulation_years, weather_file)

# Sizing/rack and module numbers
# Call the constants from the database - unneeded if we just pass module class?
DCTotal = 11000  # DC size in MW
num_of_zones = 267  # Number of smaller zones that will make up the solar farm
zone_area = 4e5   # Zone Area in m2
rack_interval_ratio = 0.04
module_type = 'HJT_2028_M10'  # Enter one of the modules from the SunCable module database
install_year = 2027
analysis_year_start = 2024

# Yield Assessment Inputs
temp_model = 'sapm'  # choose a temperature model either Sandia: 'sapm' or PVSyst: 'pvsyst'

# Revenue and storage behaviour
export_lim = 3.2e9/num_of_zones
storage_capacity = 4e7
scheduled_price = 0.00004  # 4c/kWh (conversion from Wh to kWh)

# Financial Parameters
discount_rate = 0.07

# cost data tables from airtable
data_tables = sizing.get_airtable()
# %% ======================================
# Optimise rack number for SAT
rack_type = 'SAT_1'  # Choose rack_type from 5B_MAV or SAT_1 for maverick or single axis tracking respectively
scenario_tables_optimum_SAT, revenue_SAT, kWh_export_SAT = optimise.optimise_layout(weather_simulation, rack_type,
                                                                                    module_type, install_year, DCTotal,
                                                                                    num_of_zones, zone_area,
                                                                                    rack_interval_ratio, temp_model,
                                                                                    export_lim, storage_capacity,
                                                                                    scheduled_price, data_tables,
                                                                                    discount_rate)
# %% =====================================
# Optimise rack number fo MAVs
importlib.reload(optimise)  # Why do we need this?
rack_type = '5B_MAV'
scenario_tables_optimum_MAV, revenue_MAV, kWh_export_MAV = optimise.optimise_layout(weather_simulation, rack_type,
                                                                                    module_type, install_year, DCTotal,
                                                                                    num_of_zones, zone_area,
                                                                                    rack_interval_ratio, temp_model,
                                                                                    export_lim, storage_capacity,
                                                                                    scheduled_price, data_tables,
                                                                                    discount_rate)
#%%
# Call Monte Carlo Cost analysis
# First generate data tables with the ScenarioID changed to something more intuitive
new_data_tables = optimise.form_new_data_tables(data_tables,
                                                [(scenario_tables_optimum_SAT, 'SAT'),
                                                 (scenario_tables_optimum_MAV, 'MAV')])

# Create iteration data
data_tables_iter = Suncost.create_iteration_tables(new_data_tables, 500, iteration_start=0)

# Calculate cost result
outputs_iter = Suncost.CalculateScenariosIterations(data_tables_iter, year_start=analysis_year_start, analyse_years=30)
component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, cash_flow_by_year_iter = outputs_iter
# %% ==========================================================
# Calculate LCOE and/or NPV for each iteration, and plot these for each optimum scenario.
# First generate a big table with index consisting of Iteration, Year, ScenarioID.
combined_scenario_data = pd.DataFrame()
for (scenario_id, revenue_data, kWh_export_data) in [('MAV', revenue_MAV, kWh_export_MAV),
                                                     ('SAT', revenue_SAT, kWh_export_SAT)]:

    kWh_export_data.name = 'kWh'
    revenue_data.name = 'revenue'
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
                                                 (combined_scenario_data['Year'] - analysis_year_start)


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
    data = pd.pivot_table(data, index='Iteration', values = parameter, columns='ScenarioID')
    data.plot.hist(bins=50, histtype='step')
    plt.title(parameter)
    plt.show()
#%%
# Calculate delta_LCOE and delta NPV for each iteration and plot this.
scenario1 = 'MAV'
scenario2 = 'SAT'

for parameter in ['LCOE', 'NPV']:
    data = discounted_sum[parameter].reset_index()
    data = pd.pivot_table(data, index='Iteration', values=parameter, columns='ScenarioID')
    data['Difference'] = data[scenario2] - data[scenario1]
    data['Difference'].plot.hist(bins=50, histtype='step')
    plt.title('Difference in ' + parameter)
    plt.show()

# %%
font_size = 15
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
parameters = Suncost.generate_parameters(data_tables_iter)
parameters_flat = parameters.copy()
parameters_flat.columns = [group + ' ' + str(ID) + ' ' + var for (group, ID, var) in parameters_flat.columns.values]

factor = generate_difference_factor(discounted_sum, 'LCOE', 'MAV', 'SAT', 'LCOE_Difference')
parameters_flat = parameters_flat.join(factor)

Suncost.calculate_variance_contributions(parameters_flat, 'LCOE_Difference')

# %% ==========================================================
# Present data from probabalistic analysis

cash_flow_transformed = pd.pivot_table(cash_flow_by_year_iter.reset_index(), columns='Iteration', index='Year')
revmax_direct = direct_revenue[racks_per_zone_max]
revmax_store = store_revenue[racks_per_zone_max]
revmax_total = total_revenue[racks_per_zone_max]
kWh_iter = kWh_discounted[racks_per_zone_max]
revmax_total_df = pd.DataFrame(revmax_total)
revenue_series_iter = sizing.align_cashflows(cash_flow_transformed, revmax_total_df)
npv_iter, yearly_npv_iter, npv_cost_iter, npv_revenue_iter, Yearly_NPV_revenue_iter, Yearly_NPV_costs_iter \
    = sizing.get_npv(cash_flow_transformed, revenue_series_iter, discount_rate)
LCOE_iter = npv_cost_iter/kWh_iter*100

filename = rack_type + ' ' + module_type + ' install_' + str(install_year)
npv_iter.to_csv('.\\Data\\OutputData\\' + filename + ' NPV.csv')
LCOE_iter.to_csv('.\\Data\\OutputData\\' + filename + ' LCOE.csv')


