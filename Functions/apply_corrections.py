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
# import satellite data
data_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data"
satellite_path = os.path.join(data_path, "qcrad_data.csv")
satellite_data_init = pd.read_csv(satellite_path, index_col=0, header=0)
satellite_data_init.set_index(pd.to_datetime(satellite_data_init.index), inplace=True)

satellite_data_aware = satellite_data_init.tz_localize("Asia/Dhaka")
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


# %% ===========================================================
# Define conditions of interest: Cloud types
satellite_cloud0 = satellite_data.loc[satellite_data['cloud type'] == 0, ['ghi', 'dhi', 'dni']]

satellite_cloud1 = satellite_data.loc[satellite_data['cloud type'] == 1, ['ghi', 'dhi', 'dni']]

satellite_cloud2 = satellite_data.loc[satellite_data['cloud type'] == 2, ['ghi', 'dhi', 'dni']]

satellite_cloud3 = satellite_data.loc[satellite_data['cloud type'] == 3, ['ghi', 'dhi', 'dni']]

satellite_cloud4 = satellite_data.loc[satellite_data['cloud type'] == 4, ['ghi', 'dhi', 'dni']]

# satellite_cloud5 = satellite_data.loc[satellite_data['cloud type'] == 5, ['ghi', 'dhi'], 'dni']

satellite_cloud6 = satellite_data.loc[satellite_data['cloud type'] == 6, ['ghi', 'dhi', 'dni']]

satellite_cloud7 = satellite_data.loc[satellite_data['cloud type'] == 7, ['ghi', 'dhi', 'dni']]

cloud_list_satellite = [satellite_cloud0, satellite_cloud1, satellite_cloud2, satellite_cloud3, satellite_cloud4,
              satellite_cloud6, satellite_cloud7]

labels = ['cloud0', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'cloud6', 'cloud7']

cloud_zip = list(zip(cloud_list_satellite, labels))

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
