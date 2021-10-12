# Code to spit out rack splits, technology agnostic
import pandas as pd

def get_racks(DCTotal, FieldNum, module, rack):
    rackfloat = DCTotal/(FieldNum*rack['Modules_per_rack']*module['STC'])
    rack_num_init = round(rackfloat)
    rack_interval = round(rackfloat*0.04)
    racknums = get_racknums(rack_num_init, rack_interval)
    return racknums


def get_racknums(rack_num_init, rack_interval):
    racknums = pd.Series(range(rack_num_init-5*rack_interval, rack_num_init+6*rack_interval, rack_interval))
    return racknums
