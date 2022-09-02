"""
This is part 2 of the Monte-Carlo analysis process. This script will take system parameters
from a pickl and perform both yield and cost analysis using Monte-Carlo methods
"""

# %% Import
import random
import sys
sys.path.append( '..' )
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import Functions.simulation_functions as func
import Functions.mc_yield_functions as mc_func
from numpy.polynomial import Polynomial
from Functions.optimising_functions import form_new_data_tables, optimise_layout
from Functions.sizing_functions import get_airtable, get_npv
from Functions.cost_functions import calculate_scenarios_iterations, create_iteration_tables, \
     generate_parameters, calculate_variance_contributions, import_excel_data
import warnings
from Functions.mc_yield_functions import weather_sort, generate_mc_timeseries, get_yield_datatables
import _pickle as cpickle

# This suppresses a divide be zero warning message that occurs in pvlib tools.py.
warnings.filterwarnings(action='ignore',
                                message='divide by zero encountered in true_divide*')

 # %% ===========================================================
 # define scenarios

scenarios = [#'2024',
            #'2026',
            '2028']

 # %% ===========================================================
 # import scenario data from pickle and simulation parameters from csv

current_path = os.getcwd()
parent_path = os.path.dirname(current_path)
scenario_dict = {}

for key in scenarios:
    pickle_path = os.path.join(parent_path, 'OutputFigures', 'scenario_tables_' + key + '.p')
    scenario_dict[key] = cpickle.load(open(pickle_path, 'rb'))

csv_path = os.path.join(parent_path, 'OutputFigures', 'input_params.csv')
input_params = pd.read_csv(csv_path, header=0)

# Import airtable data previously saved
data_tables = import_excel_data('CostDatabaseSept2022.xlsx')

 # %% ===========================================================
 # convert dtypes in input_params, want to keep saving as csv so human readable but does not preserve dtypes

input_params['temp_model'] = input_params['temp_model'].astype('string')
input_params['storage_capacity'] = pd.to_numeric(input_params['storage_capacity'])
input_params['scheduled_price'] = pd.to_numeric(input_params['scheduled_price'])
input_params['export_lim'] = pd.to_numeric(input_params['export_lim'])
input_params['discount_rate'] = pd.to_numeric(input_params['discount_rate'])
input_params['zone_area'] = pd.to_numeric(input_params['zone_area'])
input_params['num_of_zones'] = pd.to_numeric(input_params['num_of_zones'])

discount_rate = input_params['discount_rate'].values[0]

yield_datatables = get_yield_datatables()

 # %% ===========================================================
# Monte Carlo for yield parameters
# first create ordered dict of weather and output
# need a weather file containing several years worth of data, no gaps allowed

mc_weather_name = 'Combined_Longi_570_Tracker-bifacial_FullTS_8m.csv'
mc_weather_file = mc_func.mc_weather_import(mc_weather_name)

# %%

weather_mc_dict = {}
loss_mc_dict = {}
combined_mc_dict = {}
for key in scenarios:
    results_dict = scenario_dict[key]
    weather_mc_dict[key], loss_mc_dict[key], combined_mc_dict[key] = \
        mc_func.run_yield_mc(results_dict, input_params, mc_weather_file, yield_datatables)

# %% ===========================================================
# Now calculate AC output (currently not used)



# %% ==========================================================
# Calculate LCOE and/or NPV for each iteration, and plot these for each optimum scenario.
# First generate a big table with index consisting of Iteration, Year, ScenarioID.


# %%
# Call Monte Carlo Cost analysis

# Do be deleted later - import occurs above.
data_tables = import_excel_data('CostDatabaseSept2022.xlsx')


# %%
def extract_scenario_tables(scenario_dict, analysis_year):
    mydata = scenario_dict[analysis_year]
    # print(mydata)
    output_list = []
    for item in mydata:
        # print(item)

        label = mydata[item][0]

        data = mydata[item][1]
        output_tuple = (data, label)
        output_list.append(output_tuple)

    return output_list

def extract_results_tables(scenario_dict, analysis_year):
    mydata = scenario_dict[analysis_year]
    output_list = []
    for item in mydata:
        output_tuple = (mydata[item][0], mydata[item][1], mydata[item][2], mydata[item][3], mydata[item][4])
        output_list.append(output_tuple)

    return output_list



# %%
for year in scenarios:
    analysis_year = int(year)
    scenario_tables = extract_scenario_tables(scenario_dict,year)


    # First generate data tables with the ScenarioID changed to something more intuitive
    new_data_tables = form_new_data_tables(data_tables, scenario_tables)

    # Create iteration data
    data_tables_iter = create_iteration_tables(new_data_tables, 100, iteration_start=0)

    # Calculate cost result
    outputs_iter = calculate_scenarios_iterations(data_tables_iter, year_start=analysis_year, analyse_years=30)
    component_usage_y_iter, component_cost_y_iter, total_cost_y_iter, cash_flow_by_year_iter = outputs_iter

    #  ==========================================================
    # Calculate LCOE and/or NPV for each iteration, and plot these for each optimum scenario.
    # First generate a big table with index consisting of Iteration, Year, ScenarioID.
    combined_scenario_data = pd.DataFrame()

    results_list = extract_results_tables(scenario_dict, year)



    font_size = 14
    rc = {'font.size': font_size, 'axes.labelsize': font_size, 'legend.fontsize': font_size,
          'axes.titlesize': font_size, 'xtick.labelsize': font_size, 'ytick.labelsize': font_size}
    plt.rcParams.update(**rc)
    plt.rc('font', weight='bold')

    # For label titles
    fontdict = {'fontsize': font_size, 'fontweight': 'bold'}

    for results in results_list:
        print('Length of results tuple is: ', len(results))
        scenario_id, scenario_tables_optimum, revenue_data, kWh_export_data, npv_output = results




        kWh_export_data.name = 'kWh'
        revenue_data.name = 'revenue'

        if len(cash_flow_by_year_iter[scenario_id])>0:
            scenario_data = cash_flow_by_year_iter[scenario_id]
            scenario_data.name = 'cost'

            scenario_data = scenario_data.reset_index().merge(
                kWh_export_data.reset_index(), how='left', on='Year').merge(
                revenue_data.reset_index(), how='left', on='Year')
            scenario_data['ScenarioID'] = scenario_id

            combined_scenario_data = pd.concat([combined_scenario_data, scenario_data])

            # Now discount the costs, etc
            for col_name in ['cost', 'kWh', 'revenue']:
                combined_scenario_data[col_name + '_disc'] = combined_scenario_data[col_name] / (1 + discount_rate) ** \
                                                             (combined_scenario_data['Year'] - install_year)

            # Create a new table that removes the year, adding all the discounted flows
            discounted_sum = pd.pivot_table(combined_scenario_data, index=['Iteration', 'ScenarioID'], values=['kWh_disc',
                                                                                                               'cost_disc',
                                                                                                               'revenue_disc'])

            # Now calculate LCOE and NPV

            discounted_sum['LCOE'] = discounted_sum['cost_disc'] / discounted_sum['kWh_disc']
            discounted_sum['NPV'] = discounted_sum['revenue_disc'] - discounted_sum['cost_disc']

            print(discounted_sum)

                # Plot the LCOE and NPV distributions. For each figure, show each scenario as its own distribution.
        print('up to 194')
        for parameter in ['LCOE', 'NPV']:
            data = discounted_sum[parameter].reset_index()
            print(data)
            data = pd.pivot_table(data, index='Iteration', values=parameter, columns='ScenarioID')
            data.plot.hist(bins=50, histtype='step', fontsize=8)
            fig_title = parameter + ' - ' + str(install_year)
            plt.title(fig_title)
            # savefig.save_figure(fig_title)
            current_path = os.getcwd()
            parent_path = os.path.dirname(current_path)
            file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
            plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
            plt.close()
            # plt.show()

    if analysis_year == 2024:
        analysis_list = [(['SAT PERC 2024','MAV PERC 2024'], 'SAT vs MAV 2024')]
    elif analysis_year == 2026:
        analysis_list = [(['SAT PERC 2026', 'MAV PERC 2026'], 'SAT vs MAV 2026')]
    elif analysis_year == 2028:
        analysis_list = [(['SAT HJTa 2028', 'MAV HJTa 2028'], 'SAT vs MAV 2028')]
    else:
        analysis_list == []
    for (scenarios, title) in analysis_list:
        print(scenarios)
        scenario_costs_iter = total_cost_y_iter[total_cost_y_iter['ScenarioID'].isin(scenarios)]
        scenario_costs_nominal = scenario_costs_iter[scenario_costs_iter['Iteration']==0]

        # scenario_costs_by_year = pd.pivot_table(scenario_costs_nominal, values='TotalCostAUDY',
        #                                              index=['Year','ScenarioID'], aggfunc=np.sum,
        #                                              columns=['CostCategory_ShortName']).reset_index()
        # print(scenario_costs_by_year)
        # scenario_costs_by_year.plot.bar(stacked=True,title='Total Costs by Year - ' + title)
        # plt.show()

        scenario_costs_total_category = pd.pivot_table(scenario_costs_nominal, values='TotalCostAUDY',
                                                     index=['ScenarioID'], aggfunc=np.sum,
                                                     columns=['CostCategory_ShortName'])
        scenario_costs_total_category.to_csv('temp_category_costs' + str(analysis_year) + '.csv')
        scenario_costs_total_category.plot.bar(stacked=True, title='Total Costs by Category - ' + title)
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', 'Scenario Costs')
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()


        scenario_costs_total_nodiscount = pd.pivot_table(scenario_costs_iter, values='TotalCostAUDY',
                                                         index=['Iteration'], aggfunc=np.sum,
                                                         columns=['ScenarioID'])
        scenario_costs_total_nodiscount.plot.hist(bins=50, histtype='step')
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', 'Scenario Costs No Discount')
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()

    if analysis_year==2024:
        comparison_list = [('MAV HJT 2024','SAT HJT 2024', 'MAV vs SAT HJT 2024'),
                            ('MAV HJT 2024','MAV PERC 2024', 'HJT vs PERC MAV 2024'),
                                               ]

    elif analysis_year == 2026:
        comparison_list = [('MAV PERC 2026', 'SAT PERC 2026', 'MAV vs SAT PERC 2026'),
                           ('MAV HJT 2026', 'MAV PERC 2026', 'HJT vs PERC MAV 2026')]
    elif analysis_year == 2028:
        comparison_list = [('MAV HJTa 2028', 'SAT HJTa 2028', 'MAV vs SAT HJT 2028'),
                           ('MAV HJTa 2028', 'MAV PERCa 2028', 'HJT vs PERC MAV 2028'),
                           ('SAT HJTa 2028', 'SAT PERCa 2028', 'HJT vs PERC SAT 2028')]

    for (scenario_1, scenario_2, savename) in comparison_list:

        for parameter in ['LCOE', 'NPV']:
            data = discounted_sum[parameter].reset_index()
            data = pd.pivot_table(data, index='Iteration', values = parameter, columns='ScenarioID')

            data['Difference'] = data[scenario_2] - data[scenario_1]
            data['Difference'].plot.hist(bins=50, histtype='step')
            fig_title = 'Difference in ' + parameter + ' ' + savename
            plt.title(fig_title)
            # savefig.save_figure(fig_title)
            current_path = os.getcwd()
            parent_path = os.path.dirname(current_path)
            file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
            plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
            plt.close()
            # plt.show()

        def generate_difference_factor(df, parameter, scenario_1, scenario_2, parameter_name):
            data = df[parameter].reset_index()
            data = pd.pivot_table(data, index = 'Iteration', values= parameter, columns = 'ScenarioID')
            data[parameter_name] = data[scenario_2] - data[scenario_1]
            return data[parameter_name]


        # Sensitivity analysis / regression analysis to determine key uncertainties affecting these.
        parameters = generate_parameters(data_tables_iter)
        parameters_flat = parameters.copy()
        parameters_flat.columns = [group + ' ' + str(ID) + ' ' + var for (group, ID, var) in parameters_flat.columns.values]

        factor = generate_difference_factor(discounted_sum, 'LCOE', scenario_1, scenario_2, 'LCOE_Difference')
        parameters_flat = parameters_flat.join(factor)

        factor = generate_difference_factor(discounted_sum, 'NPV', scenario_1, scenario_2, 'NPV_Difference')
        parameters_flat = parameters_flat.join(factor)


        baseline_year = 2024
        parameters_flat['Module Cost'] = parameters_flat['ComponentID 33 BaselineCost'] * parameters_flat[
            'ComponentID 33 AnnualMultiplier'] ** (analysis_year - baseline_year)
        parameters_flat['HJT Premium'] = parameters_flat['ComponentID 35 BaselineCost'] * parameters_flat[
            'ComponentID 35 AnnualMultiplier'] ** (analysis_year - baseline_year)
        parameters_flat['TOPCon Premium'] = parameters_flat['ComponentID 34 BaselineCost'] * parameters_flat[
            'ComponentID 34 AnnualMultiplier'] ** (analysis_year - baseline_year)
        # parameters_flat['Onsite Labour Index'] = parameters_flat['ComponentID 45 BaselineCost'] * parameters_flat[
        #     'ComponentID 45 AnnualMultiplier'] ** (analysis_year - baseline_year)
        parameters_flat['Onsite Labour Index'] = parameters_flat[
            'ComponentID 45 AnnualMultiplier'] ** (analysis_year - baseline_year)


        parameters_flat = parameters_flat.rename(columns={
            'ComponentID 45 AnnualMultiplier': 'Onsite Labour Annual Multiplier',
            'ComponentID 33 AnnualMultiplier': 'Module cost Annual Multiplier',
            'SystemComponentID 163 UsageAnnualMultiplier': 'MAV Hardware Annual Multiplier',
            'SystemComponentID 164 UsageAnnualMultiplier': 'MAV Labour Annual Multiplier'
        })


        calculate_variance_contributions(parameters_flat, 'LCOE_Difference', savename=savename)

        x = parameters_flat['Module Cost']
        y = parameters_flat['Onsite Labour Index']
        z = parameters_flat['LCOE_Difference']
        title = 'Impact on LCOE difference'
        p1_description = 'Module Cost'
        p2_description = 'Labour Index'
        map = 'seismic'
        colorbartitle = 'Delta LCOE'
        fig, (ax0, ax1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [25, 1]})

        vmax = z.abs().max()
        vmin = -vmax

        scatterplot = ax0.scatter(x, y, c=z, cmap=map, vmin=vmin, vmax=vmax, s=None)
        plt.colorbar(scatterplot, cax=ax1)
        ax1.set_title(colorbartitle)

        ax0.set_xlabel(p1_description)
        ax0.set_ylabel(p2_description)
        ax0.set_title(title)

        fig_title = "Delta LCOE - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()

        x = parameters_flat['Module Cost']
        y = parameters_flat['Onsite Labour Index']
        z = parameters_flat['NPV_Difference']
        title = 'Impact on NPV difference'
        p1_description = 'Module Cost'
        p2_description = 'Labour Index'
        map = 'seismic_r'
        colorbartitle = 'Delta NPV'
        fig, (ax0, ax1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [25, 1]})

        vmax = z.abs().max()
        vmin = -vmax

        scatterplot = ax0.scatter(x, y, c=z, cmap=map, vmin=vmin, vmax=vmax, s=None)
        plt.colorbar(scatterplot, cax=ax1)
        ax1.set_title(colorbartitle)

        ax0.set_xlabel(p1_description)
        ax0.set_ylabel(p2_description)
        ax0.set_title(title)

        fig_title = "Delta NPV - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()

        x = parameters_flat['Module Cost']
        y = parameters_flat['MAV Hardware Annual Multiplier']
        z = parameters_flat['NPV_Difference']
        title = 'Impact on NPV difference'
        p1_description = 'Module Cost'
        p2_description = 'MAV Hardware Multiplier'
        map = 'seismic_r'
        colorbartitle = 'Delta NPV'
        fig, (ax0, ax1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [25, 1]})

        vmax = z.abs().max()
        vmin = -vmax

        scatterplot = ax0.scatter(x, y, c=z, cmap=map, vmin=vmin, vmax=vmax, s=None)
        plt.colorbar(scatterplot, cax=ax1)
        ax1.set_title(colorbartitle)

        ax0.set_xlabel(p1_description)
        ax0.set_ylabel(p2_description)
        ax0.set_title(title)

        fig_title = "Delta NPV hardware - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()

        x = parameters_flat['Module Cost']
        y = parameters_flat['MAV Labour Annual Multiplier']
        z = parameters_flat['NPV_Difference']
        title = 'Impact on NPV difference'
        p1_description = 'Module Cost'
        p2_description = 'MAV Labour Multiplier'
        map = 'seismic_r'
        colorbartitle = 'Delta NPV'
        fig, (ax0, ax1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [25, 1]})

        vmax = z.abs().max()
        vmin = -vmax

        scatterplot = ax0.scatter(x, y, c=z, cmap=map, vmin=vmin, vmax=vmax, s=None)
        plt.colorbar(scatterplot, cax=ax1)
        ax1.set_title(colorbartitle)

        ax0.set_xlabel(p1_description)
        ax0.set_ylabel(p2_description)
        ax0.set_title(title)

        fig_title = "Delta NPV labour - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        # plt.show()

        x = parameters_flat['MAV Labour Annual Multiplier'].astype(str).astype(float)
        y = parameters_flat['NPV_Difference'].astype(str).astype(float)
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.scatter(x, y)
        ax.set_xlabel('MAV Labour Multiplier', **fontdict)
        ax.set_ylabel('Difference in NPV', **fontdict)
        ax.set_title('Regression for MAV Labour')

        c1, c0 = Polynomial.fit(x, y, 1)
        correlation_matrix = np.corrcoef(x.values, y.values)
        correlation_xy = correlation_matrix[0, 1]
        r_squared = correlation_xy ** 2

        ax.plot(x, x * c1 + c0, linewidth=3, color='C1')
        # ax.set_ylim(0,1.25)
        # ax.set_xlim(0,1.25)
        plot_text = 'r = %.2f' % correlation_xy
        xt = (x.mean() - x.min()) / 2 + x.min()
        yt = (y.mean() / 2 - y.min()) / 2 + y.min()
        plt.text(xt, yt, plot_text, fontsize=25)

        fig_title = "Regression NPV labour - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()

        x = parameters_flat['MAV Hardware Annual Multiplier'].astype(str).astype(float)
        y = parameters_flat['NPV_Difference'].astype(str).astype(float)
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.scatter(x, y)
        ax.set_xlabel('MAV Hardware Multiplier', **fontdict)
        ax.set_ylabel('Difference in NPV', **fontdict)
        ax.set_title('Regression for MAV Hardware')

        c1, c0 = Polynomial.fit(x, y, 1)
        correlation_matrix = np.corrcoef(x.values, y.values)
        correlation_xy = correlation_matrix[0, 1]
        r_squared = correlation_xy ** 2

        ax.plot(x, x * c1 + c0, linewidth=3, color='C1')
        # ax.set_ylim(0,1.25)
        # ax.set_xlim(0,1.25)
        plot_text = 'r = %.2f' % correlation_xy
        xt = (x.mean()-x.min())/2+x.min()
        yt = (y.mean()-y.min())/2+y.min()
        plt.text(xt, yt, plot_text, fontsize=25)

        fig_title = "Regression NPV hardware - " + savename
        current_path = os.getcwd()
        parent_path = os.path.dirname(current_path)
        file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
        plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
        plt.close()


# %%
#print(results_SAT_PERC_2024)

graph_data = pd.DataFrame(columns=['Year','NPV','Label'], index=[*range(0,1)])
i = 0

for results in results_list:
    scenario_id, scenario_tables_optimum, revenue_data, kWh_export_data, npv_output = results



for (year, label, results) in [
#    (2024, 'MAV PERC', results_MAV_PERC_2024),
#    (2026, 'MAV PERC', results_MAV_PERC_2026),
#    (2028, 'MAV PERC', results_MAV_PERC_2028),
#    (2024, 'SAT PERC', results_SAT_PERC_2024),
#    (2026, 'SAT PERC', results_SAT_PERC_2026),
#    (2028, 'SAT PERC', results_SAT_PERC_2028),
#    (2024, 'MAV PERCa', results_MAV_PERCa_2024),
#    (2026, 'MAV PERCa', results_MAV_PERCa_2026),
    (2028, 'MAV PERCa', results_MAV_PERCa_2028),
#    (2024, 'SAT PERCa', results_SAT_PERCa_2024),
#    (2026, 'SAT PERCa', results_SAT_PERCa_2026),
    (2028, 'SAT PERCa', results_SAT_PERCa_2028),
#    (2024, 'MAV TOP', results_MAV_TOP_2024),
#    (2026, 'MAV TOP', results_MAV_TOP_2026),
#    (2028, 'MAV TOP', results_MAV_TOP_2028),
#    (2024, 'SAT TOP', results_SAT_TOP_2024),
#    (2026, 'SAT TOP', results_SAT_TOP_2026),
#    (2028, 'SAT TOP', results_SAT_TOP_2028),
#    (2024, 'MAV TOPa', results_MAV_TOPa_2024),
#    (2026, 'MAV TOPa', results_MAV_TOPa_2026),
    (2028, 'MAV TOPa', results_MAV_TOPa_2028),
#    (2024, 'SAT TOPa', results_SAT_TOPa_2024),
#    (2026, 'SAT TOPa', results_SAT_TOPa_2026),
    (2028, 'SAT TOPa', results_SAT_TOPa_2028),
#    (2024, 'MAV HJT', results_MAV_HJT_2024),
#    (2026, 'MAV HJT', results_MAV_HJT_2026),
#    (2028, 'MAV HJT', results_MAV_HJT_2028),
#    (2024, 'SAT HJT', results_SAT_HJT_2024),
#    (2026, 'SAT HJT', results_SAT_HJT_2026),
#    (2028, 'SAT HJT', results_SAT_HJT_2028),
#    (2024, 'MAV HJTa', results_MAV_HJTa_2024),
#    (2026, 'MAV HJTa', results_MAV_HJTa_2026),
    (2028, 'MAV HJTa', results_MAV_HJTa_2028),
#    (2024, 'SAT HJTa', results_SAT_HJTa_2024),
#    (2026, 'SAT HJTa', results_SAT_HJTa_2026),
    (2028, 'SAT HJTa', results_SAT_HJTa_2028)
    ]:
    SCENARIO_LABEL, scenario_tables_optimum, revenue, kWh_export, npv_output = results
    graph_data.loc[i,'Year'] = year
    graph_data.loc[i, 'NPV'] = npv_output / 1000000
    graph_data.loc[i, 'Label'] = label
    i += 1


print(graph_data)
graph_data = graph_data.pivot(columns='Label', values='NPV',index='Year')
print(graph_data)
graph_data.plot.line()
plt.gca().legend(bbox_to_anchor=(1.1, 1.05))
plt.gca().set_title('NPV AUD Million')
# plt.show()

for year in [2028]:
    graph_data_year = graph_data.loc[year,:].T
    graph_data_year.plot.bar()
    plt.gca().set_title('NPV for ' + str(year) + ' installation')
    plt.gca().set_xlabel('Scenario')
    plt.gca().set_ylabel('AUD Million')
    fig_title = "NPV - " + str(year)
    current_path = os.getcwd()
    parent_path = os.path.dirname(current_path)
    file_name = os.path.join(parent_path, 'OutputFigures', fig_title)
    plt.savefig(file_name, format='png', dpi=300, bbox_inches='tight')
    plt.close()



