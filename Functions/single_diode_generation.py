import pvlib

results = pvlib.pvsystem.singlediode(photocurrent=18.458, saturation_current=7.3e-11, resistance_series=0.155,
                                     resistance_shunt=350, nNsVth=1.748)