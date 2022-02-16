import pandas as pd
import numpy as np
import os
from pvlib import pvsystem
from pvlib.pvsystem import PVSystem, FixedMount
from pvlib.location import Location
from pvlib.modelchain import ModelChain
import pvlib.bifacial as bifacial

coordinates = [(-18.7692, 133.1659, 'Suncable_Site', 00, 'Australia/Darwin')]  # Coordinates of the solar farm
latitude, longitude, name, altitude, timezone = coordinates[0]
location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)

solar_position_all = Location.get_solarposition(location, weather_solcast.index, weather_solcast['temp_air'])

# Choose a sample year
weather_data = weater_solcast['2018']
solar_position = solar_position_all['2018']

solar_azimuth = solar_position['azimuth']
solar_zenith = solar_position['zenith']
surface_azimuth = solar_position['zenith']
surface_tilt = # check tracking algorithm
axis_azimuth = 0
timestamps = solar_position.index
dni = weather_data['dni']
dhi = weather_data['dhi']
gcr = 0.33



bifacial.pvfactors_timeseries()