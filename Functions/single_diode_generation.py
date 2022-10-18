import pvlib

results = pvlib.pvsystem.singlediode(photocurrent=13.6, saturation_current=1.5e-10, resistance_series=0.15,
                                     resistance_shunt=350, nNsVth=2.02)