import matplotlib
import matplotlib.pyplot as plt

def weather_nofit(ground, satellite, fig_name):
    """"""
    x = satellite
    y = ground
    fig, ax = plt.subplots(figsize=(25, 20))
    ax.scatter(x, y)
    ax.set_xlabel('Satellite', **fontdict)
    ax.set_ylabel('Ground', **fontdict)
    ax.set_title(fig_name)

    # plt.show()
    save_path = "C:\\Users\phill\Documents\Bangladesh Application\weather_data/" + fig_name
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return