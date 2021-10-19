# Code to spit out rack splits, technology agnostic
import pandas as pd

def get_racks(DCTotal,
              FieldNum,
              module,
              rack,
              field_area,
              interval_ratio):
    """
    Function to vary the number of racks per field
    :param DCTotal:
    :param FieldNum:
    :param module:
    :param rack:
    :param field_area:
    :param interval_ratio:
    :return:
    """

    rackfloat = DCTotal/(FieldNum*rack['Modules_per_rack']*module['STC'])
    rack_num_init = round(rackfloat)
    rack_interval = round(rackfloat*interval_ratio)
    if rack_interval < 1:
        rack_interval = 1
    racknums = pd.Series(range(rack_num_init - 5 * rack_interval, rack_num_init + 6 * rack_interval, rack_interval))
    module_nums = racknums * rack['Modules_per_rack']
    if rack['rack_type'] == 'SAT':
        gcr = module['A_c']*module_nums/field_area
    elif rack['rack_type'] == 'east_west':
        gcr = racknums*rack['Area']/field_area
    else:
        raise Exception('unrecognised rack type')

    return racknums, module_nums, gcr

def get_revenue(Yieldseries,
                Trans_limit,
                price_schedule,
                storage_capacity):

    """
    Function to determine revenue generation from yield,
    At present very simple, future iterations will need storage
    capacity and operation
    :param Yieldseries:
    :param Trans_limit:
    :param price_schedule:
    :return:
    """

    Fixed_Price = 0.4
    Direct_Export = Yieldseries.clip(lower=None, upper=TRANSlimit)
    Store_Avail = Yieldseries-Direct_Export
    Daily_store_pot = Store_Avail.groupby(Store_Avail.index.day).sum()
    Daily_store = Daily_store_pot.clip(lower=None, upper=storage_capacity)
    Direct_Revenue = Direct_Export*Fixed_Price
    Store_Revenue = Daily_store*Fixed_Price*0.85
    Yearly_direct = Direct_Revenue.groupby(Direct_Revenue.index.year).sum()
    Yearly_storage = Store_Revenue.groupby(Store_Revenue.index.year).sum()
    Yearly_total = Yearly_direct+Yearly_storage

    return Yearly_direct, Yearly_storage, Yearly_total

def get_npv(yearly_costs,
            yearly_revenue,
            discount_rate):
    """
    Function to determine the npv from a time series (yearly)
    of costs and revenue
    :param yearly_costs:
    :param yearly_revenue:
    :return:
    """
    net_cashflow = yearly_revenue-yearly_costs

    Yearoffset = pd.Series(range(0, len(net_cashflow)))
    Yearoffset.index = net_cashflow.index

    YearlyFactor = 1 / (1 + discount_rate) ** Yearoffset
    YearlyNPV = net_cashflow.mul(YearlyFactor, axis=0)

    NPV = YearlyNPV.sum(axis=0)

    return NPV, YearlyNPV



