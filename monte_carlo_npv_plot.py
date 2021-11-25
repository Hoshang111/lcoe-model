# %% ============================
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

npv_mav_iter = pd.read_csv(os.path.join('Data', 'OutputData', '5B_MAV LPERC_2023_M10.csv'), index_col=1)
Scenario_name = str(npv_mav_iter['ScenarioID'].values[0]) + ' MAVs'
npv_mav_iter = npv_mav_iter.rename(columns={'0':Scenario_name})

npv_sat_iter = pd.read_csv(os.path.join('Data', 'OutputData', 'SAT_1 LPERC_2023_M10.csv'), index_col=1)
Scenario_name_2 = str(npv_sat_iter['ScenarioID'].values[0]) + ' SATs'
npv_sat_iter = npv_sat_iter.rename(columns={'0':Scenario_name_2})

graph_data = npv_mav_iter.join(npv_sat_iter, rsuffix='p')
print(graph_data)
graph_data_new = graph_data[[Scenario_name, Scenario_name_2]]
graph_data_new.plot.hist(bins = 50, histtype='step')
plt.show()



