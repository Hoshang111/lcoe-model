import matplotlib
import matplotlib.pyplot as plt

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

    ax.axline((0,0), slope=1, label='m=1')
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
    ax.scatter(x, y, colour='blue', label='initial')
    ax.scatter(x, z, colour='red', label='masked')
    ax.set_xlabel('Calculated', **fontdict)
    ax.set_ylabel('Measured', **fontdict)
    ax.set_title(fig_name)

    save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/" + fig_name
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return