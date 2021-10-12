# Initial Guess at total DC power
DCTotal = 1e10

# Number of Fields, used to determine export limits etc.
FieldNum = 500

# Area for Field in m2
FieldArea = 200000

suncable_modules = pd.read_csv(os.path.join('Data', 'SystemData', 'Suncable_module_database.csv'), index_col=0, skiprows=[1,2]).T

module = suncable_modules['Jinko_JKM575M_7RL4_TV_PRE']

# Import Rack Data from database
suncable_racks = pd.read_csv(os.path.join('Data', 'SystemData', 'Suncable_rack_database.csv'), index_col=0, skiprows=[1]).T

rack = suncable_racks['SAT_1']

racknums = sizing.get_racks(DCTotal, FieldNum, module, rack)
