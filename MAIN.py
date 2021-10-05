""" This is the main script for the yield assessment. The script calls the functions below to calculate the Net Present Value
(NPV) of the solar farm

1) Sizing
Input: DC size of the solar farm
Output: Configuration in terms of number of single-axis tracking (SAT) racks or 5B Maverick units (MAV)

2) Weather:
Input: Weather file, year of simulation
Output: Weather dataframe in the required format for PVlib simulatins

3) Racks & modules:
Input: Type of module and rack
Output: Module and rack parameters required for PVlib PVsystem extracted from the module & rack database

4) DC/AC Yield:
Input: number of racks, number of MAVs, weather data, module name, mounting type (optional & future improvement:
temperature rack type, aoi model, back-tracking/optimal tilt angle)
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
During the optimisation process/simulations, cost function will give deterministic values. Once the optimum NPV is found
cost function also give the Monte-Carlo distribution.
"""

# %% Import
import pandas as pd
import numpy as np

# %%
# Sizing
# Call the constants from the database
module_per_rack  # (within sizing function)
module_per_mav  # (within sizing function)

# ======================================
# Weather
weather_simulation = weather_func(weather_file_name, year_simulation)


# ======================================
# Rack_module
rack_params, module_params = rack_module_func(rack_type, module_type)

# ========================================
# DC/AC yield
dc_yield = yield_func(number_of_modules, type_of_module, mounting_type, weather_simulation, gcr)  # number of modules or
# number of mavs/racks etc.

# ac_yield  # (optional at this stage)
# define coordinates within the function
# optional inputs: temp/rack coeff, back-tracking algo, aoi model


# ==========================================
# Revenue and storage behaviour
revenue = revenue_func(dc_yield, export_lim)




# ==========================================
# Cost
cost = cost_func(size)




# ==========================================
# Net present value (NPV)
npv = npv_func(revenue, cost)



# ==========================================
# Todo : In the future temperature (rack type) and aoi and single axis tracking (tracking algorithm)
# Todo : New algorithm will have more optimal tilt angle as well as better tracking