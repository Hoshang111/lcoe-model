import pandas as pd
import os
import datetime as dt

ground_path =
ground_data = pd.read_csv(ground_path, index_col=0)

satellite_path =
satellite_data = pd.read_csv(satellite_path, index_col=0)

satellite_data_aligned =
ground_data_hourly = ground_data.groupby(ground_data.index.dt.hour).sum()
ground_data_aligned =