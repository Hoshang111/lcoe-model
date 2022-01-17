import numpy as np
import math
from scipy.optimize import fsolve

Voc = 50.85
Isc = 13.46
Vmp = 43.10
Imp = 12.65
Rsh = Vmp / (0.2 * (Isc - Imp))
Rs = 0.3

def func(x):
    return [x[0] - x[1] * (math.exp(x[2] * Isc * Rs) - 1) - Isc * Rs / Rsh - Isc,
            x[0] - x[1] * (math.exp(x[2] * Voc) - 1) - Voc / Rsh,
            x[0] - x[1] * (math.exp(x[2] * (Vmp + Imp * Rs)) - 1) - (Voc + Isc * Rs) / Rsh - Imp ]

root = fsolve(func, [13.6, 1e-10, 2])
root
np.isclose(func(root),[0.0, 0.0, 0.0])