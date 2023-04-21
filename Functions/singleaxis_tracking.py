# %% True Tracking (no back-tracking, ignoring GCR)
from pvlib import solarposition, tracking
import os
import pvlib
import pandas as pd
import matplotlib.pyplot as plt

tz = 'US/Eastern'
lat, lon = 40, -80

times = pd.date_range('2019-01-01', '2019-01-02', closed='left', freq='5min',
                      tz=tz)
solpos = solarposition.get_solarposition(times, lat, lon)

truetracking_angles = tracking.singleaxis(
    apparent_zenith=solpos['apparent_zenith'],
    apparent_azimuth=solpos['azimuth'],
    axis_tilt=0,
    axis_azimuth=180,
    max_angle=90,
    backtrack=False,  # for true-tracking
    gcr=0.5)  # irrelevant for true-tracking

truetracking_position = truetracking_angles['tracker_theta'].fillna(0)
truetracking_position.plot(title='Truetracking Curve')

plt.show()

# %% Backtracking

fig, ax = plt.subplots()

for gcr in [0.2, 0.4, 0.6]:
    backtracking_angles = tracking.singleaxis(
        apparent_zenith=solpos['apparent_zenith'],
        apparent_azimuth=solpos['azimuth'],
        axis_tilt=0,
        axis_azimuth=180,
        max_angle=90,
        backtrack=True,
        gcr=gcr)

    backtracking_position = backtracking_angles['tracker_theta'].fillna(0)
    backtracking_position.plot(title='Backtracking Curve',
                               label=f'GCR:{gcr:0.01f}',
                               ax=ax)
plt.legend()
plt.show()
# %% Single axis tracking info for simulations
temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
suncable_modules = pd.read_csv(os.path.join('../Data', 'SystemData', 'bang_module_database.csv'), index_col=0,
                               skiprows=[1, 2]).T
module = suncable_modules['Jinko_JKM575M_7RL4_TV_PRE']

# Choose an inverter
# Choose ground coverage ratio (i.e., 0.4, 0.5, 0.6 etc.)


mount = pvlib.pvsystem.SingleAxisTrackerMount(axis_tilt=0, axis_azimuth=0, max_angle=90, backtrack=True, gcr=gcr,
                                              cross_axis_tilt=0, racking_model='open_rack', module_height=2)

array = pvlib.pvsystem.Array(mount=mount, module_parameters=module,
                             temperature_model_parameters=temperature_model_parameters)

system = pvlib.pvsystem.PVSystem(arrays=Arrays, inverter_parameters=inverter)


# Then run the model with the specified location and weather file:

location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)

mc = ModelChain(system, location)
mc.run_model(weather)