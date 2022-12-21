import sqlite3


def add_params(fileName, dc_total, num_zones, zone_area, temp_model, export_limit, storage_capacity, scheduled_price,
               discount_rate, num_racks, rack_interval_ratio):
    conn = sqlite3.connect(fileName)
    cur = conn.cursor()
    cur.execute(""" CREATE TABLE IF NOT EXISTS INPUTS (
                                        NAME TEXT NOT NULL,
                                        INPUT TEXT NOT NULL);""")
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('DC_total', dc_total))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('num_of_zones', num_zones))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('zone_area', zone_area))
    # cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('rack_interval_ratio', ?)", rack)
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('temp_model', temp_model))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('export_lim', export_limit))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('storage_capacity', storage_capacity))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('scheduled_price', scheduled_price))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('discount_rate', discount_rate))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('num_racks', num_racks))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('rack_interval_ratio', rack_interval_ratio))
    conn.commit()
    conn.close()


def add_scenario(fileName, scenario, scenario_num):
    conn = sqlite3.connect(fileName)
    cur = conn.cursor()
    cur.execute(""" CREATE TABLE IF NOT EXISTS INPUTS (
                                            NAME TEXT NOT NULL,
                                            INPUT TEXT NOT NULL);""")
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", (scenario_num, scenario))
    conn.commit()
    conn.close()
