import pvlib

results = pvlib.pvsystem.singlediode(photocurrent=13.8135, saturation_current=1.25e-10, resistance_series=0.13,

                                     resistance_shunt=350, nNsVth=2.03)