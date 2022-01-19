import pvlib

results = pvlib.pvsystem.singlediode(photocurrent=13.469, saturation_current=6e-11, resistance_series=0.23,
                                     resistance_shunt=250, nNsVth=1.9)