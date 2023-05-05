import requests
import pandas as pd
import urllib.parse
import time
import pvlib
import os
import ast
import math

def get_nsrdb(api_key, email, base_url, lat, long, datasets):

    input_data = {
        'wkt': "POINT(" + str(long) + " " + str(lat) + ")",
        'attributes': 'air_temperature,dew_point,dhi,dni,surface_albedo,surface_pressure,wind_speed,ghi,cloud_type,relative_humidity,wind_direction,total_precipitable_water',
        'interval': '60',
        'api_key': api_key,
        'email': email,
    }
    for name in datasets:
        print(f"Processing name: {name}")

        input_data['names'] = [name]

        if '.csv' in base_url:
            url = base_url + urllib.parse.urlencode(input_data, True)
            print(url)
            # Note: CSV format is only supported for single point requests
            # Suggest that you might append to a larger data frame
            data = pd.read_csv(url)
            print(f'Response data (you should replace this print statement with your processing): {data}')
            # You can use the following code to write it to a file
            # data.to_csv('SingleBigDataPoint.csv')
        else:
            headers = {
                'x-api-key': api_key
            }
            data = get_response_json_and_handle_errors(requests.post(base_url, input_data, headers=headers))
            download_url = data['outputs']['downloadUrl']
            # You can do with what you will the download url
            print(data['outputs']['message'])
            print(f"Data can be downloaded from this url when ready: {download_url}")

            # Delay for 1 second to prevent rate limiting
            time.sleep(1)
        print(f'Processed')

        metadata = data.loc[0].copy(deep=True)
        data.rename(columns={'Source':'Year', 'Location ID':'Month', 'City':'Day',
                             'State': 'Hour', 'Country':'Minute', 'Latitude':'Temperature',
                             'Longitude':'Dew Point', 'Time Zone':'dhi', 'Elevation':'dni',
                             'Local Time Zone':'Surface Albedo', 'Clearsky DHI Units':'Pressure',
                             'Clearsky DNI Units':'Wind Speed', 'Clearsky GHI Units':'ghi',
                             'Dew Point Units':'Cloud Type','DHI Units':'Relative Humidity',
                             'DNI Units':'Wind Direction', 'GHI Units':'precipitable_water'}, inplace=True)
        data.drop([0,1], axis=0, inplace=True)

        data.index = pd.to_datetime(data[['Year', 'Month', 'Day', 'Hour', 'Minute']]
                                            .astype(str).agg('-'.join, axis=1), format='%Y-%m-%d-%H-%M')

        data = data.astype('float')

        return metadata, data


def get_response_json_and_handle_errors(response: requests.Response) -> dict:
    """Takes the given response and handles any errors, along with providing
    the resulting json

    Parameters
    ----------
    response : requests.Response
        The response object

    Returns
    -------
    dict
        The resulting json
    """
    if response.status_code != 200:
        print(
            f"An error has occurred with the server or the request. The request response code/status: {response.status_code} {response.reason}")
        print(f"The response body: {response.text}")
        exit(1)

    try:
        response_json = response.json()
    except:
        print(
            f"The response couldn't be parsed as JSON, likely an issue with the server, here is the text: {response.text}")
        exit(1)

    if len(response_json['errors']) > 0:
        errors = '\n'.join(response_json['errors'])
        print(f"The request errored out, here are the errors: {errors}")
        exit(1)
    return response_json

def get_module(module_type):
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

    bang_modules = pd.read_csv(os.path.join('../Data', 'SystemData', 'bang_module_database.csv'), index_col=0,
                                   skiprows=[1, 2], converters={"cost_components": lambda x: ast.literal_eval(str(x))}).T

    module_params = bang_modules[module_type]

    return module_params

def get_inverter():
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
    invdb = pvlib.pvsystem.retrieve_sam('CECInverter')
    inverter_params = invdb.SMA_America__SC_2500_EV_US__550V_

    return inverter_params

def get_layout(site_area, mw_rating, lat, module, modules_per_inverter, tilt=20):
    """"""

    theta = 23.45+lat
    area_ratio_raw = math.tan(theta)/(math.cos(tilt)*math.tan(theta)+math.sin(tilt))
    module_number_raw = 0.9*site_area*area_ratio_raw/module['A_c']
    inverter_num = math.floor(module_number_raw/modules_per_inverter)
    provisional_mw = inverter_num*modules_per_inverter*module['STC']
# Need to check whether MW rating is referred to as AC or DC...
    if provisional_mw < mw_rating:
        final_mw = provisional_mw
    else:
        inverter_num = math.floor(mw_rating/(module['STC']*modules_per_inverter))
        final_mw = inverter_num*modules_per_inverter*module['STC']

    return final_mw, inverter_num

def get_flood_mul(flood_risk):


    if flood_risk == 'none':
        flood_mul = 0
    elif flood_risk == 'low':
        flood_mul = 1
    elif flood_risk == 'moderate':
        flood_mul = 2
    elif flood_risk == 'severe':
        flood_mul = 3

    return flood_mul

