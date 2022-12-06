import pvlib

results = pvlib.pvsystem.singlediode(photocurrent=14.35, saturation_current=3.45e-11, resistance_series=0.073,
                                     resistance_shunt=500, nNsVth=2.03)