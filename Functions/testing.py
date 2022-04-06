import pandas as pd

import numpy as np
import calendar
#
# zero_data = np.zeros(shape=(100, 10))
# yield_series = pd.DataFrame(zero_data, columns=['2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009'])
#
# degraded_series = yield_series
#
# yield_series += 1000
#
# degradation_rate = 2
#
# first_year_degradation = 10
#
# yearly_degradation = yield_series[yield_series.columns[0]]*(degradation_rate/100)
#
#
# for i in yield_series.columns:
#     if i == yield_series.columns[0]:
#         degraded_series.iloc[:, yield_series.columns.get_loc("{0}".format(i))] = yield_series["{0}".format(i)]
#
#     elif i == yield_series.columns[1]:
#         degraded_series.iloc[:, yield_series.columns.get_loc("{0}".format(i))] = yield_series["{0}".format(i)]*\
#                                                                                  (1-first_year_degradation/100)
#
#     else:
#         degraded_series.iloc[:, yield_series.columns.get_loc("{0}".format(i))] = yield_series["{0}".format(i)]*\
#                                                                                  (1-first_year_degradation/100) - \
#                                                                                  (yield_series.columns.get_loc("{0}".format(i))
#                                                                                   - 1)*yearly_degradation


# testframe = {'Name': ['Tom', 'nick', 'krish', 'jack'],
#              'Age': [20, 21, 19, 18]}
#
# testframe1 = pd.DataFrame(testframe)
#
# print(testframe1.index)
# # print(testframe1[testframe1.columns[0]])
#
# # for i in testframe1.columns:
# #     if i == testframe1.columns[0]:
# #         print(testframe1[[0]])
#
#
# # class Iteration:
# #
# #     def __init__(self, num1, num2):
# #         self.num1 = num1
# #         self.num2 = num2
# #
# #     def increment1(self):
# #         self.num1 += 1
# #         print(self.num1)
# #
# #     def increment2(self):
# #         self.num1 += 2
# #         return self.num1
# #
# #
# # maths = Iteration(5, 15)
# #
# # test1 = maths.increment2()
# #
# # print(test1)
# # , columns=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
# zero_data = np.zeros(shape=(100, 10))
# yield_series = pd.DataFrame(zero_data, columns=['2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009'])
# yield_series += 1000
# def apply_degradation(yield_series, degradation_rate, first_year_degradation):
#     """
#
#     :param yield_series:
#     :param degradation_rate:
#     :param first_year_degradation:
#     :return: degraded_series:
#     """
#
# # If year == first year in dataframe, no effect
# # if year == second year, apply first_year_degradation
# # all subsequent years, apply degradation_rate
#     degraded_series = yield_series.copy()
#     yearly_degradation = yield_series[yield_series.columns[0]]*degradation_rate/100
#
#     for i in yield_series.columns:
#         if i == yield_series.columns[0]:
#             degraded_series.iloc[:, yield_series.columns.get_loc("{0}".format(i))] = yield_series["{0}".format(i)]
#
#         elif i == yield_series.columns[1]:
#             degraded_series.iloc[:, yield_series.columns.get_loc("{0}".format(i))] = yield_series["{0}".format(i)]*\
#                                                                                      (1-first_year_degradation/100)
#
#         else:
#             degraded_series.iloc[:, yield_series.columns.get_loc("{0}".format(i))] = yield_series["{0}".format(i)]*\
#                                                                                      (1-first_year_degradation/100) - \
#                                                                                      (yield_series.columns.get_loc("{0}".format(i))
#                                                                                       - 1)*yearly_degradation
#
#     return degraded_series
#
# result = apply_degradation(yield_series, 2, 10)

def align_years(yield_series, cost_series):

    years=np.arange(cost_series.index[0], cost_series.index[-1])
    aligned_years=pd.concat([yield_series]*len(cost_series.index))
    myindex=(np.repeat(years,8784).astype(str)+aligned_years.index)
    aligned_years.index=myindex
    for year in np.arange(1980,2020):
        if ~calendar.isleap(year):
            aligned_years.drop(index=str(year)+'02-29',inplace=True)
    aligned_years.index=pd.to_datetime(aligned_years.index,format='%Y%m-%d-%h')
    return aligned_years
