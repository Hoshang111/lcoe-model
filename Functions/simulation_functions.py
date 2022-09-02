""" Functions for finding the DC output of the MAV or SAT system """
# import pydantic
# import pytest
from platform import python_branch
import pandas as pd
import numpy as np
import os
from pvlib import pvsystem as pvsys
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
import Bifacial.bifacial_pvsystem as bifacial_pvsystem
import Bifacial.bifacial_modelchain as bifacial_modelchain
import Bifacial.bifacial_modelchain_dc as dc_modelchain
import pvlib.bifacial as bifacial
from pvlib.tracking import singleaxis

import ast

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
        weather_data = pd.read_csv(os.path.join('../Data', 'WeatherData', weather_file), index_col=0)
    else:
        weather_data = pd.read_csv(weather_file_path, index_col=0)

    weather_data.set_index(pd.to_datetime(weather_data.index), inplace=True)  # set index to datetime format (each index now
    # represents end of the hourly period: i.e. 2007-01-01 02:00:00 represents the measurements between 1-2 am


    weather_data = weather_data.rename(columns={'Ghi': 'ghi', 'Dni': 'dni', 'Dhi': 'dhi', 'AirTemp': 'temp_air',
                                      'WindSpeed10m': 'wind_speed', 'PrecipitableWater': 'precipitable_water',
                                                'Ebh': 'bhi'})

    dummy = [weather_data[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed', 'precipitable_water', 'bhi']].copy().loc[str(sy)]
             for sy in simulation_years]  # get required PVlib weather variables for desired simulation years
    weather_simulation = pd.concat(dummy)
    weather_simulation['precipitable_water'] = weather_simulation['precipitable_water'] / 10  # formatting for PV-lib
    weather_simulation['cos_theta'] = weather_simulation['bhi']/weather_simulation['dni']
    weather_simulation['cos_theta'] = weather_simulation['cos_theta'].fillna(0)
    weather_simulation.sort_index(inplace=True)
    return weather_simulation


def weather_benchmark_adjustment(weather_solcast,
                                 weather_dnv_file,
                                 weather_dnv_path=None):
    ''' This is the weather adjustment function which uses Solcast's DNI data
        Refer to the other benchmark function which uses simulated DNI'''
    if weather_dnv_path is None:
        # If no path is specified for the dnv weather file, then download from the default weather data folder.
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        weather_dnv_dummy = pd.read_csv(os.path.join('../Data', 'WeatherData', weather_dnv_file),
                                        delimiter=';',
                                        index_col=0)
    else:
        weather_dnv_dummy = pd.read_csv(weather_dnv_path, index_col=0)


    weather_dnv_dummy = weather_dnv_dummy.rename(
        columns={'GlobHor': 'ghi', 'DiffHor': 'dhi', 'BeamHor': 'bhi', 'T_Amb': 'temp_air',
                 'WindVel': 'wind_speed', 'EArray': 'dc_yield'})

    weather_dnv = weather_dnv_dummy[['ghi', 'dhi', 'bhi', 'temp_air', 'wind_speed', 'dc_yield']].copy()
    weather_dnv.set_index(pd.to_datetime(weather_dnv.index, utc=False), inplace=True)
    weather_dnv.sort_index(inplace=True)

    # The weather dnv data doesn't have the precipitable water and cos_theta which is needed for the simulations
    # This data can be extracted from the SolCast weather data.
    # To match the dates, i am using floor function on Solcast date time so to convert  11:30 am to 11:00 for example
    # the reason for using floor is the end timestamp of each measurement is used as the index so far
    # according to the first column of the original weather data
    new_index = [str(i)[0:19] for i in weather_solcast.index.floor('H')]
    weather_solcast.set_index(pd.to_datetime(new_index, utc=False), inplace=True)

    weather_dnv = weather_dnv.join(weather_solcast[['precipitable_water', 'cos_theta']])
    #weather_dnv['cos_theta'] = weather_dnv['cos_theta'].shift(-1)  # for some reason it is much better aligned this way
    weather_dnv['dni'] = weather_dnv['bhi'] / weather_dnv['cos_theta']  # conversion from bhi to dni with cos theta
    weather_dnv['dni'] = weather_dnv['dni'].fillna(0)
    weather_dnv['dni'].replace(np.inf, 0, inplace=True)
    weather_dnv_simulations = weather_dnv[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed', 'precipitable_water', 'dc_yield']]
    weather_dnv.sort_index(inplace=True)
    return weather_dnv_simulations

def weather_benchmark_adjustment_mk2(weather_solcast,
                                 weather_dnv_file,
                                 weather_dnv_path=None):

    if weather_dnv_path is None:
        # If no path is specified for the dnv weather file, then download from the default weather data folder.
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        weather_dnv_dummy = pd.read_csv(os.path.join('../Data', 'WeatherData', weather_dnv_file),
                                        delimiter=';',
                                        index_col=0)
    else:
        weather_dnv_dummy = pd.read_csv(weather_dnv_path, index_col=0)


    weather_dnv_dummy = weather_dnv_dummy.rename(
        columns={'GlobHor': 'ghi', 'DiffHor': 'dhi', 'BeamHor': 'bhi', 'T_Amb': 'temp_air',
                 'WindVel': 'wind_speed', 'EArray': 'dc_yield'})

    weather_dnv = weather_dnv_dummy[['ghi', 'dhi', 'bhi', 'temp_air', 'wind_speed', 'dc_yield']].copy()
    weather_dnv.set_index(pd.to_datetime(weather_dnv.index, utc=False), inplace=True)
    weather_dnv.sort_index(inplace=True)

    # The weather dnv data doesn't have the precipitable water and cos_theta which is needed for the simulations
    # This data can be extracted from the SolCast weather data.
    # To match the dates, i am using floor function on Solcast date time so to convert  11:30 am to 11:00 for example
    # the reason for using floor is the end timestamp of each measurement is used as the index so far
    # according to the first column of the original weather data
    weather_solcast_mod = weather_solcast.set_index(weather_dnv.index)

    weather_dnv = weather_dnv.join(weather_solcast_mod[['precipitable_water', 'cos_theta']])
    #weather_dnv['cos_theta'] = weather_dnv['cos_theta'].shift(-1)  # for some reason it is much better aligned this way
    weather_dnv['dni'] = weather_dnv['bhi'] / weather_dnv['cos_theta']  # conversion from bhi to dni with cos theta
    weather_dnv['dni'] = weather_dnv['dni'].fillna(0)
    weather_dnv['dni'].replace(np.inf, 0, inplace=True)
    weather_dnv_simulations = weather_dnv[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed', 'precipitable_water', 'dc_yield']]
    weather_dnv.sort_index(inplace=True)
    return weather_dnv_simulations

def weather_sort(weather_file):
    """

    :param weather_file:
    :return:
    """

    weather_monthly = weather_file.groupby(weather_file.index.month)
    weather_list = [group for _, group in weather_monthly]
    months_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    weather = {}

    for i in range(len(months_list)):
        weather[months_list[i]] = {}
        unsorted_data = weather_list[i]
        split_data = unsorted_data.groupby(unsorted_data.index.year)
        unsorted_list = [group for _, group in split_data]
        sorted_list = sorted(unsorted_list, key=lambda x: x['ghi'].sum())
        for j in range(len(sorted_list)):
            weather[months_list[i]][j] = sorted_list[j]

    return weather

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
    # Note that for the cost_components columns, the text needs to be converted into a list of tuples. ast.literal_eval does this.
    suncable_racks = pd.read_csv(os.path.join('../Data', 'SystemData', 'Suncable_rack_database.csv'), index_col=0,
                                 skiprows=[1], converters={"cost_components": lambda x: ast.literal_eval(str(x))}).T

    suncable_modules = pd.read_csv(os.path.join('../Data', 'SystemData', 'Suncable_module_database.csv'), index_col=0,
                                   skiprows=[1, 2], converters={"cost_components": lambda x: ast.literal_eval(str(x))}).T



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
        gcr_range = rack_per_zone_num_range * rack_params['Area'] * np.cos(10 * np.pi / 180) / zone_area  # edited to have values as mucks up later graphs
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
        dc_results: List
            time series (Wh) of DC yield per zone for the studied TMYs according to the range of number of racks per zone
        dc_df: Pandas DataFrame
            dataframe (Wh) of dc_results with columns matched to the range of number of racks per zone
        dc_size: Pandas series
            dc rated power (MW) of the solar farm according to range of number of racks per zone

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
        raise ValueError('Please choose temperature model as Sandia: or PVSyst')

    if rack_params['rack_type'] == 'east_west':
        ''' DC modelling for 5B Mavericks with fixed ground mounting in east-west direction  '''

        # Inverter (this part finds an inverter from the CEC list that matches the DC output of the system)
        num_of_mod_per_inverter = num_of_mav_per_inverter * rack_params['Modules_per_rack']
        # in kW rated DC power output per inverter
        dc_rated_power = module_params['STC'] / 1000 * num_of_mod_per_inverter

        dc_to_ac = 1.2
        ac_rated_power = dc_rated_power / dc_to_ac  # in kW rated AC power output
        inverter_list = pvsys.retrieve_sam('cecinverter')

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
        mount1 = pvsys.FixedMount(surface_tilt=module_tilt, surface_azimuth=90)  # east facing array
        mount2 = pvsys.FixedMount(surface_tilt=module_tilt, surface_azimuth=270)  # west facing array

        # Define two arrays resembling Maverick design: one east facing & one west facing
        # For now we are designing at the inverter level with 4 MAVs per inverter. Half of the array is assigned with
        # mount 1 (east facing) and the other half is assigned with mount 2 (west facing)
        array_one = pvsys.Array(mount=mount1,
                                   module_parameters=module_params,
                                   temperature_model_parameters=temperature_model_parameters,
                                   modules_per_string=num_of_module_per_string,
                                   strings=num_of_strings_per_mav * num_of_mav_per_inverter / 2)

        array_two = pvsys.Array(mount=mount2,
                                   module_parameters=module_params,
                                   temperature_model_parameters=temperature_model_parameters,
                                   modules_per_string=num_of_module_per_string,
                                   strings=num_of_strings_per_mav * num_of_mav_per_inverter / 2)

        inverter_mav_system = pvsys.PVSystem(arrays=[array_one, array_two], inverter_parameters=inverter_params)

        # Model-Chain
        # Todo: We can try different angle of irradiance (aoi) models down the track
        mc = ModelChain(inverter_mav_system, location, aoi_model='ashrae')
        # mc = ModelChain(system, location, aoi_model='sapm')  # another aoi model which could be explored...

        mc.run_model(weather_simulation)
        total_module_number = round(DCTotal/(module_params['STC'] / 1e6))
        # Find the total DC output for the given DC size/total module number
        # If you want to find the per zone output, find multiplication coefficient based on number of modules per zone
        multiplication_coeff = total_module_number/num_of_mod_per_inverter
        dc_results_total = (mc.results.dc[0]['p_mp'] + mc.results.dc[1]['p_mp']) * multiplication_coeff
        # dc_results is the DC yield of the total solar farm

        dc_size = module_per_zone_num_range * module_params['STC'] / 1e6 * num_of_zones  # dc_size in MW

        # Converting MAV DC results to match SAT results according SAT's module_per_zone_num_range
        dc_results = [dc_results_total.values/total_module_number * m for m in module_per_zone_num_range]
        dc_df = pd.DataFrame(dc_results).T
        dc_df.columns = rack_per_zone_num_range
        dc_df.index = dc_results_total.index

    elif rack_params['rack_type'] == 'SAT':
        ''' DC modelling for single axis tracking (SAT) system '''

        # Inverter (this part finds an inverter from the CEC list that matches the DC output of the system)
        # Todo: Currently number of SAT per inverter is set to 4. Get more info from SunCable...
        # Todo: If these parts are essentially same for MAV and SAT move this code prior to the IF for mounting type
        num_of_mod_per_inverter = num_of_sat_per_inverter * rack_params['Modules_per_rack']
        dc_rated_power = module_params['STC'] / 1000 * num_of_mod_per_inverter  # in kW rated DC power output per inverter
        dc_to_ac = 1.2
        ac_rated_power = dc_rated_power / dc_to_ac  # in kW rated AC power output
        inverter_list = pvsys.retrieve_sam('cecinverter')

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
            if module_params['Bifacial'] > 0:
                mount = bifacial_pvsystem.SingleAxisTrackerMount(axis_tilt=0, axis_azimuth=0, max_angle=60,
                                                                 backtrack=True,
                                                                 gcr=gcr, cross_axis_tilt=0,
                                                                 racking_model='open_rack',
                                                                 module_height=rack_params['elevation'])

                sat_array = bifacial_pvsystem.Array(mount=mount,
                                                    module_parameters=module_params,
                                                    temperature_model_parameters=temperature_model_parameters,
                                                    modules_per_string=num_of_module_per_string,
                                                    strings=num_of_strings_per_sat * num_of_sat_per_inverter)

                inverter_sat_system = bifacial_pvsystem.PVSystem(arrays=[sat_array],
                                                                 inverter_parameters=inverter_params)
                mc = bifacial_modelchain.ModelChain(inverter_sat_system, location)
                mc.run_model_bifacial(weather_simulation)
                multiplication_coeff = module_num / num_of_mod_per_inverter
                dc_results.append(mc.results.dc['p_mp'] * multiplication_coeff)
                dc_size.append(module_num * num_of_zones * module_params['STC'] / 1e6)

            else:
                mount = pvsys.SingleAxisTrackerMount(axis_tilt=0, axis_azimuth=0, max_angle=60, backtrack=True,
                                                     gcr=gcr, cross_axis_tilt=0, racking_model='open_rack',
                                                     module_height=rack_params['elevation'])

                sat_array = pvsys.Array(mount=mount,
                                        module_parameters=module_params,
                                        temperature_model_parameters=temperature_model_parameters,
                                        modules_per_string=num_of_module_per_string,
                                        strings=num_of_strings_per_sat * num_of_sat_per_inverter)

                inverter_sat_system = pvsys.PVSystem(arrays=[sat_array], inverter_parameters=inverter_params)
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

    # Change the time-stamp from UTC to Australia/Darwin
    # dc_df.index = dc_df.index.tz_convert('Australia/Darwin')
    return dc_results, dc_df, dc_size


def dc_yield_benchmarking_mav(DCTotal,
                           rack_params,
                           module_params,
                           temp_model,
                           weather_simulation,
                           module_rating,
                           num_of_zones=167,
                           num_of_inv_per_zone=2,
                           num_of_module_per_string=26):

    coordinates = [(-18.7692, 133.1659, 'Suncable_Site', 00, 'Australia/Darwin')]  # Coordinates of the solar farm
    latitude, longitude, name, altitude, timezone = coordinates[0]
    location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)

    if temp_model == 'sapm':
        temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    elif temp_model == 'pvsyst':
        temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['pvsyst']['freestanding']  # other option
    else:
        raise ValueError('Please choose temperature model as Sandia: or PVSyst')

    ''' DC modelling for 5B Mavericks with fixed ground mounting in east-west direction  '''
    # Choose inverter as SMA SC 3000
    inverter_list = pvsys.retrieve_sam('cecinverter')
    filter_col = [col for col in inverter_list if col.startswith('SMA')]
    inverter_list_sma = inverter_list[filter_col]
    # It doesn't have the exact inverter so enter the chosen SMA inverter parameters manually
    inverter_params = pd.Series({'Vac':655, 'Pso':12000, 'Paco':2850000, 'Pdco':2900000, 'Vdco':1077,
                                'C0': -0.0,'C1':0.0001, 'C2':0.000911, 'C3':0.000215,
                                'Pnt':2000, 'Vdcmax':1500, 'Idcmax':3200, 'Mppt_low':856, 'Mppt_high':1425,
                                'CEC_Date':'2/15/2019', 'CEC_Type': 'Grid Support'}, name='SMA SC 3000-EV')
    # 'https://www.enfsolar.com/pv/inverter-datasheet/11765' and other SMA data sheets

    if module_rating == 545:
        num_of_strings_per_inverter = 212
    else:
        num_of_strings_per_inverter = 204

    num_of_module_per_inverter = num_of_strings_per_inverter * num_of_module_per_string

    module_tilt = rack_params['tilt']
    mount1 = pvsys.FixedMount(surface_tilt=module_tilt, surface_azimuth=90)  # east facing array
    mount2 = pvsys.FixedMount(surface_tilt=module_tilt, surface_azimuth=270)  # west facing array

    # Define two arrays resembling Maverick design: one east facing & one west facing
    # DC yield of one inverter
    array_one = pvsys.Array(mount=mount1,
                               module_parameters=module_params,
                               temperature_model_parameters=temperature_model_parameters,
                               modules_per_string=num_of_module_per_string,
                               strings=num_of_strings_per_inverter / 2)

    array_two = pvsys.Array(mount=mount2,
                               module_parameters=module_params,
                               temperature_model_parameters=temperature_model_parameters,
                               modules_per_string=num_of_module_per_string,
                               strings=num_of_strings_per_inverter / 2)

    inverter_array = pvsys.PVSystem(arrays=[array_one, array_two], inverter_parameters=inverter_params)

    # Model-Chain
    # Todo: We can try different angle of irradiance (aoi) models down the track
    mc = ModelChain(inverter_array, location, aoi_model='ashrae')
    # mc = ModelChain(system, location, aoi_model='sapm')  # another aoi model which could be explored...
    mc.run_model(weather_simulation)

    # in kW rated DC power output per inverter
    dc_rated_power_inv = module_params['STC'] / 1000 * num_of_module_per_inverter

    # Find the total DC output for the given DC size/total module number
    # If you want to find the per zone output, find multiplication coefficient based on number of modules per zone
    multiplication_coeff = num_of_zones * num_of_inv_per_zone
    dc_results_total = (mc.results.dc[0]['p_mp'] + mc.results.dc[1]['p_mp']) * multiplication_coeff
    # dc_results is the DC yield of the total solar farm
    return dc_results_total, mc


def dc_yield_benchmarking_sat(DCTotal,
                           rack_params,
                           module_params,
                           temp_model,
                           weather_simulation,
                           module_rating,
                           gcr,
                           cell_type,
                           num_of_zones=167,
                           num_of_inv_per_zone=2,
                           num_of_module_per_string=26):
    coordinates = [(-18.7692, 133.1659, 'Suncable_Site', 00, 'Australia/Darwin')]  # Coordinates of the solar farm
    latitude, longitude, name, altitude, timezone = coordinates[0]
    location = Location(latitude, longitude, name=name, altitude=altitude, tz=timezone)

    if temp_model == 'sapm':
        temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    elif temp_model == 'pvsyst':
        temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['pvsyst']['freestanding']  # other option
    else:
        raise ValueError('Please choose temperature model as Sandia: or PVSyst')

    # if cell_type == 'bifacial':
        # Choose an example year
    #    solar_position = Location.get_solarposition(location, weather_simulation.index,
    #                                                weather_simulation['temp_air'])
    #    solar_azimuth = solar_position['azimuth']
    #    solar_zenith = solar_position['apparent_zenith']
        # single axis tracking information
    #    tracking_output = singleaxis(solar_zenith, solar_azimuth, axis_tilt=0, axis_azimuth=0, max_angle=60,
    #                                 backtrack=True,
    #                                 gcr=0.3, cross_axis_tilt=0)
    #    surface_azimuth = tracking_output['surface_azimuth']
    #    surface_tilt = tracking_output['tracker_theta']
    #    axis_azimuth = 0
    #    timestamps = solar_position.index
    #    dni = weather_simulation['dni']
    #    dhi = weather_simulation['dhi']
    #    pvrow_height = 1.5
    #    pvrow_width = 1.2
    #    albedo = 0.25
    #    n_pvrows = 3
    #    index_observed_pvrow = 1
    #    rho_front_pvrow = 0.03
    #    rho_back_pvrow = 0.05
    #    horizon_band_angle = 15
    #    bifacial_output = bifacial.pvfactors_timeseries(solar_azimuth, solar_zenith, surface_azimuth, surface_tilt,
    #                                                axis_azimuth, timestamps, dni, dhi, gcr, pvrow_height, pvrow_width,
    #                                                albedo)
    #    bifacial_output = pd.DataFrame(bifacial_output).T

    #    bifacial_output['effective_irradiance'] = bifacial_output['total_abs_front'] + bifacial_output['total_abs_back'] * \
    #                                          module_params['Bifacial']
    #    bifacial_output.fillna(0, inplace=True)

    ''' DC modelling for single axis tracking (SAT) system '''
    # Choose inverter as SMA SC 3000
    inverter_list = pvsys.retrieve_sam('cecinverter')
    filter_col = [col for col in inverter_list if col.startswith('SMA')]
    inverter_list_sma = inverter_list[filter_col]
    # It doesn't have the exact inverter so enter the chosen SMA inverter parameters manually
    inverter_params = pd.Series({'Vac':655, 'Pso':12000, 'Paco':2850000, 'Pdco':2900000, 'Vdco':1077,
                                'C0': -0.0,'C1':0.0001, 'C2':0.000911, 'C3':0.000215,
                                'Pnt':2000, 'Vdcmax':1500, 'Idcmax':3200, 'Mppt_low':856, 'Mppt_high':1425,
                                'CEC_Date':'2/15/2019', 'CEC_Type': 'Grid Support'}, name='SMA SC 3000-EV')
    # 'https://www.enfsolar.com/pv/inverter-datasheet/11765' and other SMA data sheets

    if module_rating == 545:
        num_of_strings_per_inverter = 212
    else:
        num_of_strings_per_inverter = 204

    num_of_module_per_inverter = num_of_strings_per_inverter * num_of_module_per_string


    dc_rated_power_inv = module_params['STC'] / 1000 * num_of_module_per_inverter  # in kW rated DC power output per inverter


    mount = pvsys.SingleAxisTrackerMount(axis_tilt=0, axis_azimuth=0, max_angle=60, backtrack=True,
                                            gcr=gcr, cross_axis_tilt=0, racking_model='open_rack',
                                            module_height=rack_params['elevation'])

    sat_array = pvsys.Array(mount=mount,
                               module_parameters=module_params,
                               temperature_model_parameters=temperature_model_parameters,
                               modules_per_string=num_of_module_per_string,
                               strings=num_of_strings_per_inverter)

    inverter_sat_system = pvsys.PVSystem(arrays=[sat_array], inverter_parameters=inverter_params)

    if cell_type == 'mono':
        mount = pvsys.SingleAxisTrackerMount(axis_tilt=0, axis_azimuth=0, max_angle=60, backtrack=True,
                                             gcr=gcr, cross_axis_tilt=0, racking_model='open_rack',
                                             module_height=rack_params['elevation'])

        sat_array = pvsys.Array(mount=mount,
                                module_parameters=module_params,
                                temperature_model_parameters=temperature_model_parameters,
                                modules_per_string=num_of_module_per_string,
                                strings=num_of_strings_per_inverter)

        inverter_sat_system = pvsys.PVSystem(arrays=[sat_array], inverter_parameters=inverter_params)
        mc = ModelChain(inverter_sat_system, location)
        mc.run_model(weather_simulation)
        multiplication_coeff = num_of_zones * num_of_inv_per_zone
        dc_results_total = mc.results.dc['p_mp'] * multiplication_coeff

    elif cell_type == 'bifacial':
        mount = bifacial_pvsystem.SingleAxisTrackerMount(axis_tilt=0, axis_azimuth=0, max_angle=60, backtrack=True,
                                             gcr=gcr, cross_axis_tilt=0, racking_model='open_rack',
                                             module_height=rack_params['elevation'])

        sat_array = bifacial_pvsystem.Array(mount=mount,
                                module_parameters=module_params,
                                temperature_model_parameters=temperature_model_parameters,
                                modules_per_string=num_of_module_per_string,
                                strings=num_of_strings_per_inverter)

        inverter_sat_system = bifacial_pvsystem.PVSystem(arrays=[sat_array], inverter_parameters=inverter_params)
        mc = bifacial_modelchain.ModelChain(inverter_sat_system, location)
        mc.run_model_bifacial(weather_simulation)
        multiplication_coeff = num_of_zones * num_of_inv_per_zone
        dc_results_total = mc.results.dc['p_mp'] * multiplication_coeff

    return dc_results_total, mc, mount

def mc_dc(DCTotal,
             rack_params,
             module_params,
             temp_model,
             weather_simulation,
             racks_per_zone,
             modules_per_zone,
             gcr,
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
        dc_results: List
            time series (Wh) of DC yield per zone for the studied TMYs according to the range of number of racks per zone
        dc_df: Pandas DataFrame
            dataframe (Wh) of dc_results with columns matched to the range of number of racks per zone
        dc_size: Pandas series
            dc rated power (MW) of the solar farm according to range of number of racks per zone

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
        raise ValueError('Please choose temperature model as Sandia: or PVSyst')

    if rack_params['rack_type'] == 'east_west':
        ''' DC modelling for 5B Mavericks with fixed ground mounting in east-west direction  '''

        # Inverter (this part finds an inverter from the CEC list that matches the DC output of the system)
        num_of_mod_per_inverter = num_of_mav_per_inverter * rack_params['Modules_per_rack']
        # in kW rated DC power output per inverter
        dc_rated_power = module_params['STC'] / 1000 * num_of_mod_per_inverter

        dc_to_ac = 1.2
        ac_rated_power = dc_rated_power / dc_to_ac  # in kW rated AC power output
        inverter_list = pvsys.retrieve_sam('cecinverter')

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
        mount1 = pvsys.FixedMount(surface_tilt=module_tilt, surface_azimuth=90)  # east facing array
        mount2 = pvsys.FixedMount(surface_tilt=module_tilt, surface_azimuth=270)  # west facing array

        # Define two arrays resembling Maverick design: one east facing & one west facing
        # For now we are designing at the inverter level with 4 MAVs per inverter. Half of the array is assigned with
        # mount 1 (east facing) and the other half is assigned with mount 2 (west facing)
        array_one = pvsys.Array(mount=mount1,
                                   module_parameters=module_params,
                                   temperature_model_parameters=temperature_model_parameters,
                                   modules_per_string=num_of_module_per_string,
                                   strings=num_of_strings_per_mav * num_of_mav_per_inverter / 2)

        array_two = pvsys.Array(mount=mount2,
                                   module_parameters=module_params,
                                   temperature_model_parameters=temperature_model_parameters,
                                   modules_per_string=num_of_module_per_string,
                                   strings=num_of_strings_per_mav * num_of_mav_per_inverter / 2)

        inverter_mav_system = pvsys.PVSystem(arrays=[array_one, array_two], inverter_parameters=inverter_params)

        # Model-Chain
        # Todo: We can try different angle of irradiance (aoi) models down the track
        mc = ModelChain(inverter_mav_system, location, aoi_model='ashrae')
        # mc = ModelChain(system, location, aoi_model='sapm')  # another aoi model which could be explored...

        mc.run_model(weather_simulation)
        total_module_number = round(DCTotal/(module_params['STC'] / 1e6))
        # Find the total DC output for the given DC size/total module number
        # If you want to find the per zone output, find multiplication coefficient based on number of modules per zone
        multiplication_coeff = total_module_number/num_of_mod_per_inverter
        dc_results_total = (mc.results.dc[0]['p_mp'] + mc.results.dc[1]['p_mp']) * multiplication_coeff
        # dc_results is the DC yield of the total solar farm

        dc_size = modules_per_zone * module_params['STC'] / 1e6 * num_of_zones  # dc_size in MW

        # Converting MAV DC results to match SAT results according SAT's module_per_zone_num_range
        dc_results = [dc_results_total.values/total_module_number * modules_per_zone]
        dc_df = pd.DataFrame(dc_results).T
        # dc_df.columns = racks_per_zone
        dc_df.index = dc_results_total.index

    elif rack_params['rack_type'] == 'SAT':
        ''' DC modelling for single axis tracking (SAT) system '''

        # Inverter (this part finds an inverter from the CEC list that matches the DC output of the system)
        # Todo: Currently number of SAT per inverter is set to 4. Get more info from SunCable...
        # Todo: If these parts are essentially same for MAV and SAT move this code prior to the IF for mounting type
        num_of_mod_per_inverter = num_of_sat_per_inverter * rack_params['Modules_per_rack']
        dc_rated_power = module_params['STC'] / 1000 * num_of_mod_per_inverter  # in kW rated DC power output per inverter
        dc_to_ac = 1.2
        ac_rated_power = dc_rated_power / dc_to_ac  # in kW rated AC power output
        inverter_list = pvsys.retrieve_sam('cecinverter')

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

        if module_params['Bifacial'] > 0:
            mount = bifacial_pvsystem.SingleAxisTrackerMount(axis_tilt=0, axis_azimuth=0, max_angle=60,
                                                            backtrack=True,
                                                            gcr=gcr, cross_axis_tilt=0,
                                                            racking_model='open_rack',
                                                            module_height=rack_params['elevation'])

            sat_array = bifacial_pvsystem.Array(mount=mount,
                                                    module_parameters=module_params,
                                                    temperature_model_parameters=temperature_model_parameters,
                                                    modules_per_string=num_of_module_per_string,
                                                    strings=num_of_strings_per_sat * num_of_sat_per_inverter)

            inverter_sat_system = bifacial_pvsystem.PVSystem(arrays=[sat_array],
                                                    inverter_parameters=inverter_params)
            mc = bifacial_modelchain.ModelChain(inverter_sat_system, location)
            mc.run_model_bifacial(weather_simulation)
            multiplication_coeff = modules_per_zone / num_of_mod_per_inverter
            dc_results.append(mc.results.dc['p_mp'] * multiplication_coeff)
            dc_size.append(modules_per_zone * num_of_zones * module_params['STC'] / 1e6)

        else:
            mount = pvsys.SingleAxisTrackerMount(axis_tilt=0, axis_azimuth=0, max_angle=60, backtrack=True,
                                                     gcr=gcr, cross_axis_tilt=0, racking_model='open_rack',
                                                     module_height=rack_params['elevation'])

            sat_array = pvsys.Array(mount=mount,
                                        module_parameters=module_params,
                                        temperature_model_parameters=temperature_model_parameters,
                                        modules_per_string=num_of_module_per_string,
                                        strings=num_of_strings_per_sat * num_of_sat_per_inverter)

            inverter_sat_system = pvsys.PVSystem(arrays=[sat_array], inverter_parameters=inverter_params)
            mc = ModelChain(inverter_sat_system, location)
            mc.run_model(weather_simulation)
            multiplication_coeff = modules_per_zone / num_of_mod_per_inverter
            dc_results.append(mc.results.dc['p_mp'] * multiplication_coeff)
            dc_size.append(modules_per_zone * num_of_zones * module_params['STC'] / 1e6)

        # Todo: we can try different back-tracking algorithms for SAT as well
        dc_df = pd.DataFrame(dc_results).T
        # dc_df.columns = racks_per_zone
    else:
        raise ValueError("Please choose racking as one of these options: 5B_MAV or SAT_1")

    # Change the time-stamp from UTC to Australia/Darwin
    # dc_df.index = dc_df.index.tz_convert('Australia/Darwin')
    return dc_results, dc_df, dc_size

def apply_degradation(ghi, first_year_degradation, degradation_rate):
    """"""

    delta_index = (ghi.index - ghi.index[0]).days
    delta_t = delta_index.to_frame(index=False)
    deg_y1 = first_year_degradation/3.65e4
    deg_ann = degradation_rate/3.65e4

    delta_t.loc[(delta_t[0] <= 365)] = 1-delta_t*deg_y1/3.65e4
    delta_t.loc[(delta_t[0] > 365)] = 1-deg_y1/100-deg_ann*delta_t/3.65e4

    delta_t.index = ghi.index
    delta_t.columns = np.arange(len(delta_t.columns))

    return delta_t

def apply_soiling(soiling_var, weather, default_soiling):
    """"""

    month_timeseries = weather.index.month
    dummy = month_timeseries.to_series()
    init_soiling = dummy.astype('float64', copy=True)
    for month, value in default_soiling:
        init_soiling.loc[init_soiling == month] = value

    total_soiling = 1-init_soiling*soiling_var

    total_soiling.index = weather.index

    return total_soiling

def apply_temp_loss(temp_var, ghi, coefficient):
    """"""

    temp_df = ghi*temp_var
    temp_df *= coefficient/1000
    temp_loss = 1+temp_df

    temp_loss.index = ghi.index

    return temp_loss


def get_dcloss(loss_parameters, weather, default_soiling, temp_coefficient):
    """"""

    soiling_df = apply_soiling(soiling_var=loss_parameters['soiling_modifier'],
                               weather=weather['ghi'], default_soiling=default_soiling)

    temp_df = apply_temp_loss(temp_var=loss_parameters['ave_temp_increase'], ghi=weather['ghi'], coefficient=temp_coefficient)

    tol_mismatch = 1-loss_parameters['tol_mismatch']/100

    loss_df = soiling_df*temp_df*tol_mismatch

    return loss_df

