import pvlib

params = pvlib.pvsystem.singlediode(photocurrent=13.64, saturation_current=6.29e-12,
                                    resistance_series=0.2, resistance_shunt=500,
                                    nNsVth=2.1)

print(params)