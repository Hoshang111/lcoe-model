# Code for importing weather data from file and configuring for pvlib
import pandas as pd

def get_weather(weather_file, years):

    simulation_years = (str(e) for e in years)

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    weather = pd.read_csv(os.path.join('Data', 'WeatherData', weather_file), index_col=0)

    weather.set_index(pd.to_datetime(weather.index), inplace=True)  # set index to datetime format (each index now
    # represents end of the hourly period: i.e. 2007-01-01 02:00:00 represents the measurements between 1-2 am

    # Change the timezone of the datetime to Australia/Darwin (this may not be necessary/change timezone at the very end)
    # dummy = [str(i)[0:19] for i in weather.index]
    # weather.set_index(pd.DatetimeIndex(dummy, tz='UTC'), inplace=True)

    weather = weather.rename(columns={'Ghi': 'ghi', 'Dni': 'dni', 'Dhi': 'dhi', 'AirTemp': 'temp_air',
                                      'WindSpeed10m': 'wind_speed', 'PrecipitableWater': 'precipitable_water'})

    weather_simulation = weather[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed', 'precipitable_water']].copy()[
        simulation_years]
    weather_simulation['precipitable_water'] = weather_simulation['precipitable_water'] / 10  # formatting for PV-lib

    return weather_simulation
