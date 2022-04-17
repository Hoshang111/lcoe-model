import pandas as pd
import os
import datetime as dt

data_path = "D:/Bangladesh Application/weather_data/"
ground_path = os.join(data_path, "feni_ground_measurements")
ground_data = pd.read_csv(ground_path, index_col=0)
ground_data.set_index(pd.to_datetime(ground_data.index, inplace=True))

satellite_path = os.join(data_path, "ninja_feni_joined")
satellite_data = pd.read_csv(satellite_path, index_col=0)
satellite_data.set_index(pd.to_datetime(satellite_data.index, inplace=True))

# satellite_data_aligned =
ground_data_hourly = ground_data.groupby(ground_data.index.dt.hour).sum()
ground_data_aligned = ground_data_hourly.reindex_like(satellite_data)