import pandas as pd
import numpy as np
import matplotlib as plt
import pvlib
import pytz
import os
import simulation_functions as func
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



