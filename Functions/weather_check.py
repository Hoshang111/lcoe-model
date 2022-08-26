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

# %% Plot features
font_size = 25
rc = {'font.size': font_size, 'axes.labelsize': font_size, 'legend.fontsize': font_size,
      'axes.titlesize': font_size, 'xtick.labelsize': font_size, 'ytick.labelsize': font_size}
plt.rcParams.update(**rc)
plt.rc('font', weight='bold')
# For label titles
fontdict = {'fontsize': font_size, 'fontweight': 'bold'}

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

dni_comparison_path = os.path.join(data_path, "dni_simulated_Feni.csv")
dni_comparison = pd.read_csv(dni_comparison_path, index_col=0, header=1)

#%%
weather.weather_nofit(measured_data['dni'], dni_comparison, 'dni_check')


