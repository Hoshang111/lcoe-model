#%%
import pandas as pd
import numpy as np
import matplotlib as plt
import pvlib
import pytz

# PV-Lib imports
from pvlib import pvsystem
from pvlib.pvsystem import PVSystem, FixedMount
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
#%%
# Weather
# Elliot is the town's name within Northern territory
site_location = (-12.5, 130.8, 31, 'Darwin', 'Etc/GMT+9:30')
latitude, longitude, name, altitude, timezone = site_location
weather = pvlib.iotools.get_pvgis_tmy(latitude, longitude, map_variables=True)[0]
weather.index.name = "utc_time"

#%%
# Choose module/s and inverter/s (choosing existing module/inverter now, we can easily edit the
# params depending on the real module and inverters to be used.
modules = pvsystem.retrieve_sam('cecmod')
module_parameters = modules['Jinko_Solar_Co___Ltd_JKM265PP_60']

inverters = pvsystem.retrieve_sam('cecinverter')
inverter_parameters = inverters['ABB__PVS980_58_1818kVA_I__600V_']  # ABB 1.8 MVA inverter
#%% Mounting
module_tilt = 10
mount1 = pvsystem.FixedMount(surface_tilt=module_tilt,
                             surface_azimuth=90)
mount2 = pvsystem.FixedMount(surface_tilt=module_tilt,
                             surface_azimuth=270)
temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
# Define two arrays resembling Maverick design: one east facing & one west facing
array_one = pvsystem.Array(mount=mount1,
                           module_parameters=module_parameters,
                           temperature_model_parameters=temperature_model_parameters,
                           modules_per_string=30,
                           strings=112)

array_two = pvsystem.Array(mount=mount2,
                           module_parameters=module_parameters,
                           temperature_model_parameters=temperature_model_parameters,
                           modules_per_string=30,
                           strings=112)

mav_system = pvsystem.PVSystem(arrays=[array_one, array_two], inverter_parameters=inverter_parameters)
#%%
# AOI at any point in time can be found based on Solar zenith, and azimuth
zenith = 80
azimuth = 0
mav_aois = mav_system.get_aoi(solar_zenith=zenith, solar_azimuth=azimuth)
#%% Model-Chain

# Weather can be specified separately for each array (provide a tuple of DFs equal to the number of arrays)
weather = pd.DataFrame([[1050, 1000, 100, 30, 5, 1]],
                       columns=['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed', 'precipitable_water'],
                       index=[pd.Timestamp('20170401 1200', tz='Australia/Darwin')])

location = Location(latitude=-12.5, longitude=130.8)
mc = ModelChain(mav_system, location, aoi_model='ashrae')
#%%
mc.run_model(weather)
mc.results.dc

#%% Model-Chain
temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']  # or use your own params
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
sandia_module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']
cec_inverter = cec_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']

# Location
location = Location(latitude=32.2, longitude=-110.9)

system = PVSystem(surface_tilt=20, surface_azimuth=200,
                  module_parameters=sandia_module,
                  inverter_parameters=cec_inverter,
                  temperature_model_parameters=temperature_model_parameters)

mc = ModelChain(system, location, aoi_model='sapm')
#%% Model Chain from the PV-Lib document
weather = pd.DataFrame([[1050, 1000, 100, 30, 5, 1]],
                       columns=['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed', 'precipitable_water'],
                       index=[pd.Timestamp('20170401 1200', tz='US/Arizona')])
mc.run_model(weather)
