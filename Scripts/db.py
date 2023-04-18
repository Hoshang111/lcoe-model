import sqlite3


def add_params(fileName, inputs):
    conn = sqlite3.connect(fileName)
    cur = conn.cursor()
    cur.execute(""" CREATE TABLE IF NOT EXISTS INPUTS (
                                        NAME TEXT NOT NULL,
                                        INPUT TEXT NOT NULL);""")
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('DC_total', inputs[0]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('num_of_zones', inputs[1]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('rack_interval_ratio', inputs[2]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('zone_area', inputs[3]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('temp_model', inputs[4]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('export_lim', inputs[5]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('storage_capacity', inputs[6]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('scheduled_price', inputs[7]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('discount_rate', inputs[8]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('num_racks', inputs[9]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('start_year', inputs[10]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('revenue_year', inputs[11]))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('end_year', inputs[12]))
    conn.commit()
    conn.close()


def add_scenario(fileName, year, mounting_tech, module_tech, set_racks):
    conn = sqlite3.connect(fileName)
    cur = conn.cursor()
    cur.execute(""" CREATE TABLE IF NOT EXISTS INPUTS (
                                            NAME TEXT NOT NULL,
                                            INPUT TEXT NOT NULL);""")
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('year', year))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('mounting_tech', mounting_tech))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('module_tech', module_tech))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ('set_racks', set_racks))
    conn.commit()
    conn.close()


def add_opt_targets(fileName, opt_for, opt_target):
    conn = sqlite3.connect(fileName)
    cur = conn.cursor()
    cur.execute(""" CREATE TABLE IF NOT EXISTS INPUTS (
                                                NAME TEXT NOT NULL,
                                                INPUT TEXT NOT NULL);""")
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ("opt_for", opt_for))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ("opt_target", opt_target))
    cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES (?, ?)", ("projectID", fileName))
    conn.commit()
    conn.close()
