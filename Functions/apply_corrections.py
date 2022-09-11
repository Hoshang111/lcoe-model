import _pickle as cpickle
import os
import pandas as pd
import numpy as np
import Functions.weather_functions as weather

# %% ===================================================
data_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data"
file_path = os.path.join(data_path, "corrections.p")
corrections = cpickle.load(open(file_path, 'rb'))

#%% ====================================================
# import ground and satellite data
data_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data"
ground_path = os.path.join(data_path, "qcrad_data.csv")
ground_data = pd.read_csv(ground_path, index_col=0, header=0)
ground_data.set_index(pd.to_datetime(ground_data.index), inplace=True)

satellite_data_2017_path = os.path.join(data_path, "Feni_Himawari_2017.csv")
satellite_data_2018_path = os.path.join(data_path, "Feni_Himawari_2018.csv")
satellite_data_2019_path = os.path.join(data_path, "Feni_Himawari_2019.csv")
satellite_data_2017 = pd.read_csv(satellite_data_2017_path, header=2)
satellite_data_2018 = pd.read_csv(satellite_data_2018_path, header=2)
satellite_data_2019 = pd.read_csv(satellite_data_2019_path, header=2)
satellite_data_2017.set_index(pd.to_datetime(satellite_data_2017[["Year", "Month", "Day", "Hour", "Minute"]]), inplace=True)
satellite_data_2018.set_index(pd.to_datetime(satellite_data_2018[["Year", "Month", "Day", "Hour", "Minute"]]), inplace=True)
satellite_data_2019.set_index(pd.to_datetime(satellite_data_2019[["Year", "Month", "Day", "Hour", "Minute"]]), inplace=True)
satellite_data_localtz = pd.concat([satellite_data_2017, satellite_data_2018, satellite_data_2019], axis=0)
satellite_data_aware = satellite_data_localtz.tz_localize("Asia/Dhaka")
satellite_data = satellite_data_aware.tz_convert("UTC")
satellite_data = satellite_data.rename(columns={'GHI':'ghi',
                                                'DHI':'dhi',
                                                'DNI':'dni',
                                                'Temperature':'temp',
                                                'Wind Speed':'wind_speed',
                                                'Clearsky GHI':'clearsky ghi',
                                                'Cloud Type':'cloud type'})
satellite_data_aware = satellite_data_aware.rename(columns={'GHI':'ghi',
                                                'DHI':'dhi',
                                                'DNI':'dni',
                                                'Temperature':'temp',
                                                'Wind Speed':'wind_speed',
                                                'Clearsky GHI':'clearsky ghi',
                                                'Cloud Type':'cloud type'})

#%% Align Data
# satellite_data_aligned =
ground_data_mod = ground_data.shift(periods=5, freq='T')
ground_data_hourly = ground_data_mod.resample('10T', axis=0).mean()
# ground_data_hourly = ground_data_hourlyA.shift(periods=-5, freq='T')
satellite_data_aligned = satellite_data.reindex(ground_data_hourly.index)

ground_dhi = ground_data_hourly['dhi']
ground_ghi = ground_data_hourly['ghi']
ground_dni = satellite_data_aligned['dni']

satellite_dhi = satellite_data_aligned['dhi']
satellite_ghi = satellite_data_aligned['ghi']
satellite_dni = satellite_data_aligned['dni']

# %% ===========================================================
# Define conditions of interest: Cloud types
satellite_cloud0 = satellite_data_aligned.loc[satellite_data['cloud type'] == 0, ['ghi', 'dhi', 'dni']]
ground_cloud0 = ground_data_hourly.loc[satellite_data['cloud type'] == 0, ['ghi', 'dhi', 'dni']]

satellite_cloud1 = satellite_data_aligned.loc[satellite_data['cloud type'] == 1, ['ghi', 'dhi', 'dni']]
ground_cloud1 = ground_data_hourly.loc[satellite_data['cloud type'] == 1, ['ghi', 'dhi', 'dni']]

satellite_cloud2 = satellite_data_aligned.loc[satellite_data['cloud type'] == 2, ['ghi', 'dhi', 'dni']]
ground_cloud2 = ground_data_hourly.loc[satellite_data['cloud type'] == 2, ['ghi', 'dhi', 'dni']]

satellite_cloud3 = satellite_data_aligned.loc[satellite_data['cloud type'] == 3, ['ghi', 'dhi', 'dni']]
ground_cloud3 = ground_data_hourly.loc[satellite_data['cloud type'] == 3, ['ghi', 'dhi', 'dni']]

satellite_cloud4 = satellite_data_aligned.loc[satellite_data['cloud type'] == 4, ['ghi', 'dhi', 'dni']]
ground_cloud4 = ground_data_hourly.loc[satellite_data['cloud type'] == 4, ['ghi', 'dhi', 'dni']]

# satellite_cloud5 = satellite_data_aligned.loc[satellite_data['cloud type'] == 5, ['ghi']]
# ground_cloud5 = ground_data_hourly.loc[satellite_data['cloud type'] == 5, ['ghi']]

satellite_cloud6 = satellite_data_aligned.loc[satellite_data['cloud type'] == 6, ['ghi', 'dhi', 'dni']]
ground_cloud6 = ground_data_hourly.loc[satellite_data['cloud type'] == 6, ['ghi', 'dhi', 'dni']]

satellite_cloud7 = satellite_data_aligned.loc[satellite_data['cloud type'] == 7, ['ghi', 'dhi', 'dni']]
ground_cloud7 = ground_data_hourly.loc[satellite_data['cloud type'] == 7, ['ghi', 'dhi', 'dni']]

cloud_list_satellite = [satellite_cloud0, satellite_cloud1, satellite_cloud2, satellite_cloud3, satellite_cloud4,
              satellite_cloud6, satellite_cloud7]

cloud_list_ground = [ground_cloud0, ground_cloud1, ground_cloud2, ground_cloud3, ground_cloud4,
              ground_cloud6, ground_cloud7]

labels = ['cloud0', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'cloud6', 'cloud7']

cloud_zip = list(zip(cloud_list_satellite, cloud_list_ground, labels))

# %% =======================================================
dhi_corrected = []
ghi_corrected = []

for key in corrections:
    if 'ghi' in key:
        ghi_corrected.append(corrections[key][3])
    elif 'dhi' in key:
        dhi_corrected.append(corrections[key][3])

df_ghi_corrected = pd.concat(ghi_corrected)
df_ghi_corrected.sort_index(inplace=True)

df_dhi_corrected = pd.concat(dhi_corrected)
df_dhi_corrected.sort_index(inplace=True)

corrected_full = pd.concat([df_ghi_corrected, df_dhi_corrected], axis=1)

weather.weather_nofit(ground_ghi, satellite_ghi, 'ghi_no_correction')
weather.weather_nofit(ground_ghi, corrected_full['ghi'], 'ghi_full_correction')
