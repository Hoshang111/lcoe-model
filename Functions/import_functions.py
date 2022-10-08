import os, sys
import numpy as np
import pandas as pd
from pathlib import Path
import pvlib

# %% ==================================================
# Module import

def import_module(pan_file_id):

    cwd = os.getcwd()
    parent = Path(cwd).parent
    pvtools_path = os.path.join(parent, 'pvsyst_tools')
    sys.path.append(parent)
    sys.path.append(pvtools_path)
    import pvsyst

    pan_file_path = os.path.join(cwd, 'Data', "SystemData", pan_file_id)
    module_parameters = pvsyst.pan_to_module_param(pan_file_path)

    return module_parameters

