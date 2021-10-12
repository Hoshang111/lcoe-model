# Code to spit out rack splits, technology agnostic
import pandas as pd

def get_racks(DCTotal, FieldNum, module, rack, field_area):
    rackfloat = DCTotal/(FieldNum*rack['Modules_per_rack']*module['STC'])
    rack_num_init = round(rackfloat)
    rack_interval = round(rackfloat*0.04)
    racknums, module_nums = get_racknums(rack_num_init, rack_interval)
    if rack['rack_type'] == 'SAT':
        gcr = module['A_c']*module_nums/field_area
    elif rack['rack_type'] == 'east_west':
        gcr = racknums*rack['Area']/field_area
    else:
        raise Exception('unrecognised rack type')

    return racknums, module_nums, gcr


def get_racknums(rack_num_init, rack_interval, rack):
    racknums = pd.Series(range(rack_num_init-5*rack_interval, rack_num_init+6*rack_interval, rack_interval))
    module_nums = racknums*rack['Modules_per_rack']
    return racknums, module_nums
