# pylint: disable=E0401
''' This is the main script for the yield assessment. The script calls the functions below
    to calculate the Net Present Value (NPV) of the solar farm

1) Weather:
Input: Weather file, year of simulation
Output: Weather dataframe in the required format for PVlib simulatins

2) Racks & modules:
Input: Type of module and rack
Output: Module and rack parameters required for PVlib PVsystem extracted
        from the module & rack database

3) Sizing
Input: DC size of the solar farm
Output: Configuration in terms of number of single-axis tracking (SAT) racks or
        5B Maverick units (MAV)

4) DC/AC Yield:
Input: number of racks, number of MAVs, weather data, module name, mounting type
      (optional & future improvement:temperature rack type, aoi model,
       back-tracking/optimal tilt angle)
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
Later, we will convert this to an optimization process which will give the
optimum NPV based on:
    - Configuration
    - Mounting
    - Other parameters (more advanced params like back tracking algo,
      temp/racking type etc.)
During the optimisation process/simulations, cost function will give deterministic values.
Once the optimum NPV is found cost function also give the Monte-Carlo distribution.'''

# %% Import
import importlib
import pandas as pd
import matplotlib.pyplot as plt
from layout_optimiser import form_new_data_tables, optimise_layout
import layout_optimiser as optimiser
from simulation_functions import weather
from sizing import get_airtable
from suncable_cost import calculate_scenarios_iterations, create_iteration_tables, \
     generate_parameters, calculate_variance_contributions

# %%
######################## Constants ######################
# Weather
SIMULATION_YEARS = [2019]
WEATHER_FILE = 'Solcast_PT60M.csv'
weather_simulation = weather(SIMULATION_YEARS, WEATHER_FILE)

'''
Sizing/rack and module numbers
Call the constants from the database - unneeded if we just pass module class?
'''
# DC size in MW
DC_TOTAL = 11000
# Number of smaller zones that will make up the solar farm
NUM_OF_ZONES = 267
# Zone Area in m2
ZONE_AREA = 4e5
RACK_INTERVAL_RATIO = 0.04
# Enter one of the modules from the SunCable module database
MODULE_TYPE = 'HJT_2028_M10'
INSTALL_YEAR = 2027
YEAR_ANALYSIS = 2024

# Yield Assessment Inputs
# Choose a temperature model either Sandia: 'sapm' or PVSyst: 'pvsyst'
TEMP_MODEL = 'sapm'

# Revenue and storage behaviour
EXPORT_LIM = 3.2e9/NUM_OF_ZONES
STORAGE_CAPACITY = 4e7
SCHEDULED_PRICE = 0.00004  # 4c/kWh (conversion from Wh to kWh)

# Financial Parameters
DISCOUNT_RATE = 0.07

# cost data tables from airtable
DATA_TABLES = get_airtable()

#########################################################
# Optimise SATs
# %% ======================================
# Rack_module
# Choose rack_type from 5B_MAV or SAT_1 for maverick or single axis tracking respectively
RACK_TYPE = 'SAT_1'

scenario_tables_optimum_SAT, revenue_SAT, kWh_export_SAT = optimise_layout(weather_simulation,
                    RACK_TYPE, MODULE_TYPE, INSTALL_YEAR,
                    DC_TOTAL, NUM_OF_ZONES, ZONE_AREA, RACK_INTERVAL_RATIO, TEMP_MODEL,
                    EXPORT_LIM, STORAGE_CAPACITY, SCHEDULED_PRICE,
                    DATA_TABLES, DISCOUNT_RATE)

# %% =====================================
# Optimise MAVs
importlib.reload(optimiser)
RACK_TYPE = '5B_MAV'
scenario_tables_optimum_MAV, revenue_MAV, kWh_export_MAV = optimise_layout(weather_simulation,
                     RACK_TYPE, MODULE_TYPE, INSTALL_YEAR,
                     DC_TOTAL, NUM_OF_ZONES, ZONE_AREA, RACK_INTERVAL_RATIO, TEMP_MODEL,
                     EXPORT_LIM, STORAGE_CAPACITY, SCHEDULED_PRICE,
                     DATA_TABLES, DISCOUNT_RATE)


#%%
# Call Monte Carlo Cost analysis

# First generate data tables with the ScenarioID changed to something more intuitive
new_data_tables = form_new_data_tables(DATA_TABLES,
                                                [(scenario_tables_optimum_SAT, 'SAT'),
                                                 (scenario_tables_optimum_MAV, 'MAV')])

# Create iteration data
data_tables_iter = create_iteration_tables(new_data_tables, 500, 0)

# Calculate cost result
outputs_iter = calculate_scenarios_iterations(data_tables_iter, YEAR_ANALYSIS, 30)
component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, \
     cash_flow_by_year_iter = outputs_iter


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
    combined_scenario_data[col_name + '_disc'] = combined_scenario_data[col_name] / \
         (1 + DISCOUNT_RATE) ** (combined_scenario_data['Year'] - YEAR_ANALYSIS)


# Create a new table that removes the year, adding all the discounted flows
discounted_sum = pd.pivot_table(combined_scenario_data, index=['Iteration', 'ScenarioID'], \
    values=['kWh_disc', 'cost_disc', 'revenue_disc'])

# Now calculate LCOE and NPV

discounted_sum['LCOE'] = discounted_sum['cost_disc'] / discounted_sum['kWh_disc']
discounted_sum['NPV'] = discounted_sum['revenue_disc'] - discounted_sum['cost_disc']

print(discounted_sum)

# Plot the LCOE and NPV distributions. For each figure, show each scenario as its own distribution.

for parameter in ['LCOE', 'NPV']:
    data = discounted_sum[parameter].reset_index()
    print(data)
    data = pd.pivot_table(data, 'Iteration', parameter, 'ScenarioID')
    data.plot.hist(50, 'step', 15)
    plt.title(parameter)
    plt.show()


#%%

# Calculate delta_LCOE and delta NPV for each iteration and plot this.
SCENARIO_1 = 'MAV'
SCENARIO_2 = 'SAT'

for parameter in ['LCOE', 'NPV']:
    data = discounted_sum[parameter].reset_index()
    data = pd.pivot_table(data, 'Iteration', parameter, 'ScenarioID')

    data['Difference'] = data[SCENARIO_2] - data[SCENARIO_1]
    data['Difference'].plot.hist(50, 'step')
    plt.title('Difference in '+ parameter)
    plt.show()

# %%

FONT_SIZE = 15
rc = {'font.size': FONT_SIZE, 'axes.labelsize': FONT_SIZE, 'legend.fontsize': FONT_SIZE,
      'axes.titlesize': FONT_SIZE, 'xtick.labelsize': FONT_SIZE, 'ytick.labelsize': FONT_SIZE}
plt.rcParams.update(**rc)
plt.rc('font', 'bold')

# For label titles
fontdict = {'fontsize': FONT_SIZE, 'fontweight': 'bold'}


'''
Function that generates a difference factor
'''
def generate_difference_factor(diff_factor, param_factor, scenario_1, scenario_2, parameter_name):
    data_factor = diff_factor[param_factor].reset_index()
    data_factor = pd.pivot_table(data_factor, 'Iteration', param_factor, 'ScenarioID')
    data_factor[parameter_name] = data_factor[scenario_2] - data_factor[scenario_1]
    return data[parameter_name]


# Sensitivity analysis / regression analysis to determine key uncertainties affecting these.
parameters = generate_parameters(data_tables_iter)
parameters_flat = parameters.copy()
parameters_flat.columns = [group + ' ' + str(ID) + ' ' + var \
    for (group, ID, var) in parameters_flat.columns.values]

factor = generate_difference_factor(discounted_sum, 'LCOE', 'MAV', 'SAT', 'LCOE_Difference')
parameters_flat = parameters_flat.join(factor)

calculate_variance_contributions(parameters_flat, 'LCOE_Difference')

# %%

# %% ==========================================================
# Present data from probabalistic analysis

# cash_flow_transformed = pd.pivot_table(cash_flow_by_year_iter.reset_index(), \
# columns='Iteration', index='Year')
# revmax_direct = direct_revenue[racks_per_zone_max]
# revmax_store = store_revenue[racks_per_zone_max]
# revmax_total = total_revenue[racks_per_zone_max]
# kWh_iter = kWh_discounted[racks_per_zone_max]
# revmax_total_df = pd.DataFrame(revmax_total)
# revenue_series_iter = sizing.align_cashflows(cash_flow_transformed, revmax_total_df)
# npv_iter, yearly_npv_iter, npv_cost_iter, npv_revenue_iter, Yearly_NPV_revenue_iter, \
# Yearly_NPV_costs_iter = sizing.get_npv(cash_flow_transformed, revenue_series_iter, \
# discount_year)
# LCOE_iter = npv_cost_iter/kWh_iter*100

# FILENAME = RACK_TYPE + ' ' + MODULE_TYPE + ' install_' + str(INSTALL_YEAR)
# npv_iter.to_csv('.\\Data\\OutputData\\' + FILENAME + ' NPV.csv')
# LCOE_iter.to_csv('.\\Data\\OutputData\\' + FILENAME + ' LCOE.csv')
