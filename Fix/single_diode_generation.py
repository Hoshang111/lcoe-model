import pvlib

results = pvlib.pvsystem.singlediode(photocurrent=14.4, saturation_current=2.661e-11, resistance_series=0.07,
                                     resistance_shunt=500, nNsVth=2.03)