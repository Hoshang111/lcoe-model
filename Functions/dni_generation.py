import pandas as pd
import numpy as np
import matplotlib as plt
import pvlib
import pytz
import os
import Functions.simulation_functions as func
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

weather_dnv_file = 'Combined_Longi_570_Tracker-bifacial_FullTS_8m.csv'
os.chdir(os.path.dirname(os.path.abspath(__file__)))
weather_dnv_dummy = pd.read_csv(os.path.join('../Data', 'WeatherData', weather_dnv_file),
                                delimiter=';',
                                index_col=0)
weather_dnv_dummy = weather_dnv_dummy.rename(
        columns={'GlobHor': 'ghi', 'DiffHor': 'dhi', 'BeamHor': 'bhi', 'T_Amb': 'temp_air',
                 'WindVel': 'wind_speed', 'EArray': 'dc_yield'})

weather_dnv = weather_dnv_dummy[['ghi', 'dhi', 'bhi', 'temp_air', 'wind_speed', 'dc_yield']].copy()
weather_dnv.set_index(pd.to_datetime(weather_dnv.index, utc=False, dayfirst=True), inplace=True)
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

dni_simulated.to_csv(os.path.join('../Data', 'WeatherData', 'dni_simulated_full.csv'),
                     header='Dni')

#%% Generate precipitable water

solcast_file = 'Solcast_PT60m.csv'
os.chdir(os.path.dirname(os.path.abspath(__file__)))
weather_solcast = pd.read_csv(os.path.join('../Data', 'WeatherData', solcast_file),
                                delimiter=',',
                                index_col=0)
weather_solcast.set_index(pd.to_datetime(weather_solcast.index, utc=True), inplace=True)
weather_solcast.set_index(weather_solcast.index.tz_convert('Australia/Darwin'), inplace=True, drop=True)
solcast_pw = pd.DataFrame(weather_solcast['PrecipitableWater'])
solcast_pw_shift = solcast_pw.shift(periods=-0.5, freq='H')
solcast_pw_mod = solcast_pw_shift[~((solcast_pw_shift.index.month == 2) & (solcast_pw_shift.index.day == 29))]
solcast_TMY_pw = solcast_pw_mod.groupby([(solcast_pw_mod.index.month), (solcast_pw_mod.index.day), (solcast_pw_mod.index.hour)]).median()
pw_index = weather_dnv_aware.index
first_part = weather_solcast['2007-07-01':'2007-12-31']

start_date = '01/01/2006 00:00'
end_date = '31/12/2021 23:59'

fun_index = pd.date_range(start=start_date, end=end_date, freq='H', tz='Australia/Darwin')
total_index = fun_index[~((fun_index.month == 2) & (fun_index.day == 29))]

pw_df = pd.concat([solcast_TMY_pw]*16, ignore_index=True)

pw_df.index = total_index

solcast_empty = weather_dnv_aware.join(solcast_pw_shift)

solcast_empty.drop(columns=['ghi', 'bhi', 'dhi', 'temp_air', 'wind_speed', 'dc_yield'], inplace=True)

pw_final = solcast_empty.fillna(pw_df)

pw_final.to_csv(os.path.join('../Data', 'WeatherData', 'pw_full.csv'),
                     header='PrecipitableWater')


