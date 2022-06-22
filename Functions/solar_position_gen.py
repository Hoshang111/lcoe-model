from pvlib.location import Location
import pandas as pd
import numpy as np
import os
import pytz

coordinates = [(27.671, 85.4298, 'Bhaktapur', 1401, 'Asia/Kathmandu')]  # Coordinates of the solar farm
latitude, longitude, name, altitude, timezone = coordinates[0]
location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)

simulation_period = pd.date_range(start='1/1/2018 00:00:00', end='7/1/2018 23:59:00', freq='H')

solar_position = location.get_solarposition(simulation_period)
clearsky = location.get_clearsky(simulation_period)

save_path = "C:/Users/phill/documents/SOLA9103/bhaktapur"

solar_position.to_csv(save_path + '_sol_pos.csv')
clearsky.to_csv(save_path + 'clearsky.csv')
