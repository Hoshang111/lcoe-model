# %% ============================
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

module_name = 'HJT_2028_M10'
install_year = 2028

npv_mav_iter = pd.read_csv(os.path.join('Data', 'OutputData', '5B_MAV ' + module_name + ' install_' + str(install_year) + ' NPV.csv'), index_col=1)
Scenario_name = str(npv_mav_iter['ScenarioID'].values[0]) + ' MAVs'
npv_mav_iter = npv_mav_iter.rename(columns={'0':Scenario_name})

npv_sat_iter = pd.read_csv(os.path.join('Data', 'OutputData', 'SAT_1 ' + module_name + ' install_' + str(install_year) + ' NPV.csv'), index_col=1)
Scenario_name_2 = str(npv_sat_iter['ScenarioID'].values[0]) + ' SATs'
npv_sat_iter = npv_sat_iter.rename(columns={'0':Scenario_name_2})

graph_data_npv = npv_mav_iter.join(npv_sat_iter, rsuffix='p')
print(graph_data_npv)

graph_data_npv2 = graph_data_npv[[Scenario_name, Scenario_name_2]]
graph_data_npv2.plot.hist(bins = 50, histtype='step')
xticks, x_tick_labels = plt.xticks()
plt.xticks(ticks=xticks, labels = xticks/1e6)
plt.xlabel('Net Present Value ($m)', loc='center')
plt.savefig('.\\Data\\OutputData\\' + module_name + ' install_' + str(install_year) + ' NPV', bbox_inches='tight', pad_inches=0.1)
plt.show()

LCOE_mav_iter = pd.read_csv(os.path.join('Data', 'OutputData', '5B_MAV ' + module_name + ' install_' + str(install_year) + ' LCOE.csv'), index_col=1)
Scenario_name_LCOE = str(LCOE_mav_iter['ScenarioID'].values[0]) + ' MAVs'
LCOE_mav_iter = LCOE_mav_iter.rename(columns={'0':Scenario_name})

LCOE_sat_iter = pd.read_csv(os.path.join('Data', 'OutputData', 'SAT_1 ' + module_name + ' install_' + str(install_year) + ' LCOE.csv'), index_col=1)
Scenario_name_LCOE2 = str(LCOE_sat_iter['ScenarioID'].values[0]) + ' SATs'
LCOE_sat_iter = LCOE_sat_iter.rename(columns={'0':Scenario_name_2})

graph_data_LCOE = LCOE_mav_iter.join(LCOE_sat_iter, rsuffix='p')
print(graph_data_LCOE)
graph_data_LCOE2 = graph_data_LCOE[[Scenario_name_LCOE, Scenario_name_LCOE2]]
graph_data_LCOE2.plot.hist(bins = 50, histtype='step')
plt.xlabel('LCOE (c/kWh)', loc='center')
plt.savefig('.\\Data\\OutputData\\' + module_name + ' install_' + str(install_year) + ' LCOE',bbox_inches='tight', pad_inches=0.1)
plt.show()

