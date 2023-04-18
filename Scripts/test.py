import os
import _pickle as cpickle

import pandas as pd

current_path = os.getcwd()
parent_path = os.path.dirname(current_path)
pickle_path = os.path.join(parent_path, 'Data', 'mc_analysis', 'analysis_dictionary_test1' + '.p')
scenario_dict = cpickle.load(open(pickle_path, 'rb'))
# df = pd.DataFrame.from_dict(scenario_dict['results_MAV_5P13B_2025']['cost_mc'], orient="index")
print(scenario_dict)