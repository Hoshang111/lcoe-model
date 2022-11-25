import sqlite3



conn = sqlite3.connect("phill_test.db")
cur = conn.cursor()
cur.execute(""" CREATE TABLE IF NOT EXISTS INPUTS (
                                    NAME TEXT NOT NULL,
                                    INPUT TEXT NOT NULL);""")

cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('DC_total', 11000)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('num_of_zones', 720)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('zone_area', 140000)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('rack_interval_ratio', 0.01)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('temp_model', 'pvsyst')")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('export_lim', 4444444.44)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('storage_capacity', 50000000)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('scheduled_price', 0.00015)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('discount_rate', 0.07)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('year_sc1', 2028)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('mount_tech_sc1', 'MAV')")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('mod_tech_sc1', 'PERC')")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('set_racks1', 'None')")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('year_sc2', 2028)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('mount_tech_sc2', 'SAT')")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('mod_tech_sc2', 'PERC')")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('set_racks2', 'None')")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('num_iterations', 20)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('optimize_for', 'Yield')")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('optimize_target', 31)")
cur.execute("INSERT INTO INPUTS(NAME, INPUT) VALUES ('projectID', 'phill_test')")
conn.commit()
conn.close()