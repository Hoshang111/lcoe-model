import os, sys
import numpy as np
import pandas as pd
from pathlib import Path
import pvlib
import pvtools.pvsyst as pvsyst

# %% ==================================================
# Module import

def import_module(pan_file_id):

    cwd = os.getcwd()
    print(cwd)
    parent = Path(cwd).parent
    pvtools_path = os.path.join(parent, 'pvsyst_tools')
    sys.path.append(parent)
    sys.path.append(pvtools_path)


    pan_file_path = os.path.join(cwd, 'Data', "SystemData", pan_file_id)
    module_parameters = pvsyst.pan_to_module_param(pan_file_path)

    return module_parameters

import_module("Jinko_JKM575M-7RL4-TV_PRE.PAN")