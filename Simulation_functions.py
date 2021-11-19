""" Functions for finding the DC output of the MAV or SAT system """
# import pydantic
# import pytest
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
            weather_file,
            weather_file_path=None):
    """
        weather function uploads the relevant weather variables for simulations
        Parameters
        ----------
        simulation_years: numeric
            Array of years for DC output simulations

        weather_file: str
            Name of the weather file

        weather_file_path: str
            Absolute path for the weather file if provided

        Returns
        -------
        weather_simulation : DataFrame
            Weather data to be used for simulations for the desired years.
    """
    if weather_file_path is None:
        # If no path is specified for the weather file, then download from the default weather data folder.
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        weather_data = pd.read_csv(os.path.join('Data', 'WeatherData', weather_file), index_col=0)
    else:
        weather_data = pd.read_csv(weather_file_path, index_col=0)

    weather_data.set_index(pd.to_datetime(weather_data.index), inplace=True)  # set index to datetime format (each index now
    # represents end of the hourly period: i.e. 2007-01-01 02:00:00 represents the measurements between 1-2 am

    # Change the timezone of the datetime to Australia/Darwin
    # (this may not be necessary/change timezone at the very end)
    # dummy = [str(i)[0:19] for i in weather.index]
    # weather.set_index(pd.DatetimeIndex(dummy, tz='UTC'), inplace=True)

    weather_data = weather_data.rename(columns={'Ghi': 'ghi', 'Dni': 'dni', 'Dhi': 'dhi', 'AirTemp': 'temp_air',
                                      'WindSpeed10m': 'wind_speed', 'PrecipitableWater': 'precipitable_water'})

    dummy = [weather_data[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed', 'precipitable_water']].copy()[str(sy)] for sy
             in simulation_years]  # get required PVlib weather variables for desired simulation years
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


def get_racks(DCTotal,
              num_of_zones,
              module_params,
              rack_params,
              zone_area,
              rack_interval_ratio):
    """
        get_racks function finds a range of possible numbers for racks and modules based on the parameters:

        According to info from SunCable
        Zone: 20 MW (can be MAV or SAT):
        Field: 20 zones make up a field (~400 MW)
        Solar Precinct: 36 fields make up the total array of SunCable

        Parameters
        ----------
        DCTotal: numeric
            Total DC rated power of the simulated solar farm in MW

        num_of_zones: numeric
            The number of zones that the solar farm consists of

        module_params: pandas series or dataframe
            Includes information such as modules_per_rack, rack_type, elevation, rear_shading, tilt, length, width, area

        rack_params: pandas series or dataframe
            Includes information such as modules_per_rack, rack_type, elevation, rear_shading, tilt, length, width, area

        zone_area: numeric
            The area of the zone to find the ground coverage ratio.

        rack_interval_ratio: numeric
            A ratio used to create a range of rack numbers within the zone for searching optimal NPV.
            Choose this between 0-0.3 (i.e. up to 30%)
            (No fixed size at 20 MW per zone)

        Returns
        -------
        rack_per_zone_num_range: pd.series
            A range of values for number of racks

        module_per_zone_num_range: pd.series
            A range of values for number of modules (based on the number of racks)

        gcr_range: pd.series
            A range of values for ground coverage ratio (based on the number of racks)

    """
    rack_per_zone_float = DCTotal/(num_of_zones*rack_params['Modules_per_rack']*module_params['STC']/1e6)
    rack_per_zone_init = round(rack_per_zone_float)
    rack_interval = round(rack_per_zone_float*rack_interval_ratio)
    # Rack interval needs to be equal of greater than 1
    if rack_interval < 1:
        rack_interval = 1
    rack_per_zone_num_range = pd.Series(range(rack_per_zone_init - 5 * rack_interval, rack_per_zone_init +
                                              6 * rack_interval, rack_interval))

    # Drop any negative values which may result due to inappropriate rack_interval_ratio input
    rack_per_zone_num_range.drop(rack_per_zone_num_range.index[(rack_per_zone_num_range < 0)], inplace=True)
    rack_per_zone_num_range = rack_per_zone_num_range.reindex()

    module_per_zone_num_range = rack_per_zone_num_range * rack_params['Modules_per_rack']

    # Raise an error if any of the gcr_range is more than 1.
    if rack_params['rack_type'] == 'SAT':
        gcr_range = module_params['A_c']*module_per_zone_num_range/zone_area
    elif rack_params['rack_type'] == 'east_west':
        gcr_range = []  # in east west (MAV) gcr is not relevant at this stage
    elif rack_params['rack_type'] == 'east_west_future':  # if we start taking inter-row spacing into acount for mav
                                                         # in the future
        gcr_range = rack_per_zone_num_range * rack_params['Area'] * np.cos(10 * np.pi / 180) / zone_area  # multiply by cos(10)
    else:
        raise ValueError('unrecognised rack type')

    return rack_per_zone_num_range, module_per_zone_num_range, gcr_range

def dc_yield(DCTotal,
             rack_params,
             module_params,
             temp_model,
             weather_simulation,
             rack_per_zone_num_range,
             module_per_zone_num_range,
             gcr_range,
             num_of_zones,
             num_of_mav_per_inverter=4,
             num_of_sat_per_inverter=4,
             num_of_module_per_string=30,
             num_of_strings_per_mav=4,
             num_of_strings_per_sat=4
             ):
    """ dc_yield function finds the dc output for the simulation period for the given rack, module and gcr ranges
        The model has two options rack options: 5B_MAV or SAT_1

        Parameters
        ----------
        DCTotal: numeric
            Total DC rated power of the simulated solar farm in MW

        rack_params: Dataframe
            rack parameters for the array

        module_params : Dataframe
            module parameters for the array

        temp_model : str
            temperature model for calculating module temperature: Sandia ('sapm) or PVSyst ('pvsyst')

        weather_simulation : Dataframe
            weather data to be used for simulations

        rack_per_zone_num_range: pandas series
            possible number of racks per zone

        module_per_zone_num_range: pandas series
            possible number of modules per zone

        gcr_range: pandas series
            possible number of ground coverage ratio (gcr) for the given DC size. This info is more relevant for the
            single axis tracking (SAT) simulations

        num_of_zones: Int
            number of zones withing the simulated DC farm

        num_of_mav_per_inverter: Int
            number of 5B Mavericks per inverter, currently set to 4

        num_of_sat_per_inverter: Int
            number of single axis tracker (SAT) per inverter, currently set to 4

        num_of_module_per_string: Int
            number of modules per string, currently set to 30

        num_of_strings_per_mav: Int
            number of parallel strings per mav, currently set to 4

        num_of_strings_per_sat: Int
            number of parallel strings per sat, currently set to 4

        Return
        ------
        DC_output_range: Pd series

    """
    coordinates = [(-18.7692, 133.1659, 'Suncable_Site', 00, 'Australia/Darwin')]  # Coordinates of the solar farm
    latitude, longitude, name, altitude, timezone = coordinates[0]
    location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)

    # Todo: Temperature model parameters will be modified as we have more inputs from Ruby's thesis and CFD model
    if temp_model == 'sapm':
        temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    elif temp_model == 'pvsyst':
        temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['pvsyst']['freestanding']  # other option
    else:
        raise ValueError ('Please choose temperature model as Sandia: or PVSyst')

    if rack_params['rack_type'] == 'east_west':
        ''' DC modelling for 5B Mavericks with fixed ground mounting in east-west direction  '''

        # Inverter (this part finds an inverter from the CEC list that matches the DC output of the system)
        num_of_mod_per_inverter = num_of_mav_per_inverter * rack_params['Modules_per_rack']
        # in kW rated DC power output per inverter
        dc_rated_power = module_params['STC'] / 1000 * num_of_mod_per_inverter

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
            inverter_params = inverter_candidates.iloc[0]  # Choose an inverter from the list of candidates

        module_tilt = rack_params['tilt']
        mount1 = pvsystem.FixedMount(surface_tilt=module_tilt, surface_azimuth=90)  # east facing array
        mount2 = pvsystem.FixedMount(surface_tilt=module_tilt, surface_azimuth=270)  # west facing array

        # Define two arrays resembling Maverick design: one east facing & one west facing
        # For now we are designing at the inverter level with 4 MAVs per inverter. Half of the array is assigned with
        # mount 1 (east facing) and the other half is assigned with mount 2 (west facing)
        array_one = pvsystem.Array(mount=mount1,
                                   module_parameters=module_params,
                                   temperature_model_parameters=temperature_model_parameters,
                                   modules_per_string=num_of_module_per_string,
                                   strings=num_of_strings_per_mav * num_of_mav_per_inverter / 2)

        array_two = pvsystem.Array(mount=mount2,
                                   module_parameters=module_params,
                                   temperature_model_parameters=temperature_model_parameters,
                                   modules_per_string=num_of_module_per_string,
                                   strings=num_of_strings_per_mav * num_of_mav_per_inverter / 2)

        inverter_mav_system = PVSystem(arrays=[array_one, array_two], inverter_parameters=inverter_params)

        # Model-Chain
        # Todo: We can try different angle of irradiance (aoi) models down the track
        mc = ModelChain(inverter_mav_system, location, aoi_model='ashrae')
        # mc = ModelChain(system, location, aoi_model='sapm')  # another aoi model which could be explored...

        mc.run_model(weather_simulation)
        total_module_number = round(DCTotal/(module_params['STC'] / 1e6))
        # Find the total DC output for the given DC size/total module number
        # If you want to find the per zone output, find multiplication coefficient based on number of modules per zone
        multiplication_coeff = total_module_number/num_of_mod_per_inverter
        dc_results = (mc.results.dc[0]['p_mp'] + mc.results.dc[1]['p_mp']) * multiplication_coeff
        dc_size = total_module_number * module_params['STC'] / 1e6  # dc_size in MW

        # Converting MAV DC results to fit SAT results according to module_per_zone_num_range
        dc_results_range = [dc_results.values/total_module_number * m * num_of_zones for m in module_per_zone_num_range]
        dc_df = pd.DataFrame(dc_results_range).T
        dc_df.columns = rack_per_zone_num_range
        dc_df.index = dc_results.index


    elif rack_params['rack_type'] == 'SAT':
        ''' DC modelling for single axis tracking (SAT) system '''

        # Inverter (this part finds an inverter from the CEC list that matches the DC output of the system)
        # Todo: Currently number of SAT per inverter is set to 4. Get more info from SunCable...
        # Todo: If these parts are essentially same for MAV and SAT move this code prior to the IF for mounting type
        num_of_mod_per_inverter = num_of_sat_per_inverter * rack_params['Modules_per_rack']
        dc_rated_power = module_params['STC'] / 1000 * num_of_mod_per_inverter  # in kW rated DC power output per inverter
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
            inverter_params = inverter_candidates.iloc[0]  # Choose an inverter from the list of candidates

        dc_results = []
        dc_size = []
        for gcr, module_num in zip(gcr_range, module_per_zone_num_range):
            mount = pvsystem.SingleAxisTrackerMount(axis_tilt=0, axis_azimuth=0, max_angle=90, backtrack=True,
                                                    gcr=gcr, cross_axis_tilt=0, racking_model='open_rack',
                                                    module_height=2)

            sat_array = pvsystem.Array(mount=mount,
                                       module_parameters=module_params,
                                       temperature_model_parameters=temperature_model_parameters,
                                       modules_per_string=num_of_module_per_string,
                                       strings=num_of_strings_per_sat * num_of_sat_per_inverter)

            inverter_sat_system = pvsystem.PVSystem(arrays=[sat_array], inverter_parameters=inverter_params)

            mc = ModelChain(inverter_sat_system, location)
            mc.run_model(weather_simulation)
            multiplication_coeff = module_num / num_of_mod_per_inverter
            dc_results.append(mc.results.dc['p_mp'] * multiplication_coeff)
            dc_size.append(module_num * num_of_zones * module_params['STC'] / 1e6)
        # Todo: we can try different back-tracking algorithms for SAT as well
        dc_df = pd.DataFrame(dc_results).T
        dc_df.columns = rack_per_zone_num_range
    else:
        raise ValueError("Please choose racking as one of these options: 5B_MAV or SAT_1")

    return dc_results, dc_df, dc_size

    # Todo: The model calculates according to UTC so we will need to modify the time-stamp to Darwin...



