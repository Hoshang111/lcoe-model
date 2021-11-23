import pvlib

params = pvlib.pvsystem.singlediode(photocurrent=13.6, saturation_current=9.94e-12,
                                    resistance_series=0.2, resistance_shunt=500,
                                    nNsVth=1.9)

print(params)