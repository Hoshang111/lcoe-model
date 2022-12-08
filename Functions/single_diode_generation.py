import pvlib

results = pvlib.pvsystem.singlediode(photocurrent=13.6, saturation_current=1.63e-10, resistance_series=0.15,
                                     resistance_shunt=400, nNsVth=5)