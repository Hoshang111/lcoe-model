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
weather_solcast = func.weather(simulation_years, weather_file)
weather_solcast.set_index(weather_solcast.index.tz_convert('Australia/Darwin'), inplace=True, drop=True)

weather_dnv_file = 'SunCable_TMY_HourlyRes_bifacial_545_4m_result.csv'
os.chdir(os.path.dirname(os.path.abspath(__file__)))
weather_dnv_dummy = pd.read_csv(os.path.join('Data', 'WeatherData', weather_dnv_file),
                                        delimiter=';',
                                        index_col=0)
weather_dnv_dummy = weather_dnv_dummy.rename(
        columns={'GlobHor': 'ghi', 'DiffHor': 'dhi', 'BeamHor': 'bhi', 'T_Amb': 'temp_air',
                 'WindVel': 'wind_speed', 'EArray': 'dc_yield'})

weather_dnv = weather_dnv_dummy[['ghi', 'dhi', 'bhi', 'temp_air', 'wind_speed', 'dc_yield']].copy()
weather_dnv.set_index(pd.to_datetime(weather_dnv.index, utc=False), inplace=True)
weather_dnv.sort_index(inplace=True)

solpos = location.get_solarposition(weather_dnv.index)
clearsky = location.get_clearsky(weather_dnv.index)
# suntimes = location.get_sun_rise_set_transit(weather_dnv.index, method='spa')
# transit_zenith = location.get_solarposition(suntimes['transit'])

## Create Dni lookup table based on 1 minute data
dt_lookup = pd.date_range(start= weather_dnv.index[0],
                          end= weather_dnv.index[-1], freq='T', tz=pytz.UTC)
clearsky_lookup = location.get_clearsky(dt_lookup)
solpos_lookup = location.get_solarposition(dt_lookup)
zenith_to_rad = np.radians(solpos_lookup)
cos_lookup = np.cos(zenith_to_rad)
cos_lookup[cos_lookup > 30] = 30
cos_lookup[cos_lookup < 0] = 0
horizontal_dni_lookup = cos_lookup['apparent_zenith']*clearsky_lookup['dni']
horizontal_dni_lookup[horizontal_dni_lookup < 0] = 0
hz_dni_lookup = horizontal_dni_lookup
hz_dni_lookup.index = horizontal_dni_lookup.index.tz_convert('Australia/Darwin')
hourly_lookup = hz_dni_lookup.resample('H').mean()
clearsky_dni_lookup = clearsky_lookup['dni']
clearsky_dni_lookup.index = clearsky_lookup.index.tz_convert('Australia/Darwin')
hourly_dni_lookup = clearsky_dni_lookup.resample('H').mean()
dni_lookup = hourly_dni_lookup/hourly_lookup
dni_lookup[dni_lookup>30] = 30
# dni_lookup = ratio_lookup.shift(periods=1)

weather_dnv_aware = weather_dnv.tz_localize('Australia/Darwin')
dni_simulated = (weather_dnv_aware['ghi']-weather_dnv_aware['dhi'])*dni_lookup

dni_simulated.to_csv(os.path.join('Data', 'WeatherData', 'dni_simulated.csv'),
                     header='Dni')