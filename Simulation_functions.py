""" Functions for finding the DC output of the MAV or SAT system """

import pandas as pd
import numpy as np
import os


os.chdir(os.path.dirname(os.path.abspath(__file__))) # Change the directory to the current folder

def weather(simulation_years,
            weather_file_path=None):
    """
        weather function uploads the relevant weather variables for simulations
        Parameters
        ----------
        weather_file_path: str
            Absolute path for the weather file if provided

        simulation_years: numeric
            Array of years for DC output simulations

        Returns
        -------
        weather_simulation : DataFrame
            Weather data to be used for simulations for the desired years.
    """

    if weather_file_path is None:
        # If no path is specified for the weather file, then download from the default weather data folder.
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        weather = pd.read_csv(os.path.join('Data', 'WeatherData', 'Solcast_PT60M.csv'), index_col=0)
    else:
        weather = pd.read_csv(weather_file_path, index_col=0)

    weather.set_index(pd.to_datetime(weather.index), inplace=True)  # set index to datetime format (each index now
    # represents end of the hourly period: i.e. 2007-01-01 02:00:00 represents the measurements between 1-2 am

    # Change the timezone of the datetime to Australia/Darwin
    # (this may not be necessary/change timezone at the very end)
    # dummy = [str(i)[0:19] for i in weather.index]
    # weather.set_index(pd.DatetimeIndex(dummy, tz='UTC'), inplace=True)

    weather = weather.rename(columns={'Ghi': 'ghi', 'Dni': 'dni', 'Dhi': 'dhi', 'AirTemp': 'temp_air',
                                      'WindSpeed10m': 'wind_speed', 'PrecipitableWater': 'precipitable_water'})

    dummy = [weather[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed', 'precipitable_water']].copy()[str(sy)] for sy in
             simulation_years]  # get required PVlib weather variables for desired simulation years
    weather_simulation = pd.concat(dummy)
    weather_simulation['precipitable_water'] = weather_simulation[
                                                   'precipitable_water'] / 10  # formatting for PV-lib

    return weather_simulation


def rack_module_params(rack_type,
                       module_type):
    """
        rack_module_params function extracts the relevant rack and module variables for simulations

        Parameters
        ----------
        rack_type: str
            Type of rack to be used in solar farm

        module_type: str
            Type of module to be used in solar farm

        Returns
        -------
        rack_params, module_params : Dataframe
            Rack and module parameters to be used in PVlib simulations
    """
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Change the directory to the current folder
    suncable_racks = pd.read_csv(os.path.join('Data', 'SystemData', 'Suncable_rack_database.csv'), index_col=0,
                                 skiprows=[1]).T
    suncable_modules = pd.read_csv(os.path.join('Data', 'SystemData', 'Suncable_module_database.csv'), index_col=0,
                                   skiprows=[1, 2]).T

    rack_params = suncable_racks[rack_type]
    module_params = suncable_modules[module_type]

    return rack_params, module_params


def dc_yield(rack_params,
             module_params,
             weather_simulation,
             gcr,
             zone_rated_power=2000,
             num_of_mav_per_inv=4,
             num_mod_per_string=30,
             num_of_strings_per_mav=4,
             num_of_mod_per_mav=120):
    """ dc_yield function finds the dc output of the array for the simulation period

        Parameters
        ----------
        rack_params: Dataframe
            rack parameters for the array

        module_params : Dataframe
            module parameters for the array

        weather_simulation : Dataframe
            weather data to be used for simulations

        gcr: Int/List
            ground coverage ratio used for single axis tracking simulations

        zone_rated_power: Int
            the rater power of the SunCable zone, currently set to 2000 kW (20 MW)

        num_of_mav_per_inv: Int
            number of 5B Mavericks per inverter, currently set to 4

        num_mod_per_string: Int
            number of modules per string, currently set to 30

        num_of_strings_per_mav: Int
            number of parallel strings per mav, currently set to 4

        num_of_mod_per_mav: Int
            number of modules per 5B Mavericks, currently set to 30 * 4 = 120

        Return
        ------

    """
    coordinates = [(-18.7692, 133.1659, 'Suncable_Site', 00, 'Australia/Darwin')]  # Coordinates of the solar farm

    num_of_mod_per_inverter = num_of_mav_per_inv * num_of_mod_per_mav  # 480 modules per inverter
    # num_of_inv_per_zone = np.ceil(zone_rated_power / (module['STC'] / 1000 * num_of_mod_per_inverter))  # TODO: This is an
    # important assumption to check (i.e., ceil of floor)...


# optional inputs: temp/rack coeff, back-tracking algo, aoi model
