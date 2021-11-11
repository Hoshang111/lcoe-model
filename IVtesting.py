import pvlib

params = pvlib.pvsystem.singlediode(photocurrent=13.6, saturation_current=6.29e-12,
                                    resistance_series=0.18, resistance_shunt=500,
                                    nNsVth=1.9)

print(params)