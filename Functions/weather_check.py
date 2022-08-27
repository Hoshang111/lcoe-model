# This script is designed to check an input weather file for errors and inconsistencies

import pandas as pd
import numpy as np
import os
import datetime as dt
import matplotlib.pyplot as plt
import pickle
import pytz
import pvanalytics as pv_an
import pvlib
import Functions.weather_functions as weather
import pvanalytics
from pvanalytics.quality.irradiance import check_irradiance_consistency_qcrad
import pathlib

#%%
SMALL_SIZE = 8
MEDIUM_SIZE = 10
BIGGER_SIZE = 12

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

#%%

data_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data"
measured_path = os.path.join(data_path, "ground_measurements_feni.csv")
measured_data_a = pd.read_csv(measured_path, index_col=0, header=1)
measured_data_a.set_index(pd.to_datetime(measured_data_a.index), inplace=True)
measured_data_a = measured_data_a.rename(columns = {'DHI_ThPyra2_Wm-2_avg':'dhi',
                                                 'GHI_ThPyra1_Wm-2_avg':'ghi',
                                                 'DNI_ThPyrh1_Wm-2_avg':'dni',
                                                 'Temp_ThPyra1_degC_avg':'temp',
                                                 'WindSpeed_Anemo1_ms_avg':'wind_speed',
                                                  'RH_ThHyg1_per100_avg':'relative_humidity'})
measured_data = measured_data_a.tz_localize("UTC")
measured_data.drop(labels=measured_data.index[0], axis=0, inplace=True)

dni_comparison_path = os.path.join(data_path, "dni_simulated_Feni.csv")
dni_comparison = pd.read_csv(dni_comparison_path, index_col=0, header=1)

#%%
weather.weather_nofit(measured_data['dni'], dni_comparison, 'dni_check')

#%% Apply pvanalytics irradiance checks

"""
QCrad Consistency for Irradiance Data
=====================================
Check consistency of GHI, DHI and DNI using QCRad criteria.
"""

# %%
# Now generate solar zenith estimates for the location,
# based on the data's time zone and site latitude-longitude
# coordinates.
latitude = 23.0159
longitude = 91.3976
solar_position = pvlib.solarposition.get_solarposition(measured_data.index,
                                                       latitude,
                                                       longitude)

# %%
# Use
# :py:func:`pvanalytics.quality.irradiance.check_irradiance_consistency_qcrad`
# to generate the QCRAD consistency mask.

qcrad_consistency_mask = check_irradiance_consistency_qcrad(
    solar_zenith=solar_position['zenith'],
    ghi=measured_data['ghi'],
    dhi=measured_data['dhi'],
    dni=measured_data['dni'])


# %%
# Plot the GHI, DHI, and DNI data streams with the QCRAD
# consistency mask overlay. This mask applies to all 3 data streams.
fig = measured_data[['ghi', 'dhi',
            'dni']].plot()
# Highlight periods where the QCRAD consistency mask is True
fig.fill_between(measured_data.index, fig.get_ylim()[0], fig.get_ylim()[1],
                 where=qcrad_consistency_mask[0], alpha=0.4)
fig.legend(labels=["GHI", "DHI", "DNI", "QCRAD Consistent"],
           loc="upper center")
plt.xlabel("Date")
plt.ylabel("Irradiance (W/m^2)")
plt.tight_layout()
save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/qcrad"
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()

# %%
# Plot the GHI, DHI, and DNI data streams with the diffuse
# ratio limit mask overlay. This mask is true when the
# DHI / GHI ratio passes the limit test.
fig = measured_data[['ghi', 'dhi',
            'dni']].plot()
# Highlight periods where the GHI ratio passes the limit test
fig.fill_between(measured_data.index, fig.get_ylim()[0], fig.get_ylim()[1],
                 where=qcrad_consistency_mask[1], alpha=0.4)
fig.legend(labels=["GHI", "DHI", "DNI",
                   "Within Diffuse Ratio Limit"],
           loc="upper center")
plt.xlabel("Date")
plt.ylabel("Irradiance (W/m^2)")
plt.tight_layout()
save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/diffuse_check"
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()

#%% now apply masks to remove invalid data
qcrad_data = measured_data.mask(~qcrad_consistency_mask[0])

#%% now plot updated distributions against initial and calculated data
