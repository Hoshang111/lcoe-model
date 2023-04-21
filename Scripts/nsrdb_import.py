import requests
import pandas as pd
import urllib.parse
import time

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
            data = get_response_json_and_handle_errors(requests.post(BASE_URL, input_data, headers=headers))
            download_url = data['outputs']['downloadUrl']
            # You can do with what you will the download url
            print(data['outputs']['message'])
            print(f"Data can be downloaded from this url when ready: {download_url}")

            # Delay for 1 second to prevent rate limiting
            time.sleep(1)
        print(f'Processed')

        return data


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

API_KEY = "gHAuzn9Uv6qRgQ8EYgTdIQRkWk2hpfqNjTxItLQk"
EMAIL = "p.hamer@unsw.edu.au"
BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/himawari-tmy-download.csv?"
DATASET = ['tmy-2020']
LAT = -21.47
LONG = 129.04
POINTS = '1511107'
weather_data = get_nsrdb(API_KEY, EMAIL, BASE_URL, LAT, LONG, DATASET)
