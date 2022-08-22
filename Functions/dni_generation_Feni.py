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

coordinates = [(22.79993, 91.35836, 'Feni', 9, 'Asia/Dhaka')]  # Coordinates of the solar farm
latitude, longitude, name, altitude, timezone = coordinates[0]
location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)

data_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data"
ground_path = os.path.join(data_path, "ground_measurements_feni.csv")
ground_data_a = pd.read_csv(ground_path, index_col=0, header=1)
ground_data_a.set_index(pd.to_datetime(ground_data_a.index), inplace=True)
ground_data_a = ground_data_a.rename(columns = {'DHI_ThPyra2_Wm-2_avg':'dhi',
                                                 'GHI_ThPyra1_Wm-2_avg':'ghi',
                                                 'DNI_ThPyrh1_Wm-2_avg':'dni',
                                                 'Temp_ThPyra1_degC_avg':'temp',
                                                 'WindSpeed_Anemo1_ms_avg':'wind_speed',
                                                  'RH_ThHyg1_per100_avg':'relative_humidity'})
ground_data = ground_data_a.tz_localize("UTC")

solpos = location.get_solarposition(ground_data.index)
clearsky = location.get_clearsky(ground_data.index)
# suntimes = location.get_sun_rise_set_transit(weather_dnv.index, method='spa')
# transit_zenith = location.get_solarposition(suntimes['transit'])

## Create Dni lookup table based on 1 minute data
dt_lookup = pd.date_range(start= ground_data.index[0],
                          end= ground_data.index[-1], freq='T', tz=pytz.UTC)
clearsky_lookup = location.get_clearsky(dt_lookup)
solpos_lookup = location.get_solarposition(dt_lookup)
zenith_to_rad = np.radians(solpos_lookup)
cos_lookup = np.cos(zenith_to_rad)
cos_lookup[cos_lookup > 30] = 30
cos_lookup[cos_lookup < 0] = 0
horizontal_dni_lookup = cos_lookup['apparent_zenith']*clearsky_lookup['dni']
horizontal_dni_lookup[horizontal_dni_lookup < 0] = 0
clearsky_dni_lookup = clearsky_lookup['dni']
dni_lookup = clearsky_dni_lookup/horizontal_dni_lookup
dni_lookup[dni_lookup>30] = 30
# dni_lookup = ratio_lookup.shift(periods=1)

dni_simulated = (ground_data['ghi']-ground_data['dhi'])*dni_lookup

dni_simulated.to_csv(os.path.join('../Data', 'WeatherData', 'dni_simulated_Feni.csv'),
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


