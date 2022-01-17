''' Tests single IV current'''
import pvlib

params = pvlib.pvsystem.singlediode(photocurrent=13.65, saturation_current=8.61e-12,
                                    resistance_series=0.2, resistance_shunt=500,
                                    nNsVth=1.925)
print(params)
