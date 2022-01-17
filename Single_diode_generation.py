import pvlib

results = pvlib.pvsystem.singlediode(photocurrent=13.464, saturation_current=6e-11, resistance_series=0.4,
                                     resistance_shunt=500, nNsVth=2)