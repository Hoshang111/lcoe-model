import pvlib

results = pvlib.pvsystem.singlediode(photocurrent=13.67, saturation_current=7.5e-12, resistance_series=0.2,
                                     resistance_shunt=500, nNsVth=1.925)