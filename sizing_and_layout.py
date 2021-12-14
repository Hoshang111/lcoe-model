# -*- coding: utf-8 -*-
# Sizing and costing model.
# import python libraries
from pvlib.modelchain import ModelChain
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import datetime
import pvlib
import os.path
import os
import sys
import suncable_cost as SunCost


# Define plot setting
COLOR = 'dimgrey'
mpl.rc('axes', edgecolor=COLOR)
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['text.color'] = COLOR
mpl.rcParams['axes.labelcolor'] = COLOR
mpl.rcParams['xtick.color'] = COLOR
mpl.rcParams['ytick.color'] = COLOR

# Import scenario and SCOPTI Data, includes revenue time series, weather time series selection, module and tracker, battery and size
# SCPIdf = pd.read_csv('', sep =',', low_memory=False)
# SCNdf = pd.read_csv('', sep = '', low_memory=False)

# Initial Guess at total DC power
DCTotal = 1e10

# Number of Fields, used to determine export limits etc.
FieldNum = 500

# Area for Field in m2
FieldArea = 200000

# Export limit for project
TRANSlimit = 3.2e9

# Define Available Revenue (should come from inputs)

FixedPrice = 40

# Define Scenario parameters based on inputs
# if SCNdf()

# Define System Variations, These should be based on scenario and scopti inputs

# Initial Number of modules per field, set by racks, overwritten by new code to import from database
# RackNum = 368
# ModulesperRack = 120
# ModuleNum = RackNum*ModulesperRack

# ExportLimit = TRANSlimit/(ModuleNum*FieldNum)

# Storage Efficiency, used for internal dispatch profiles
StorageEff = 0.85



# Run PVlib for specified system

# Import Weather Data
# First iteration using TMY as supplied by suncable

coordinates = [(-18.7692,133.1659,'Suncable_Site', 00, 'Australia/Darwin')]

weather = pd.read_csv(os.path.join('Data','WeatherData','Solcast_PT60M.csv'), index_col=0,
                         infer_datetime_format=True,parse_dates=[1],low_memory=False)

# weather = weather.drop(weather.columns[4],1)

# weather = weather.drop(['End of file'])

weather = weather.rename(columns={'Ghi':'ghi','Dni':'dni','Dhi':'dhi','AirTemp':'temp_air',
                                  'WindSpeed10m':'wind_speed','PrecipitableWater':'precipitable_water'})

weather.index = pd.to_datetime(weather.index)

weather['ghi'] = pd.to_numeric(weather['ghi'])

weather['precipitable_water'] = weather['precipitable_water']/10

# print (weather.dtypes)

# Initial run use standard data need to replace with Suncable data

# Import Suncable Module Database

suncable_modules = pd.read_csv(os.path.join('Data', 'SystemData', 'Suncable_module_database.csv'), index_col=0, skiprows=[1,2]).T

module = suncable_modules['Jinko_JKM575M_7RL4_TV_PRE']

# Import Rack Data from database
suncable_racks = pd.read_csv(os.path.join('Data', 'SystemData', 'Suncable_rack_database.csv'), index_col=0, skiprows=[1]).T

rack = suncable_racks['SAT_1']

# Determine Rack and Module numbers
Modules_per_rack = rack['Modules_per_rack']
Rackfloat = DCTotal/(FieldNum*Modules_per_rack*module['STC'])
Racknumber = round(Rackfloat)
RackInterval = 2

# Variations to rack number
RackNums = pd.Series(range(Racknumber-5*RackInterval, Racknumber+6*RackInterval, RackInterval))

# Convert to number of modules for GCR calculations
Modulenumber = Racknumber*Modules_per_rack
ModuleNums = RackNums*Modules_per_rack

# print (module.dtypes)
#temporarily put airtable call here

# sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')

sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')

# module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']

# at present the inverter limits the output, need to switch to different inverter
inverter = sapm_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']

temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[
    'sapm']['open_rack_glass_glass']

# temp_air = 30

# wind_speed = 0

# define gcr via number of modules and area (approximation)
GCR = module['A_c']*Modulenumber/FieldArea
GCRlist = module['A_c']*ModuleNums/FieldArea
gcrrange = ModuleNums.size

print(GCRlist)

energies = {}
ACoutput = {}
Arrays = [0,0,0,0,0,0,0,0,0,0,0]

# this should ultimately change to an if/else statement based on rack type
for i in range(gcrrange):
    gcr = GCRlist[i]
    ModuleNumber = ModuleNums[i]

    mount = pvlib.pvsystem.SingleAxisTrackerMount(axis_tilt=0, axis_azimuth=0, max_angle=90, backtrack=True, gcr=gcr, cross_axis_tilt=0,
                                              racking_model='open_rack', module_height=2)

    Arrays[i] = pvlib.pvsystem.Array(mount=mount, module_parameters=module,
                             temperature_model_parameters=temperature_model_parameters)

system = pvlib.pvsystem.PVSystem(arrays=Arrays, inverter_parameters=inverter)

for latitude, longitude, name, altitude, timezone in coordinates:
 #   naive_times=weather.index
 #   weather.index = weather.index.tz_localize(timezone)
 #   times = weather.index + pd.DateOffset(minutes=30)
    location = Location(latitude, longitude, name=name, altitude=altitude,
               tz=timezone)
 #   solar_position = location.get_solarposition(times,temperature=weather['temp_air'])
 #   solar_position.index = solar_position.index + pd.DateOffset(minutes=-30)
 #   print (solar_position.dtypes)
    # the dni function is borderline ridiculous, either significantly rework or get TMY with dni
#    dni = pvlib.irradiance.dni(weather['ghi'],weather['dhi'],solar_position['zenith'])
#    weather.insert(1,'dni',dni)
#    weather = location.get_clearsky(times)
    mc = ModelChain(system, location)
    mc.run_model(weather)
    DCoutput = mc.results.dc
    DCppm = [df['p_mp'] for df in DCoutput]

energies = [sum(tup) for tup in DCppm]
energies = pd.Series(energies)
DCSeries = pd.DataFrame(DCppm).T
DCSeries.columns = RackNums
DCpower = DCSeries.mul(ModuleNums.values, axis=1)

Yieldseries = energies*ModuleNums
LayoutList = pd.DataFrame([RackNums, ModuleNums, GCRlist, energies, Yieldseries], index=[
    'Number of Racks', 'Number of Modules', 'gcr', 'Yield_per_module', 'Yield'])


print(energies.round(0))
# verified it runs to this point and returns total energy, will instead need to export energy timeseries and convert to revenue
# if SCNdf['type']='SAT'
#     rowspace=SCPIdf['zonedim']/SCPIdf['racknum']

# Assign Revenue Generation based on exporting at capacity, with excess stored and subsequently exported
# This will need to become significantly more complex to handle battery operation and more complex tariffs

# up to this point we have calculated for a range of layouts, now need to perform comparison with costs
# GrossAC = mc.results.ac

ExportDC = DCpower.clip(lower=None, upper=TRANSlimit)

StoredDC = DCpower-ExportDC

ExportREV = ExportDC*FixedPrice

StoredREV = StoredDC*StorageEff*FixedPrice

TotalREV = ExportREV+StoredREV

# This gives us our primary outputs, a time series of system yield and revenue generation
# Further manipulation should group these into yearly outputs for comparison with cost data timeseries

YearlyRev = TotalREV.groupby(TotalREV.index.year).sum()

# Just some code to visualise the outputs and check it works as intended
# Stored_Ratio = StoredREV/ExportREV

# YieldRev = {'Time': mc.results.times, 'AC_output': GrossAC, 'Export_W': ExportAC, 'Export_$': ExportREV, 'Store_W': StoredAC,
#             'Store_$': StoredREV, 'Store_Ratio': Stored_Ratio}

# YieldRevData = pd.DataFrame(YieldRev, columns=[
#                             'Time', 'AC_output', 'Export_W', 'Export_$', 'Store_W', 'Store_$', 'Store_Ratio'])

# YieldRevData['month'] = YieldRevData['Time'].dt.month
#
# YieldRevData['hour'] = YieldRevData['Time'].dt.hour

# OutputPlot = YieldRevData.pivot_table(values='Store_Ratio', index=[
#                                       'month'], columns=['hour'], aggfunc=np.mean).round(3)

# YearlyOutput = YieldRevData.groupby(YieldRevData['Time'].dt.year).sum()

# Manipulating the output to match the timeframe of the cost model 2024-2058
# YearlyRev = pd.DataFrame(np.zeros(shape=(31,8)),columns=['AC_output','Export_W','Export_$',
#                                                         'Store_W','Store_$','Store_Ratio','month','hour'])
CashIn = pd.DataFrame(np.zeros(shape=(31,11)), columns=RackNums)

CashIn[5:15] = YearlyRev[4:14]
CashIn[15:25] = YearlyRev[4:14]
CashIn[25:31] = YearlyRev[4:10]

#cYearlyRev.index = [list(range(2024,2059,1))]

# YearlyRev = YearlyRev.rename('Year')

# Graphing details for test plot
# plt.matshow(OutputPlot, cmap='YlOrRd', aspect='auto')
# bar = plt.colorbar()
# cbar.set_label('Stored Ratio')
# plt.xlabel('Hour of Day')
# plt.ylabel('Month')
# plt.show()

# Call costing tool
# Option 1: Call as zones, installation year


# SCNcostdata.to_csv(os.path.join('Data','CostData','Scenariolist.csv'), index=False)

# SYScostdata.to_csv(os.path.join('Data','CostData','SystemLink.csv'), index=False)

# Option 2: Specify components for system, quantity and year
# costdbcol = ['ModuleA','ModuleB','ModuleC','SAT1','SAT2','SAT3','MAV','InverterA','InverterB',
#            'Wiring10mm','Wiring15mm']
# costindexA = pd.date_range(SCNdf['startdate'],periods=SCNdf['projyears'], freq="Y")
# costindex = constindexA.dt.year

# Tell Cost Model to run
# run nathansfunkythang

# Import .csv output from cost model

# Option 3 Call code directly and overwrite values as required
ScenarioList = {'Scenario_Name': RackNums,
                'ScenarioID': RackNums, 'Scenario_Tag': RackNums}

SCNcostdata = pd.DataFrame(ScenarioList, columns=[
                           'Scenario_Name', 'ScenarioID', 'Scenario_Tag'])


SystemLinkracks = {'ScenarioID': RackNums, 'ScenarioSystemID': RackNums, 'InstallNumber': RackNums,
              'SystemID': RackNums, 'InstallDate': RackNums}

SYScostracks = pd.DataFrame(SystemLinkracks, columns=[
                           'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])

SYScostracks['SystemID'] = 13
SYScostracks['InstallDate'] = 2025

SystemLinkfixed = {'ScenarioID': RackNums, 'ScenarioSystemID': RackNums, 'InstallNumber': RackNums,
              'SystemID': RackNums, 'InstallDate': RackNums}

SYScostfixed = pd.DataFrame(SystemLinkfixed, columns=[
                           'ScenarioID', 'ScenarioSystemID', 'InstallNumber', 'SystemID', 'InstallDate'])

SYScostfixed['SystemID'] = 14
SYScostfixed['InstallDate'] = 2025
SYScostfixed['InstallNumber'] = 1

SYScostData = SYScostracks.append(SYScostfixed)

SYScostData['ScenarioSystemID'] = range(1, 2*len(RackNums)+1)

# Airtable Import
api_key = 'keyJSMV11pbBTdswc'
base_id='appjQftPtMrQK04Aw'

data_tables = SunCost.import_airtable_data(base_id=base_id, api_key=api_key)
scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list = data_tables


# Replacing some tables from specified inputs
new_data_tables = SCNcostdata, SYScostData, system_list, system_component_link, component_list, currency_list, costcategory_list

# Running the cost calculations
# outputs = SunCost.CalculateScenarios (data_tables, year_start=2024, analyse_years=30)
costoutputs = SunCost.CalculateScenarios (new_data_tables, year_start=2024, analyse_years=30)
component_usage_y, component_cost_y, total_cost_y, cash_flow_by_year = costoutputs


CashIn.index = cash_flow_by_year.index
# YearlyCostsdf = pd.read_csv(os.path.join('Data','CostData','Cash_flow_by_year.csv'), sep =',', low_memory=False)

# Convert to datetime and groupby year
#YearlyCostsdf['Time'] = pd.to_datetime(YearlyCostsdf['Year'], format='%Y')
# YearlyCosts = YearlyCostsdf.groupby(YearlyCostsdf['Time'].dt.year).sum()

# Add costs and revenues
NetCashflow = CashIn - cash_flow_by_year

Yearoffset = pd.Series(range(0, 31))
Yearoffset.index = NetCashflow.index

DiscountRate = 0.07

YearlyFactor = 1/(1+DiscountRate)**Yearoffset
YearlyNPV = NetCashflow.mul(YearlyFactor, axis=0)

# Need to add any external costs for transmission etc.

NPV = YearlyNPV.sum(axis=0)