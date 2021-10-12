""" Functions for finding the DC output of the MAV or SAT system """

import pandas as pd
import numpy as np
import os
from pvlib import pvsystem
from pvlib.pvsystem import PVSystem, FixedMount
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS


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
            Type of rack to be used in solar farm. Two options: '5B_MAV' or 'SAT_1'

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
             num_of_mod_per_string=30,
             num_of_strings_per_mav=4,
             num_of_mod_per_mav=120):
    """ dc_yield function finds the dc output of the array for the simulation period
        The model has two options: 5B_MAV or SAT_1

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

        num_of_mod_per_string: Int
            number of modules per string, currently set to 30

        num_of_strings_per_mav: Int
            number of parallel strings per mav, currently set to 4

        num_of_mod_per_mav: Int
            number of modules per 5B Mavericks, currently set to 30 * 4 = 120

        Return
        ------

    """
    coordinates = [(-18.7692, 133.1659, 'Suncable_Site', 00, 'Australia/Darwin')]  # Coordinates of the solar farm
    # Todo :
    if rack_params.name == '5B_MAV':
        ''' DC modelling for 5B Mavericks '''

        # Inverter (this part finds an inverter from the CEC list that matches the DC output of the system)
        num_of_mod_per_inverter = num_of_mav_per_inv * num_of_mod_per_mav  # 480 modules per inverter
        dc_rated_power = module_params['STC'] / 1000 * num_of_mod_per_inverter  # in kW rated DC power output
        dc_to_ac = 1.2
        ac_rated_power = dc_rated_power / dc_to_ac  # in kW rated AC power output
        inverter_list = pvsystem.retrieve_sam('cecinverter')

        # Find inverter candidates by narrowing down the options. Assume 5% tolerance for now for the DC ratings...
        inv_dc_idx = (inverter_list.loc['Pdco'] >= dc_rated_power * 1000 * 0.95) & \
                     (inverter_list.loc['Pdco'] <= dc_rated_power * 1000 * 1.05)

        inverter_candidates = inverter_list.T[inv_dc_idx]
        # If no inverters match the criteria, choose a micro-inverter. If there are candidates choose one of them.
        if inverter_candidates is None:
            inverter_params = inverter_candidates['ABB__MICRO_0_25_I_OUTD_US_208__208V_']
        else:
            inverter_params = inverter_candidates.iloc['Sungrow_Power_Supply_Co___Ltd___SC250KU__480V_']

        #  Mounting
        module_tilt = rack_params['tilt']
        mount1 = pvsystem.FixedMount(surface_tilt=module_tilt, surface_azimuth=90)  # east facing array
        mount2 = pvsystem.FixedMount(surface_tilt=module_tilt, surface_azimuth=270)  # west facing array

        # Todo: Temperature model parameters will be modified as we have more inputs from Ruby's thesis and CFD model
        temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']

        # Define two arrays resembling Maverick design: one east facing & one west facing
        # For now we are designing at the inverter level with 4 MAVs per inverter
        array_one = pvsystem.Array(mount=mount1,
                                   module_parameters=module_params,
                                   temperature_model_parameters=temperature_model_parameters,
                                   modules_per_string=num_of_mod_per_string,
                                   strings=num_of_strings_per_mav * num_of_mav_per_inv / 2)

        array_two = pvsystem.Array(mount=mount2,
                                   module_parameters=module_params,
                                   temperature_model_parameters=temperature_model_parameters,
                                   modules_per_string=num_of_mod_per_string,
                                   strings=num_of_strings_per_mav * num_of_mav_per_inv / 2)

        mav_system = PVSystem(arrays=[array_one, array_two], inverter_parameters=inverter_params)

        # Model-Chain
        latitude, longitude, name, altitude, timezone = coordinates[0]
        location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)

        # Todo: We can try different angle of irradiance (aoi) models down the track
        mc = ModelChain(mav_system, location, aoi_model='ashrae')
        # mc = ModelChain(system, location, aoi_model='sapm')  # another aoi model which could be explored...

        mc.run_model(weather_simulation)
        # The model calculates according to UTC so we will need to modify the time-stamp to Darwin...


    elif rack_params.name == 'SAT_1':
        ''' DC modelling for SATs '''
        print('dcg')




    else:
        raise ValueError("Please choose racking as one of these options: 5B_MAV or SAT_1")




    # num_of_inv_per_zone = np.ceil(zone_rated_power / (module['STC'] / 1000 * num_of_mod_per_inverter))  # TODO: This is an
    # important assumption to check (i.e., ceil of floor)...
    # ac_yield  # (optional at this stage)
    # optional inputs: temp/rack coeff, back-tracking algo, aoi model
