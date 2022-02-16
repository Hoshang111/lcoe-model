import pandas as pd
import numpy as np
import matplotlib as plt
import pvlib
import pytz
import os
import simulation_functions as func
import math
# PV-Lib imports
from pvlib import pvsystem
from pvlib.pvsystem import PVSystem, FixedMount
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

coordinates = [(-18.7692, 133.1659, 'Suncable_Site', 00, 'Australia/Darwin')]  # Coordinates of the solar farm
latitude, longitude, name, altitude, timezone = coordinates[0]
location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)

simulation_years = [2018]
weather_file = 'Solcast_PT60M.csv'
weather_simulation = func.weather(simulation_years, weather_file)

solpos = location.get_solarposition(weather_simulation.index)
clearsky = location.get_clearsky(weather_simulation.index)
suntimes = location.get_sun_rise_set_transit(weather_simulation.index, method='spa')
transit_zenith = location.get_solarposition(suntimes['transit'])

## Create Dni lookup table based on 5 minute data
dt_lookup = pd.date_range(start= weather_simulation.index[0],
                          end= weather_simulation.index[-1], freq='5T')
clearsky_lookup = location.get_clearsky(dt_lookup)
solpos_lookup = location.get_solarposition(dt_lookup)
zenith_to_rad = np.radians(solpos_lookup)
cos_lookup = np.cos(zenith_to_rad)
horizontal_dni_lookup = cos_lookup['apparent_zenith']*clearsky_lookup['dni']
horizontal_dni_lookup[horizontal_dni_lookup<0] = 0
hourly_lookup = horizontal_dni_lookup.resample('H').mean()





