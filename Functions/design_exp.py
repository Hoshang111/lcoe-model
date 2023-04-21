""" This script is a preliminary design for the MAV yield modelling
In this initial design, we are focusing on the DC yield of the array"""

#  Further information about the design:

# Zone: 20 MW (can be MAV or SAT): We are focusing on a single zone for now with 20 MW capacity
# 20 Zones make up one Field:
# 36 fields make up the total Solar precinct of the SunCable

# MAV has 4 strings and 30 modules per string: 120 modules per MAV: 60 modules east facing/ 60 modules west facing
# MAV tilt is 10 degrees for both directions
# 4 MAVs per inverter (480 modules per inverter).
# %%
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
# mpl.use('Qt5Agg')
# mpl.use('TkAgg')
import pytz
import os
from pvlib import pvsystem
from pvlib.pvsystem import PVSystem, FixedMount
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
# %% Coordinates and weather
coordinates = [(-18.7692, 133.1659, 'Suncable_Site', 00, 'Australia/Darwin')]

os.chdir(os.path.dirname(os.path.abspath(__file__)))

weather = pd.read_csv(os.path.join('../Data', 'WeatherData', 'Solcast_PT60M.csv'), index_col=0)

weather.set_index(pd.to_datetime(weather.index), inplace=True)  # set index to datetime format (each index now
# represents end of the hourly period: i.e. 2007-01-01 02:00:00 represents the measurements between 1-2 am

# Change the timezone of the datetime to Australia/Darwin (this may not be necessary/change timezone at the very end)
# dummy = [str(i)[0:19] for i in weather.index]
# weather.set_index(pd.DatetimeIndex(dummy, tz='UTC'), inplace=True)

weather = weather.rename(columns={'Ghi': 'ghi', 'Dni': 'dni', 'Dhi': 'dhi', 'AirTemp': 'temp_air',
                                  'WindSpeed10m': 'wind_speed', 'PrecipitableWater': 'precipitable_water'})

simulation_year = str(2020)  # for now try to run a simulation with one year (366 days in 2020!)
weather_simulation = weather[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed', 'precipitable_water']].copy()[simulation_year]
weather_simulation['precipitable_water'] = weather_simulation['precipitable_water']/10  # formatting for PV-lib
# %% Modules
suncable_modules = pd.read_csv(os.path.join('../Data', 'SystemData', 'bang_module_database.csv'), index_col=0,
                               skiprows=[1, 2]).T
module = suncable_modules['Jinko_JKM575M_7RL4_TV_PRE']

# Start on the single inverter level first
zone_rated_power = 20000  # in kW (20 MW)
num_of_mav_per_inv = 4  # 4 MAVs per inverter
num_of_mod_per_string = 30  # 30 modules per string
num_of_strings_per_mav = 4  # 4 strings per mav
num_of_mod_per_mav = 120  # 60 east facing 60 west facing
num_of_mod_per_inverter = num_of_mav_per_inv * num_of_mod_per_mav  # 480 modules per inverter
num_of_inv_per_zone = np.ceil(zone_rated_power/(module['STC']/1000 * num_of_mod_per_inverter))  # TODO: This is an
# important assumption to check (i.e., ceil of floor)...
# %% Inverter
dc_rated_power = module['STC']/1000 * num_of_mod_per_inverter  # in kW rated DC power output
dc_to_ac = 1.2
ac_rated_power = dc_rated_power / dc_to_ac  # in kW rated AC power output

inverter_list = pvsystem.retrieve_sam('cecinverter')

# Choose an inverter by narrowing down the options. Assume 5% tolerance for now for the DC and AC ratings...
inv_dc_idx = (inverter_list.loc['Pdco'] >= dc_rated_power * 1000 * 0.95) & \
             (inverter_list.loc['Pdco'] <= dc_rated_power * 1000 * 1.05)

inv_ac_idx = (inverter_list.loc['Paco'] >= ac_rated_power * 1000 * 0.95) & \
             (inverter_list.loc['Paco'] <= ac_rated_power * 1000 * 1.05)

inverter_candidates = inverter_list.T[inv_dc_idx]  # We have 15 candidates. I am choosing the Sungrow for now...
inverter = inverter_candidates.loc['Sungrow_Power_Supply_Co___Ltd___SC250KU__480V_']
# %% Mounting
module_tilt = 10
mount1 = pvsystem.FixedMount(surface_tilt=module_tilt,
                             surface_azimuth=90)  # east facing array
mount2 = pvsystem.FixedMount(surface_tilt=module_tilt,
                             surface_azimuth=270)  # west facing array
temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
# Define two arrays resembling Maverick design: one east facing & one west facing
# For now we are designing at the inverter level with 4 MAVs per inverter
array_one = pvsystem.Array(mount=mount1,
                           module_parameters=module,
                           temperature_model_parameters=temperature_model_parameters,
                           modules_per_string=num_of_mod_per_string,
                           strings=num_of_strings_per_mav * num_of_mav_per_inv/2)

array_two = pvsystem.Array(mount=mount2,
                           module_parameters=module,
                           temperature_model_parameters=temperature_model_parameters,
                           modules_per_string=num_of_mod_per_string,
                           strings=num_of_strings_per_mav * num_of_mav_per_inv/2)

mav_system = PVSystem(arrays=[array_one, array_two], inverter_parameters=inverter)
# %% Model-Chain
coordinates = [(-18.7692, 133.1659, 'Suncable_Site', 00, 'Australia/Darwin')]
latitude, longitude, name, altitude, timezone = coordinates[0]
location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)
mc = ModelChain(mav_system, location, aoi_model='ashrae')
# mc = ModelChain(system, location, aoi_model='sapm')  # another aoi model which could be explored...
mc.run_model(weather_simulation)
# The model calculates according to UTC so we will need to modify the time-stamp to Darwin...
# %%
dc_results_a1 = mc.results.dc[0]['p_mp'].sum()/1000  # kWh
dc_results_a2 = mc.results.dc[1]['p_mp'].sum()/1000  # kWh
