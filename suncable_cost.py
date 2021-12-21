import os
import datetime
import math
import random as rd
import numbers
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from airtable import Airtable
from scipy import stats

data_file_location = '.\\outputs\\'
log_file_location = '.\\AirtableLogs\\'

def get_airtable(base_id, api_key, table_name, sort_by=None, required_list=[]):
    print('  Getting data from ', table_name)

    # First connect to the specified table name in the airtable database
    at = Airtable(base_id, table_name, api_key=api_key).get_all()

    # Get a full list of all columns - not all records have every column, 
    # so we need to search through every record!
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
        at = Airtable(base_id, table_name, api_key=api_key).get_all(fields=column_names, sort=[(sort_by, 'asc')])

    row_count = len(at)

    pandas_frame = pd.DataFrame(0, index=range(0, row_count), columns=column_names)
    i = 0
    for record in at:
        for field in record['fields']:
            # Airtable will annoyingly return a list of items for the ID. In this case, just take the first item
            if type(record['fields'][field]) is list:
                pandas_frame.loc[i, field] = record['fields'][field][0]
            else:
                pandas_frame.loc[i, field] = record['fields'][field]
        i += 1

    # Some error checking
    # Check if any ID values are zero
    if len(pandas_frame[pandas_frame[sort_by] == 0]) > 0:
        print('** Error - at least one row has no ID!')

    # Check if any specific "required" fields are zero.
    for col in required_list:
        if len(pandas_frame[pandas_frame[col] == 0]) > 0:
            error_list = pandas_frame[pandas_frame[col] == 0]
            print('** Error! Entries ', str(list(error_list[sort_by])), ' need data for ', col)
    return pandas_frame


def save_tables_as_excel(table_name_list):
    time_indicator = '{:%Y-%m-%d %H-%M}'.format(datetime.datetime.now())

    writer = pd.ExcelWriter(log_file_location + 'output ' + time_indicator + '.xlsx')
    for (table, name) in table_name_list:
        table.to_excel(writer, name)
    writer.save()


def import_airtable_data(base_id, api_key, save_tables=False):
    def my_get_airtable(table_name, sort_by, save_list):
        my_list = get_airtable(base_id, api_key, table_name, sort_by=sort_by)
        save_list.append((my_list, table_name))
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
    if save_tables:
        save_tables_as_excel(excel_save_list)
    print("Finished importing airtable data")

    return scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list


def import_excel_data(excel_file_name):
    scenario_list = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name), sheet_name='ScenarioList',
                                  index_col=0)
    system_list = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name), sheet_name='SystemList', index_col=0)
    scenario_system_link = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name),
                                         sheet_name='ScenarioSystemLink', index_col=0)
    component_list = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name), sheet_name='ComponentList',
                                   index_col=0)
    system_component_link = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name),
                                          sheet_name='SystemComponentLink', index_col=0)
    currency_list = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name), sheet_name='CurrencyList',
                                  index_col=0)
    costcategory_list = pd.read_excel(os.path.join('Data', 'CostData', excel_file_name), sheet_name='CostCategoryList',
                                      index_col=0)
    return scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list


def create_iteration_tables(input_tables, num_iterations, iteration_start=0):
    scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list = input_tables

    scenario_iter = generate_iterations(scenario_list, index_name='ScenarioID',
                                        index_description='Scenario_Tag', num_iterations=num_iterations,
                                        iteration_start=iteration_start)

    scenario_system_iter = generate_iterations(scenario_system_link, index_name='ScenarioSystemID',
                                               index_description='ScenarioSystemID', num_iterations=num_iterations,
                                               iteration_start=iteration_start)

    system_iter = generate_iterations(system_list, index_name='SystemID',
                                      index_description='SystemID', num_iterations=num_iterations,
                                      iteration_start=iteration_start)
    system_component_iter = generate_iterations(system_component_link, index_name='SystemComponentID',
                                                index_description='SystemComponentID', num_iterations=num_iterations,
                                                iteration_start=iteration_start)
    component_iter = generate_iterations(component_list, index_name='ComponentID',
                                         index_description='ComponentID', num_iterations=num_iterations,
                                         iteration_start=iteration_start)
    currency_iter = generate_iterations(currency_list, index_name='CurrencyID',
                                        index_description='Currency_Name', num_iterations=num_iterations,
                                        iteration_start=iteration_start)
    costcategory_iter = generate_iterations(costcategory_list, index_name='CostCategoryID',
                                            index_description='CostCategoryID', num_iterations=num_iterations,
                                            iteration_start=iteration_start)

    return scenario_iter, scenario_system_iter, system_iter, system_component_iter, component_iter, currency_iter, costcategory_iter


def generate_parameters(data_tables_iter):
    scenario_iter, scenario_system_iter, system_iter, system_component_iter, component_iter, currency_iter, costcategory_iter = data_tables_iter
    parameters = []
    for (iteration_list, listid) in [
        (scenario_iter, 'ScenarioID'),
        (scenario_system_iter, 'ScenarioSystemID'),
        (system_iter, 'SystemID'),
        (system_component_iter, 'SystemComponentID'),
        (component_iter, 'ComponentID'),
        (currency_iter, 'CurrencyID'),
        (costcategory_iter, 'CostCategoryID')
    ]:
        parameters = form_heirarchical_parameter_list(iteration_list, listid).join(parameters)

    return parameters


def generate_iterations(input_parameter_list, index_name, index_description, num_iterations, iteration_start=0,
                        default_dist_type=None, skip_list=[], verbose=False):
    # First identify what parameters need data to be generated
    columns_to_process = set(input_parameter_list.columns.values)
    parameter_set = set()
    fixed_set = set()
    distribution_set = set()

    if default_dist_type is None:
        dist_type = 'two_half_log_normal'

    for col in columns_to_process:
        if (col + '_H' in columns_to_process) & (col + '_L' in columns_to_process):
            parameter_set.add(col)
            if col + '_D' in columns_to_process:
                distribution_set.add(col)
        elif not (col in skip_list):
            fixed_set.add(col)
    for parameter in parameter_set:
        fixed_set.remove(parameter + '_H')
        fixed_set.remove(parameter + '_L')
    for parameter in distribution_set:
        fixed_set.remove(parameter + '_D')

    fixed_list = list(fixed_set)
    parameter_list = list(parameter_set)
    distribution_list = list(distribution_set)
    if verbose:
        print('  Fixed list: ', fixed_list)
        print('  Parameter list:', parameter_list)
        print('  distribution defined list: ', distribution_list)

    column_list = fixed_list.copy()
    column_list.extend(parameter_list)

    # Check that all parameters are accounted for
    columns_unprocessed = set(input_parameter_list.columns.values)
    for col in fixed_list:
        if col in columns_unprocessed:
            columns_unprocessed.discard(col)
        else:
            print('* Warning, fixed parameter ', col, ' has an error. It does not exist, or has been repeated')
    for col in parameter_list:
        if col in columns_unprocessed:
            columns_unprocessed.discard(col)
        else:
            print('* Warning, variable parameter ', col, ' has an error. It does not exist, or has been repeated')
        parameter = col + '_L'
        if parameter in columns_unprocessed:
            columns_unprocessed.discard(parameter)
        else:
            print('* Warning, variable parameter ', parameter, ' has an error. It does not exist, or has been repeated')
        parameter = col + '_H'
        if parameter in columns_unprocessed:
            columns_unprocessed.discard(parameter)
        else:
            print('* Warning, variable parameter ', parameter, ' has an error. It does not exist, or has been repeated')

    for col in distribution_list:
        parameter = col + '_D'
        if parameter in columns_unprocessed:
            columns_unprocessed.discard(parameter)
        else:
            print('* Warning, variable parameter ', parameter, ' has an error. It does not exist, or has been repeated')

    for col in skip_list:
        if col in columns_unprocessed:
            columns_unprocessed.discard(col)
        else:
            print('* Warning, skip parameter ', col, ' has an error. It does not exist, or has been repeated')
    for col in columns_unprocessed:
        print('* Warning, parameter ', col,
              ' has an error. It is in the table, but is not specified as fixed, variable or skipped')

    # Now create the output dataframe
    output_table = pd.DataFrame(columns=column_list)
    output_table.index.name = 'Iteration'
    parameter_generator = pd.DataFrame(index=np.arange(iteration_start, iteration_start + num_iterations),
                                       columns=column_list)
    parameter_generator.index.name = 'Iteration'

    id_list = input_parameter_list[index_name].drop_duplicates()
    for ID in id_list:
        if verbose:
            print('  Processing ', index_name, ': ', ID)
        for col in column_list:
            # print('   Col: ',col)
            if col in fixed_list:
                fill_fixed_data(input_parameter_list, index_name, ID, col, parameter_generator)
            elif col in parameter_list:
                if col in distribution_list:
                    this_dist_name = input_parameter_list[input_parameter_list[index_name] == ID][col + '_D'].values[0]
                    fill_random_data(input_parameter_list, index_name, ID, col, this_dist_name, parameter_generator)

                else:
                    fill_random_data(input_parameter_list, index_name, ID, col, dist_type, parameter_generator)
            if index_description is None:
                parameter_name = index_name + ' ' + str(ID) + ' ' + col
            else:
                name = str(input_parameter_list[input_parameter_list[index_name] == ID][index_description].values[0])
                parameter_name = name + ' (' + str(ID) + '): ' + col

                # flat_parameter_listing[parameter_name] = pd.to_numeric(parameter_generator[col])

        output_table = output_table.append(parameter_generator)
    output_table = output_table.reset_index()
    return output_table


def form_heirarchical_parameter_list(input_iteration_list, index_name, index_descriptor='none', ID_filter='none',
                                     parameter_filter='none'):
    internal_df = input_iteration_list.copy()
    if not ID_filter == 'none':
        internal_df = internal_df[internal_df[index_name].isin(filter)]
    if not parameter_filter == 'none':
        internal_df = internal_df.loc[:, parameter_filter + ['Iteration', index_name]]

    if index_descriptor != 'none':
        internal_df[index_name] = internal_df[index_name].astype(str) + ': ' + internal_df[index_descriptor]

    internal_df = internal_df.rename(columns={index_name: 'ID'})
    output_df = internal_df.pivot(columns='ID', index='Iteration')
    output_df.columns.names = ['VariableName', 'ID']
    # add the index as the grouping ID
    output_df = pd.concat([output_df], keys=[index_name], names=['GroupingID'], axis=1)
    output_df = output_df.swaplevel(i=-2, j=-1, axis=1)
    # If we want to remove any parameters that do not change, we can do so, but this is not a good idea.
    # print(index_name)
    # print(output_df.head())
    remove_fixed(output_df)
    # We want to remove any str based parameters, as they cannot be used for the contribution to variance analysis.
    remove_string_variables(output_df)
    # print(output_df.head())
    # print('')
    return output_df


def remove_string_variables(df):
    for col in df.columns:
        if not isinstance(df[col][0], numbers.Number):
            df.drop(col, inplace=True, axis=1)


def remove_fixed(df):
    for col in df.columns:
        if len(df[col].unique()) == 1:
            df.drop(col, inplace=True, axis=1)


def fill_fixed_data(parameters_file, ID_name, ID_value, parameter_name, output_data, value=None):
    if value is None:
        value = parameters_file[parameters_file[ID_name] == ID_value][parameter_name].values[0]
    output_data[parameter_name] = value


def fill_random_data(parameters_file, ID_name, ID_value, parameter_name, dist_type, output_data):
    if ((ID_name == '') and (ID_value == '')):
        nom_in = parameters_file[parameter_name].astype(float).values[0]
        low_in = parameters_file[parameter_name + 'L'].astype(float).values[0]
        high_in = parameters_file[parameter_name + 'H'].astype(float).values[0]
    else:
        nom_in = parameters_file[parameters_file[ID_name] == ID_value][parameter_name].astype(float).values[0]
        low_in = parameters_file[parameters_file[ID_name] == ID_value][parameter_name + '_L'].astype(float).values[0]
        high_in = parameters_file[parameters_file[ID_name] == ID_value][parameter_name + '_H'].astype(float).values[0]

    if (nom_in < 0 and (low_in > 0 or high_in > 0)) or (nom_in > 0 and (low_in < 0 or high_in < 0)):
        print('* Warning: ', ID_name, ': ', ID_value, ' parameter ', parameter_name, ' has differing signs on data')
    if ((nom_in != 0) and (abs(high_in) <= abs(nom_in) or abs(low_in) >= abs(nom_in)) and (
            not (high_in == nom_in and low_in == nom_in))):
        print('* Warning: ', ID_name, ': ', ID_value, ' parameter ', parameter_name, ' has abnormal data')

    if (nom_in != 0) and (low_in == 0) and (high_in == 0):
        low_in = nom_in
        high_in = nom_in
        print('* Warning: ', ID_name, ': ', ID_value, ' parameter ', parameter_name,
              ' has zero for H and L data. These have been set to match Nom data!')
    if low_in != 0:
        if (nom_in / low_in) > 3:
            print('* Warning: ', ID_name, ': ', ID_value, ' parameter ', parameter_name,
                  ' has Low data more than 3 times smaller than Nominal!')
    if (nom_in != 0):
        if ((high_in / nom_in) > 3):
            print('* Warning: ', ID_name, ': ', ID_value, ' parameter ', parameter_name,
                  ' has High data more than 3 times larger than Nominal!')
    if high_in < low_in:
        print('* Warning: ', ID_name, ': ', ID_value, ' parameter ', parameter_name,
              ' has high and low mixed up!')
        temp = high_in
        high_in = low_in
        low_in = temp
    if dist_type == 'two_half_log_normal':
        # this means a two-half log-normal distribution
        output_data[parameter_name] = output_data[parameter_name].apply(generate_log_normal_apply,
                                                                        args=(nom_in, low_in, high_in))
    else:
        print('**** ERROR - distribution not available')
    if 0 in output_data.index:
        output_data.loc[0, parameter_name] = nom_in


def generate_log_normal(nom, low, hi):
    if nom == 0:
        return 0
    else:
        zi = rd.gauss(0, 1)
        if zi > 0:
            return nom * math.exp(zi * math.log(hi / nom) / 1.28)
        else:
            return nom * math.exp(zi * math.log(nom / low) / 1.28)


def generate_log_normal_apply(self, nom, low, hi):
    dummy = self  # Gets rid of a warning about not using a parameter
    dummy += 1
    return generate_log_normal(nom, low, hi)


def calculate_scenarios(input_tables, year_start, analyse_years):
    # Two key tables are generated by this analysis.
    # The first is a list of components and the year that each is expended.
    # The second is a list of components and their cost in each year.
    # The only years calculated are between year_start and year_start + analyse_years.
    year_list = pd.DataFrame(list(range(year_start, year_start + analyse_years + 1)), columns=['Year'])
    year_list['Temp'] = 1  # To allow a "cross" merge later

    scenario_list, scenario_system_link, system_list, system_component_link, component_list, currency_list, costcategory_list = input_tables
    ###########################################
    # Components used per year
    # Final table will have these columns
    # ScenarioSystemID (Key) | SystemComponentID (Key) | Year (Key) | ScenarioID | SystemID | ComponentID | CostCategoryID | NumberComponents
    ###########################################

    component_usage_by_year = scenario_system_link.merge(system_component_link, how='left', on='SystemID').merge(
        costcategory_list, how='left', on='CostCategoryID')
    component_usage_by_year['Temp'] = 1
    component_usage_by_year = component_usage_by_year.merge(year_list, how='inner', on='Temp').drop(['Temp'], axis=1)

    # Reset usage to zero for all time first
    component_usage_by_year['TotalUsageY'] = 0

    # Any "Installation" cost components only have a cost in the year of installation
    component_usage_by_year['TotalUsageY'] = np.where(((component_usage_by_year['Timing'] == 'Installation') & (
            component_usage_by_year['InstallDate'] == component_usage_by_year['Year'])),
                                                      component_usage_by_year['InstallNumber'] *
                                                      component_usage_by_year['Usage'],
                                                      component_usage_by_year['TotalUsageY'])

    # Any "PerOperationYear" cost  components only occur in the years following installation
    component_usage_by_year['TotalUsageY'] = np.where(
        ((component_usage_by_year['Timing'] == 'PerOperationYear') & (
                component_usage_by_year['InstallDate'] < component_usage_by_year['Year'])),
        component_usage_by_year['InstallNumber'] * component_usage_by_year['Usage'],
        component_usage_by_year['TotalUsageY'])

    ###########################################
    # Components costs per year
    # Final table will have these columns
    # ComponentID (Key) | Year (Key) | Cost
    ###########################################
    component_cost_by_year = component_list.merge(currency_list, how='left', on='CurrencyID')
    component_cost_by_year['Temp'] = 1

    component_cost_by_year = component_cost_by_year.merge(year_list, how='inner', on='Temp')
    component_cost_by_year.drop('Temp', axis=1, inplace=True)

    component_cost_by_year['AUDBaseline'] = component_cost_by_year['To_AUD'] * component_cost_by_year['BaselineCost']
    # For now, assume everything uses an annual multiplier for cost
    component_cost_by_year['AUDCostY'] = component_cost_by_year['AUDBaseline'] * component_cost_by_year[
        'AnnualMultiplier'] ** (component_cost_by_year['Year'] - component_cost_by_year['BaselineYear'])

    ############################################
    # Combining both data tables to give total costs
    ############################################

    combined_cost_usage = component_usage_by_year.merge(component_cost_by_year, how='left', on=['Year', 'ComponentID'])
    combined_cost_usage['TotalCostAUDY'] = combined_cost_usage['AUDCostY'] * combined_cost_usage['TotalUsageY']

    ############################################
    # Add up total costs per year for each ScenarioID.
    ############################################

    cash_flow_year = pd.pivot_table(combined_cost_usage, values='TotalCostAUDY', index='Year', aggfunc=np.sum,
                                    columns='ScenarioID')

    return component_usage_by_year, component_cost_by_year, combined_cost_usage, cash_flow_year


def calculate_scenarios_iterations(iteration_input_tables, year_start, analyse_years):
    # Two key tables are generated by this analysis.
    # The first is a list of components and the year that each is expended.
    # The second is a list of components and their cost in each year.
    # The only years calculated are between year_start and year_start + analyse_years.
    year_list = pd.DataFrame(list(range(year_start, year_start + analyse_years + 1)), columns=['Year'])
    year_list['Temp'] = 1  # To allow a "cross" merge later

    scenario_iter, scenario_system_iter, system_iter, system_component_iter, component_iter, currency_iter, costcategory_iter = iteration_input_tables
    ###########################################
    # Components used per year
    # Final table will have these columns
    # ScenarioSystemID (Key) | SystemComponentID (Key) | Year (Key) | ScenarioID | SystemID | ComponentID | CostCategoryID | NumberComponents
    ###########################################

    component_usage_by_year_iter = scenario_system_iter.merge(system_component_iter, how='left',
                                                              on=['Iteration', 'SystemID']).merge(costcategory_iter,
                                                                                                  how='left',
                                                                                                  on=['Iteration',
                                                                                                      'CostCategoryID'])
    component_usage_by_year_iter['Temp'] = 1
    component_usage_by_year_iter = component_usage_by_year_iter.merge(year_list, how='inner', on='Temp').drop(['Temp'],
                                                                                                              axis=1)

    # Reset usage to zero for all time first
    component_usage_by_year_iter['TotalUsageY'] = 0

    # Any "Installation" cost components only have a cost in the year of installation
    component_usage_by_year_iter['TotalUsageY'] = np.where(((component_usage_by_year_iter[
                                                                 'Timing'] == 'Installation') & (
                                                                    component_usage_by_year_iter['InstallDate'] ==
                                                                    component_usage_by_year_iter['Year'])),
                                                           component_usage_by_year_iter['InstallNumber'] *
                                                           component_usage_by_year_iter['Usage'],
                                                           component_usage_by_year_iter['TotalUsageY'])

    # Any "PerOperationYear" cost  components only occur in the years following installation
    component_usage_by_year_iter['TotalUsageY'] = np.where(
        ((component_usage_by_year_iter['Timing'] == 'PerOperationYear') & (
                component_usage_by_year_iter['InstallDate'] < component_usage_by_year_iter['Year'])),
        component_usage_by_year_iter['InstallNumber'] * component_usage_by_year_iter['Usage'],
        component_usage_by_year_iter['TotalUsageY'])

    ###########################################
    # Components costs per year
    # Final table will have these columns
    # ComponentID (Key) | Year (Key) | Cost
    ###########################################
    component_cost_by_year_iter = component_iter.merge(currency_iter, how='left', on=['Iteration', 'CurrencyID'])
    component_cost_by_year_iter['Temp'] = 1

    component_cost_by_year_iter = component_cost_by_year_iter.merge(year_list, how='inner', on='Temp')
    component_cost_by_year_iter.drop('Temp', axis=1, inplace=True)

    component_cost_by_year_iter['AUDBaseline'] = component_cost_by_year_iter['To_AUD'] * component_cost_by_year_iter[
        'BaselineCost']
    # For now, assume everything uses an annual multiplier for cost
    component_cost_by_year_iter['AUDCostY'] = component_cost_by_year_iter['AUDBaseline'] * component_cost_by_year_iter[
        'AnnualMultiplier'] ** (component_cost_by_year_iter['Year'] - component_cost_by_year_iter['BaselineYear'])

    ############################################
    # Combining both data tables to give total costs
    ############################################

    combined_cost_usage_iter = component_usage_by_year_iter.merge(component_cost_by_year_iter, how='left',
                                                                  on=['Iteration', 'Year', 'ComponentID'])
    combined_cost_usage_iter['TotalCostAUDY'] = combined_cost_usage_iter['AUDCostY'] * combined_cost_usage_iter[
        'TotalUsageY']

    ############################################
    # Add up total costs per year for each ScenarioID.
    ############################################

    cash_flow_year_iter = pd.pivot_table(combined_cost_usage_iter, values='TotalCostAUDY', index=['Iteration', 'Year'],
                                         aggfunc=np.sum, columns='ScenarioID')

    return component_usage_by_year_iter, component_cost_by_year_iter, combined_cost_usage_iter, cash_flow_year_iter


def calculate_variance_contributions(input_factors, cost_result_name):
    num_table=20
    num_graphs=5
    title=None
    short_titles=False
    xlabel=None
    ylabel=None
    show_regression=True 
    show_r=True
    show_r2=False
                                     
    # This removes first any input factors with no variation
    filtered_factors = input_factors.loc[:, (input_factors.std() > 0)]

    correlation_table = filtered_factors.corr()

    correlation_table['variance'] = round(
        (correlation_table[cost_result_name] * correlation_table[cost_result_name]) * 100, 0)

    total_variance = correlation_table['variance'].sum()
    correlation_table['variance'] = correlation_table['variance'].fillna(0).astype(int)

    input_factor_range = input_factors.describe(percentiles=(0.1, 0.5, 0.9)).T.loc[:, ['10%', '50%', '90%']].round(2)
    input_factor_range['range'] = input_factor_range['10%'].astype(str) + ' - ' + input_factor_range['90%'].astype(str)

    correlation_table['range'] = input_factor_range['range']
    correlation_table['10th percentile'] = input_factor_range['10%']
    correlation_table['50th percentile'] = input_factor_range['50%']
    correlation_table['90th percentile'] = input_factor_range['90%']

    print('Total Variance sum (should be 2.0) = ', total_variance)

    print(correlation_table.sort_values(
        by='variance', ascending=False).loc[:, [cost_result_name, 'variance', 'range']].head(num_table))

    # Graph scatterplot:
    parameter_list = correlation_table.sort_values(by='variance', ascending=False).loc[:,
                     [cost_result_name, 'variance']].head(num_graphs + 1).index
    # print(parameter_list)
    parameter_description_list = zip(parameter_list, parameter_list)
    # print(parameter_description_list)

    for (parameter, label) in parameter_description_list:
        # print(parameter)
        # print(label)
        if parameter != cost_result_name:
            plt.scatter(input_factors[parameter], input_factors[cost_result_name], edgecolor='None')
            if title is None:
                if short_titles:
                    this_title = 'Correlation to ' + cost_result_name
                else:
                    this_title = 'Impact of ' + str(parameter) + ' on ' + cost_result_name
            plt.title(this_title)
            if xlabel is None:
                if short_titles:
                    this_xlabel = str(label)
                else:
                    this_xlabel = 'Input Factor: ' + str(label)
            else:
                this_xlabel = xlabel
            plt.xlabel(this_xlabel)
            if ylabel is None:
                if short_titles:
                    this_ylabel = cost_result_name
                else:
                    this_ylabel = 'Output Factor: ' + cost_result_name
            plt.ylabel(this_ylabel)

            if show_regression:
                slope, intercept, r_value, p_value, std_err = stats.linregress(input_factors[parameter],
                                                                               input_factors[cost_result_name])

                xmin, xmax = plt.xlim()
                ymin = slope * xmin + intercept
                ymax = slope * xmax + intercept

                plt.annotate('', xy=(xmin, ymin), xycoords='data', xytext=(xmax, ymax), textcoords='data',
                             arrowprops=dict(arrowstyle="-"))

                if show_r:
                    text = 'r = {0:.2f}'.format(r_value)
                if show_r2:
                    r2_value = r_value * r_value
                    text = text + '\nr$^2$ = {0:.2f}'.format(r2_value)
                plt.annotate(text, xy=(0.5, 0.5), fontsize=20, xycoords='figure fraction')

            plt.show()
