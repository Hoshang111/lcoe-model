import pandas as pd
from pvlib.location import Location
import pvlib.bifacial as bifacial
from pvlib.tracking import singleaxis

# %% Download Solcast Weather file
#weather_file = 'Solcast_PT60M.csv'
#simulation_years = np.arange(2007, 2022, 1)
#weather_solcast = func.weather(simulation_years, weather_file)
#weather_solcast.set_index(weather_solcast.index.tz_convert('Australia/Darwin'), inplace=True, drop=True)

# Location
coordinates = [(-18.7692, 133.1659, 'Suncable_Site', 00, 'Australia/Darwin')]  # Coordinates of the solar farm
latitude, longitude, name, altitude, timezone = coordinates[0]
location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)

# Choose an example year
weather_data = weather_simulation_dnv['2018']
solar_position = Location.get_solarposition(location, weather_data.index, weather_data['temp_air'])

solar_azimuth = solar_position['azimuth']
solar_zenith = solar_position['apparent_zenith']

# single axis tracking information
tracking_output = singleaxis(solar_zenith, solar_azimuth, axis_tilt=0, axis_azimuth=0, max_angle=60, backtrack=True, gcr=0.3, cross_axis_tilt=0)
# %%
surface_azimuth = tracking_output['surface_azimuth']
surface_tilt = tracking_output['tracker_theta']
axis_azimuth = 0
timestamps = solar_position.index
dni = weather_data['dni']
dhi = weather_data['dhi']
gcr = 0.33
pvrow_height = 1.5
pvrow_width = 1.2
albedo = 0.25
n_pvrows = 3
index_observed_pvrow = 1
rho_front_pvrow = 0.03
rho_back_pvrow = 0.05
horizon_band_angle = 15

bifacial_output = bifacial.pvfactors_timeseries(solar_azimuth, solar_zenith, surface_azimuth, surface_tilt,
                              axis_azimuth, timestamps, dni, dhi, gcr, pvrow_height, pvrow_width, albedo)
bifacial_output = pd.DataFrame(bifacial_output).T

bifacial_output['effective_irradiance'] = bifacial_output['total_abs_front'] + bifacial_output['total_abs_back'] * module_params['Bifacial']
bifacial_output.fillna(0, inplace=True)

# Extract cell temperature from mc.run_model simulations and input into bifacial_output
# (Run the normal mc script first)

cell_temp_normal = mc.results.cell_temperature['2018']
bifacial_output['cell_temperature'] = cell_temp_normal.values
