import matplotlib
import matplotlib.pyplot as plt
import numpy as np

#%% Plot features
font_size = 25
rc = {'font.size': font_size, 'axes.labelsize': font_size, 'legend.fontsize': font_size,
      'axes.titlesize': font_size, 'xtick.labelsize': font_size, 'ytick.labelsize': font_size}
plt.rcParams.update(**rc)
plt.rc('font', weight='bold')
# For label titles
fontdict = {'fontsize': font_size, 'fontweight': 'bold'}

def weather_nofit(ground, satellite, fig_name):
    """"""
    x = satellite
    y = ground
    fig, ax = plt.subplots(figsize=(25, 20))
    ax.scatter(x, y)
    ax.set_xlabel('Satellite', **fontdict)
    ax.set_ylabel('Ground', **fontdict)
    ax.set_title(fig_name)

    ax.axline((0, 0), slope=1, label='m=1', linewidth=3, color='orange')
    # plt.show()
    save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/" + fig_name
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return

def weather_overlay(initial_data, masked_data, calc_data, fig_name):
    """"""

    x = calc_data
    y = initial_data
    z = masked_data

    fig, ax = plt.subplots(figsize=(25, 20))
    ax.scatter(x, y, color='blue', label='initial')
    ax.scatter(x, z, color='red', label='masked')
    ax.set_xlabel('Calculated', **fontdict)
    ax.set_ylabel('Measured', **fontdict)
    ax.set_title(fig_name)
    ax.axline((0, 0), slope=1, label='m=1', linewidth=3, color='orange')

    save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/" + fig_name
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return

def weather_scatter(ground, satellite, fig_name):
    """"""

    x = satellite
    y = ground
    fig, ax = plt.subplots(figsize=(25, 20))
    ax.scatter(x, y)
    ax.set_xlabel('Ground', **fontdict)
    ax.set_ylabel('Satellite', **fontdict)
    ax.set_title(fig_name)

    # Best fit line - edit changed to second order
    # m, b = np.polyfit(x, y, 1)
    if not x.empty:
        c2, c1, c0 = np.polyfit(x, y, 2)
        correlation_matrix = np.corrcoef(x.values, y.values)
        correlation_xy = correlation_matrix[0, 1]
        r_squared = correlation_xy ** 2
        plot_text = 'R-squared = %.2f' % r_squared
        plt.text(0.3, 0.3, plot_text, fontsize=25)
    else:
        c2, c1, c0 = [0, 0, 0]

    ax.axline((0, 0), slope=1, label='m=1', linewidth=3, color='orange')

    # plt.show()
    save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/" + fig_name
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return c0, c1, c2

def weather_correction(ground0, satellite0, label):
    """"""

    idx = np.isfinite(ground0) & np.isfinite(satellite0)
    ground = ground0[idx]
    satellite = satellite0[idx]
    fig_name = 'Uncorrected_' + '_' + label
    c0, c1, c2 = weather_scatter(ground, satellite, fig_name)

    satellite_dummy = satellite ** 2 * c2 + satellite * c1 + c0
    satellite_corr = satellite_dummy.clip(lower=0, upper=None)

    # re-plot with corrected data
    fig_name = 'Corrected_' + '_' + label
    c0_a, c1_a, c2_a = weather_scatter(ground, satellite_corr, fig_name)

    return c0, c1, c2, satellite_corr