# import os
# import datetime
# import math
# import random as rd
# import numbers
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# from airtable import Airtable
# from scipy import stats

import suncable_cost


# First get data from Airtable
api_key = 'keyJSMV11pbBTdswc'
base_id = 'appjQftPtMrQK04Aw'
table_name = 'YieldParameters'

yield_variables = suncable_cost.get_airtable(base_id, api_key, table_name, sort_by='YieldID')

# Now generate iteration data. Note that all variables are assumed flat distribution in this case (unless specified otherwise in the airtable database).
yield_variables_iter = suncable_cost.generate_iterations(yield_variables, index_name='YieldID',
                                        index_description='YieldName', num_iterations=100,
                                        iteration_start=0, default_dist_type = 'flat')


# Separate out the three sets of variables

yield_variables_baseline = yield_variables_iter[yield_variables_iter['YieldID']==1].set_index('Iteration')
yield_variables_MAV_adj = yield_variables_iter[yield_variables_iter['YieldID']==2].set_index('Iteration')
yield_variables_SAT_adj = yield_variables_iter[yield_variables_iter['YieldID']==3].set_index('Iteration')

# Generate the combined MAV or SAT variables

yield_variables_MAV = yield_variables_baseline.copy()
yield_variables_SAT = yield_variables_baseline.copy()
for (new, adj, id, name) in [
    (yield_variables_MAV, yield_variables_MAV_adj, 4, 'Baseline + MAV'),
    (yield_variables_SAT, yield_variables_SAT_adj, 5, 'Baseline + SAT'),
]:

    new['YieldID'] = id
    new['YieldName'] = name

    for sum_variable in ['ave_temp_increase','degr_annual','non_avail','degr_yr1','tol_mismatch']:
        new[sum_variable] += adj[sum_variable]
    for mult_variable in ['bifaciality_modifier','soiling_modifier']:
        new[mult_variable] *= adj[mult_variable]

# Save files locally - not needed

yield_variables_baseline.to_csv('temp_yield_variables_baseline.csv')
yield_variables_MAV.to_csv('temp_yield_variables_MAV.csv')
yield_variables_SAT.to_csv('temp_yield_variables_SAT.csv')