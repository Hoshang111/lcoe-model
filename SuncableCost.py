
from airtable import Airtable
import datetime
import time as time
import os
import numpy as np
import pandas as pd

data_file_location = '.\\outputs\\'
log_file_location = '.\\AirtableLogs\\'



def get_airtable(base_id, api_key, table_name, sort_by = None, required_list = []):
    print('  Getting data from ', table_name)

    # First connect to the specified table name in the airtable database
    at = Airtable(base_id, table_name, api_key=api_key).get_all()

    # Get a full list of all columns - not all records have every column, so we need to search through every record!
    all_column_names = set()
    for record in at:
        all_column_names.update(list(record['fields'].keys()))
    col_list = all_column_names.copy()
    # Now remove from this list the fields that need to be removed
    for item in col_list:
        if item.startswith('_'):
            all_column_names.remove(item)

    column_names = list(all_column_names)

    if sort_by is None:
        at = Airtable(base_id, table_name, api_key=api_key).get_all(fields=column_names)
    else:
        at = Airtable(base_id, table_name, api_key=api_key).get_all(fields=column_names,sort=[(sort_by, 'asc')])

    row_count = len(at)

    pandas_frame = pd.DataFrame(0, index=range(0,row_count), columns=column_names)
    i = 0
    for record in at:
        for field in record['fields']:
            # Airtable will annoyingly return a list of items for the ID. In this case, just take the first item
            if type(record['fields'][field]) is list:
                pandas_frame.loc[i, field] = record['fields'][field][0]
            else:
                pandas_frame.loc[i,field] = record['fields'][field]
        i += 1

    # Some error checking
    # Check if any ID values are zero
    if len(pandas_frame[pandas_frame[sort_by] == 0]) > 0:
        print('** Error - at least one row has no ID!')

    # Check if any specific "required" fields are zero.
    for col in required_list:
        if len(pandas_frame[pandas_frame[col] == 0]) > 0:
            error_list = pandas_frame[pandas_frame[col] == 0]
            print('** Error! Entries ',str(list(error_list[sort_by])),' need data for ',col)
    return pandas_frame

def save_tables_as_excel(table_name_list):
    time_indicator = '{:%Y-%m-%d %H-%M}'.format(datetime.datetime.now())
    writer = pd.ExcelWriter(log_file_location + 'output' + str(time.time()) +'.xlsx')
    writer = pd.ExcelWriter(log_file_location + 'output ' + time_indicator + '.xlsx')
    for (table,name) in table_name_list:
        table.to_excel(writer, name)
    writer.save()

def import_airtable_data(base_id, api_key):

    def my_get_airtable(table_name,sort_by,excel_save_list):
        my_list = get_airtable(base_id, api_key, table_name, sort_by=sort_by)
        excel_save_list.append((my_list, table_name))
        return my_list

    print("Getting data from Airtable database")

    excel_save_list = []
    scenario_list = my_get_airtable('ScenarioList', 'ScenarioID', excel_save_list)
    system_list = my_get_airtable('SystemList', 'SystemID', excel_save_list)
    scenario_system_link = my_get_airtable('ScenarioSystemLink', 'ScenarioSystemID', excel_save_list)
    component_list = my_get_airtable('ComponentList', 'ComponentID', excel_save_list)
    system_component_link = my_get_airtable('SystemComponentLink', 'SystemComponentID', excel_save_list)
    currency_list = my_get_airtable('CurrencyList', 'CurrencyID', excel_save_list)
    costcategory_list = my_get_airtable('CostCategoryList', 'CostCategoryID', excel_save_list)
    save_tables_as_excel(excel_save_list)
    print("Finished importing airtable data")


    return scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list

def import_excel_data(excel_file_name):
    scenario_list = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name),sheet_name='ScenarioList',index_col=0)
    system_list = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name),sheet_name='SystemList',index_col=0)
    scenario_system_link = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name),sheet_name='ScenarioSystemLink',index_col=0)
    component_list = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name),sheet_name='ComponentList',index_col=0)
    system_component_link = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name),sheet_name='SystemComponentLink',index_col=0)
    currency_list = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name),sheet_name='CurrencyList',index_col=0)
    costcategory_list = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name),sheet_name='CostCategoryList',index_col=0)

    return scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list

def CalculateScenarios(input_tables, year_start, analyse_years):

    # Two key tables are generated by this analysis.
    # The first is a list of components and the year that each is expended.
    # The second is a list of components and their cost in each year.
    # The only years calculated are between year_start and year_start + analyse_years.
    year_list = pd.DataFrame(list(range(year_start, year_start+analyse_years+1)),columns=['Year'])
    year_list['Temp'] = 1 # To allow a "cross" merge later


    scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list = input_tables
    ###########################################
    # Components used per year
    # Final table will have these columns
    # ScenarioSystemID (Key) | SystemComponentID (Key) | Year (Key) | ScenarioID | SystemID | ComponentID | CostCategoryID | NumberComponents
    ###########################################

    component_usage_by_year = scenario_system_link.merge(system_component_link,how='left',on='SystemID').merge(costcategory_list,how='left',on='CostCategoryID')
    component_usage_by_year['Temp'] = 1
    component_usage_by_year = component_usage_by_year.merge(year_list, how='inner', on='Temp').drop(['Temp'],axis=1)


    # Reset usage to zero for all time first
    component_usage_by_year['TotalUsageY'] = 0

    # Any "Installation" cost components only have a cost in the year of installation
    component_usage_by_year['TotalUsageY'] = np.where(((component_usage_by_year['Timing']=='Installation') & (component_usage_by_year['InstallDate']==component_usage_by_year['Year'])),component_usage_by_year['InstallNumber']*component_usage_by_year['Usage'],component_usage_by_year['TotalUsageY'])

    # Any "PerOperationYear" cost  components only occur in the years following installation
    component_usage_by_year['TotalUsageY'] = np.where(
        ((component_usage_by_year['Timing'] == 'PerOperationYear') & (component_usage_by_year['InstallDate'] < component_usage_by_year['Year'])),
        component_usage_by_year['InstallNumber'] * component_usage_by_year['Usage'], component_usage_by_year['TotalUsageY'])




    ###########################################
    # Components costs per year
    # Final table will have these columns
    # ComponentID (Key) | Year (Key) | Cost
    ###########################################
    component_cost_by_year = component_list.merge(currency_list, how='left',on='CurrencyID')
    component_cost_by_year['Temp'] = 1

    component_cost_by_year = component_cost_by_year.merge(year_list,how='inner',on='Temp')
    component_cost_by_year.drop('Temp',axis=1,inplace=True)

    component_cost_by_year['AUDBaseline'] = component_cost_by_year['To_AUD']*component_cost_by_year['BaselineCost']
    # For now, assume everything uses an annual multiplier for cost
    component_cost_by_year['AUDCostY'] = component_cost_by_year['AUDBaseline'] * component_cost_by_year['AnnualMultiplier'] ** (component_cost_by_year['Year'] - component_cost_by_year['BaselineYear'])


    ############################################
    # Combining both data tables to give total costs
    ############################################

    combined_cost_usage = component_usage_by_year.merge(component_cost_by_year,how='left',on=['Year','ComponentID'])
    combined_cost_usage['TotalCostAUDY'] = combined_cost_usage['AUDCostY']*combined_cost_usage['TotalUsageY']

    ############################################
    # Add up total costs per year for each ScenarioID.
    ############################################

    cash_flow_year = pd.pivot_table(combined_cost_usage, values='TotalCostAUDY', index='Year',aggfunc=np.sum,columns='ScenarioID')


    return component_usage_by_year, component_cost_by_year, combined_cost_usage, cash_flow_year


