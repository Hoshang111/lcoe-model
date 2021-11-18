def daily_export_storage(dc_yield, export_limit, storage_capacity):

# A function to map storage and export in timeseries aligned with DC yield

ymd = [str(a) + '-' + str(b) + '-' + str(c) for a, b, c in zip(dc_yield.index.year, dc_yield.index.month,
                                                            dc_yield.index.day)]  # find year-month-day
ymd_unique = np.unique(ymd)  # unique year-month-day

Finding daily battery storage and export operations

export_daily_operations = []
battery_daily_operations = []
dc_yield_local = pd.DataFrame(data=dc_yield.values, index=dc_yield.index.tz_convert('Australia/Darwin'))


# We assume that whatever is generated is first used to charge batteries and the remaining is exported up to the export
# limit. This assumption can be easily switched : (i.e. export first up to export limit then charge the batteries)
for day in ymd_unique:
    dc_yield[str(day)]
    battery_dummy = np.zeros(24)
    i = 0
    while battery_dummy.sum() <= storage_capacity:
        battery_dummy[i] = dc_yield_local[str(day)].iloc[i]
        i += 1
        if i >= 24:
            break