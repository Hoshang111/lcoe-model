import _pickle as cpickle
import os
import pandas as pd
import pytz
import numpy as np
import Functions.weather_functions as weather
import pvlib
from pvlib.location import Location

# %% ===================================================
data_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data"
file_path = os.path.join(data_path, "corrections.p")
corrections = cpickle.load(open(file_path, 'rb'))

# %% ===================================================
def get_dni(location, ghi, dhi):
    dt_lookup = pd.date_range(start=ghi.index[0],
                              end=ghi.index[-1], freq='T', tz=pytz.UTC)
    solpos_lookup = location.get_solarposition(dt_lookup)
    clearsky_lookup = location.get_clearsky(dt_lookup)
    zenith_to_rad = np.radians(solpos_lookup)
    cos_lookup = np.cos(zenith_to_rad)
    cos_lookup[cos_lookup > 30] = 30
    cos_lookup[cos_lookup < 0] = 0
    horizontal_dni_lookup = cos_lookup['apparent_zenith'] * clearsky_lookup['dni']
    horizontal_dni_lookup[horizontal_dni_lookup < 0] = 0
    hz_dni_lookup = horizontal_dni_lookup
 #   hz_dni_lookup.index = horizontal_dni_lookup.index.tz_convert('Asia/Dhaka')
    hz_dni_lookup.index = hz_dni_lookup.index.shift(periods=30)
    hourly_lookup = hz_dni_lookup.resample('H').mean()
    clearsky_dni_lookup = clearsky_lookup['dni']
 #   clearsky_dni_lookup.index = clearsky_lookup.index.tz_convert('Asia/Dhaka')
    clearsky_dni_lookup.index = clearsky_dni_lookup.index.shift(periods=30)
    hourly_dni_lookup = clearsky_dni_lookup.resample('H').mean()
    dni_lookup = hourly_dni_lookup / hourly_lookup
    dni_lookup[dni_lookup > 30] = 30
    dni_lookup.index = dni_lookup.index.shift(periods=-30, freq='T')
    dni_simulated = (ghi-dhi)*dni_lookup
    dni_simulated.rename('dni', inplace=True)

    return dni_simulated

#%% ====================================================
# import satellite data
data_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data\TMY\Sumitomo"
satellite_path = os.path.join(data_path, "sumitomo_TMY_2020.csv")
satellite_init = pd.read_csv(satellite_path,  header=2)
satellite_init['Year'] = 2020
dummy = pd.DataFrame([satellite_init['Year'], satellite_init['Month'], satellite_init['Day'],
                          satellite_init['Hour'], satellite_init['Minute']])
dt_index = pd.to_datetime(dummy.T)
satellite_init.index = dt_index
satellite_data = satellite_init.tz_localize("UTC")
# satellite_data = satellite_data_aware.tz_convert("UTC")
satellite_data = satellite_data.rename(columns={'GHI':'ghi',
                                                'DHI':'dhi',
                                                'DNI':'dni',
                                                'Temperature':'temp',
                                                'Wind Speed':'wind_speed',
                                                'Clearsky GHI':'clearsky ghi',
                                                'Cloud Type':'cloud type'})


# %% ===========================================================
# Load site details
coordinates = [(21.986667, 90.241667, 'Patuakhali', 9, 'Asia/Dhaka')]  # Coordinates of the solar farm
latitude, longitude, name, altitude, timezone = coordinates[0]
site = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)


# %% ===========================================================
# Define conditions of interest: Cloud types
satellite_cloud0 = satellite_data.loc[satellite_data['cloud type'] == 0, ['ghi', 'dhi', 'dni']]

satellite_cloud1 = satellite_data.loc[satellite_data['cloud type'] == 1, ['ghi', 'dhi', 'dni']]

satellite_cloud2 = satellite_data.loc[satellite_data['cloud type'] == 2, ['ghi', 'dhi', 'dni']]

satellite_cloud3 = satellite_data.loc[satellite_data['cloud type'] == 3, ['ghi', 'dhi', 'dni']]

satellite_cloud4 = satellite_data.loc[satellite_data['cloud type'] == 4, ['ghi', 'dhi', 'dni']]

if 5 in satellite_data['cloud type']:
    satellite_cloud5 = satellite_data.loc[satellite_data['cloud type'] == 5, ['ghi', 'dhi'], 'dni']
else:
    satellite_cloud5 = pd.DataFrame()

satellite_cloud6 = satellite_data.loc[satellite_data['cloud type'] == 6, ['ghi', 'dhi', 'dni']]

satellite_cloud7 = satellite_data.loc[satellite_data['cloud type'] == 7, ['ghi', 'dhi', 'dni']]

satellite_cloud8 = satellite_data.loc[satellite_data['cloud type'] == 8, ['ghi', 'dhi', 'dni']]

satellite_cloud9 = satellite_data.loc[satellite_data['cloud type'] == 9, ['ghi', 'dhi', 'dni']]

cloud_list_satellite = [satellite_cloud0, satellite_cloud1, satellite_cloud2, satellite_cloud3, satellite_cloud4,
              satellite_cloud5, satellite_cloud6, satellite_cloud7, satellite_cloud8, satellite_cloud9]

labels = ['cloud0', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'cloud5', 'cloud6', 'cloud7', 'cloud8', 'cloud9']

cloud_zip = list(zip(cloud_list_satellite, labels))

# %% =======================================================
dhi_corrected = []
ghi_corrected = []

for data, id in cloud_zip:
    if len(data.index) > 0:
        ghi_label = id + '_ghi'
        dhi_label = id + '_dhi'

        if ghi_label in corrections.keys():
            ghi_factors = corrections[ghi_label][0:3]
        else:
            ghi_factors = [0, 1, 0]
        if dhi_label in corrections.keys():
            dhi_factors = corrections[dhi_label][0:3]
        else:
            dhi_factors = [0, 1, 0]


        ghi_correction = data['ghi']**2*ghi_factors[2] + data['ghi']*ghi_factors[1]\
                + ghi_factors[0]
        dhi_correction = data['dhi'] ** 2 * dhi_factors[2] + data['dhi'] * dhi_factors[1] \
                    + dhi_factors[0]
        ghi_corrected.append(ghi_correction)
        dhi_corrected.append(dhi_correction)

df_ghi_corrected = pd.concat(ghi_corrected)
df_ghi_corrected.sort_index(inplace=True)

df_dhi_corrected = pd.concat(dhi_corrected)
df_dhi_corrected.sort_index(inplace=True)

corrected_full = pd.concat([df_ghi_corrected, df_dhi_corrected], axis=1)

df_dhi_corrected.loc[(df_dhi_corrected<0)] = 0
df_ghi_corrected.loc[(df_ghi_corrected<0)] = 0
df_dni_corrected = get_dni(location=site, ghi=df_ghi_corrected, dhi=df_dhi_corrected)

TMY_dummy = satellite_data.drop(['ghi', 'dhi', 'dni'], axis=1)
new_TMY = pd.concat([TMY_dummy, df_ghi_corrected, df_dhi_corrected, df_dni_corrected], axis =1)

save_path = os.path.join(data_path, 'corrected_sumi_TMY.csv')
new_TMY.to_csv(save_path)

def weather_correct(weather_file, corrections, location):
    """"""

    # Define conditions of interest: Cloud types

    cloud_list = []
    for i in range(9):
        label = 'cloud' + str(i)
        if i in weather_file['cloud type']:
            locals()[label] = weather_file.loc[weather_file['cloud type'] == 0, ['ghi', 'dhi', 'dni']]
        else:
            locals()[label] = pd.DataFrame()

        cloud_list.append(locals()[label])

    labels = ['cloud0', 'cloud1', 'cloud2', 'cloud3', 'cloud4', 'cloud5', 'cloud6', 'cloud7', 'cloud8', 'cloud9']

    cloud_zip = list(zip(cloud_list_satellite, labels))

    dhi_corrected = []
    ghi_corrected = []

    for data, id in cloud_list:
        if len(data.index) > 0:
            ghi_label = id + '_ghi'
            dhi_label = id + '_dhi'

            if ghi_label in corrections.keys():
                ghi_factors = corrections[ghi_label][0:3]
            else:
                ghi_factors = [0, 1, 0]
            if dhi_label in corrections.keys():
                dhi_factors = corrections[dhi_label][0:3]
            else:
                dhi_factors = [0, 1, 0]

            ghi_correction = data['ghi'] ** 2 * ghi_factors[2] + data['ghi'] * ghi_factors[1] \
                             + ghi_factors[0]
            dhi_correction = data['dhi'] ** 2 * dhi_factors[2] + data['dhi'] * dhi_factors[1] \
                             + dhi_factors[0]
            ghi_corrected.append(ghi_correction)
            dhi_corrected.append(dhi_correction)

    df_ghi_corrected = pd.concat(ghi_corrected)
    df_ghi_corrected.sort_index(inplace=True)

    df_dhi_corrected = pd.concat(dhi_corrected)
    df_dhi_corrected.sort_index(inplace=True)

    corrected_full = pd.concat([df_ghi_corrected, df_dhi_corrected], axis=1)

    df_dhi_corrected.loc[(df_dhi_corrected < 0)] = 0
    df_ghi_corrected.loc[(df_ghi_corrected < 0)] = 0
    df_dni_corrected = get_dni(location=site, ghi=df_ghi_corrected, dhi=df_dhi_corrected)

    weather_dummy = weather_file.drop(['ghi', 'dhi', 'dni'], axis=1)
    weather_corrected = pd.concat([TMY_dummy, df_ghi_corrected, df_dhi_corrected, df_dni_corrected], axis=1)

    return weather_corrected