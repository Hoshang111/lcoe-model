# File to build system parameters for pvlib
import pandas as pd
import pvlib

def system_build(rack_type, gcr):
    if rack_type = 'SAT':
        system = SAT_build(rack_type, gcr)
    else if rack_type = 'east_west':
        system = EW_build(rack_type)





def SAT_build():
    for i in range(gcr.size)
        mount = pvlib.pvsystem. \
            SingleAxisTrackerMount(axis_tilt=0, axis_azimuth=0,
                                   max_angle=90, backtrack=True, gcr=gcr[i], cross_axis_tilt=0,
                                   racking_model='open_rack', module_height=2)
        arrays[i] = pvlib.pvsystem.Array(mount=mount, module_parameters=module,
                             temperature_model_parameters=temperature_model_parameters)



def EW_build():

