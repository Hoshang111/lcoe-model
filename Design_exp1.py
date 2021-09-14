#%%
import pandas as pd
import numpy as np
import matplotlib as plt
import pvlib

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
inverter_parameters = inverters['ABB__PVS980_58_1818kVA_I__600V_'] #ABB 1.8 MVA inverter

# Choose mounting type
#%%
module_tilt = 10
mount1 = pvsystem.FixedMount(surface_tilt=module_tilt,
                             surface_azimuth=90)
mount2 = pvsystem.FixedMount(surface_tilt=module_tilt,
                             surface_azimuth=270)

# Define two arrays resembling Maverick design: one east facing & one west facing
array_one = pvsystem.Array(mount=mount1,
                           module_parameters=module_parameters,
                           temperature_model_parameters='Pvsyst',
                           modules_per_string=30,
                           strings=112)

array_two = pvsystem.Array(mount=mount2,
                           module_parameters=module_parameters,
                           temperature_model_parameters='Pvsyst',
                           modules_per_string=30,
                           strings=112)

mav_system = pvsystem.PVSystem(arrays=[array_one, array_two], inverter_parameters=inverter_parameters)
#%%
# AOI at any point in time can be found based on Solar zenith, and azimuth
zenith = 80
azimuth = 0
mav_aois = mav_system.get_aoi(solar_zenith=zenith, solar_azimuth=azimuth)

#%% Model-Chain