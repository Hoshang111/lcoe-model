# Use
Run montecarlo.py (can be done through a terminal using python3 montecarlo.py)

# Post-Report priorities
* time shift to centre of period (for sun angle etc.)
* Implement Bi-facial
* Update temperature coeffecients from first principles (Io based)
* Check effect of increased revenue
* Battery Storage
* Probabilistic Yield - incl soiling, mismatch, degradation, failures etc.
* 

# Sizing and Costing Model
SCOPTI (high-level sizing) -> Iterative Layout -> Yield + Costing -> LCOE Calc

### Yield
* Simple modelling of Mavs (1 east, 1 west-facing array, separate) **done**
* Benchmarking **done**
* Tracking Algorithms
* Tracking for different rows
* Future module database **done**
* *Thermal modelling and effects* **(Baran, Ruby)**
* Monte-Carlo Analysis
* Soiling
* Incident angle modifiers
* Inverters 
* Balance of system
* SAT Tracker claims
* Mis-match/Module Variation
* Failure/Downtime
  * Monte-Carlo input
  * Distinguish failures from degradation?
* Degradation **on hold**

### Cost
* Probabilistic Analysis - ID alternative methods **done**
* *Update costs with EPC input* **(Alwyn, Nathan)**
* Determine method for aligning future module costs with technologies **done**
* Add option to import from excel rather than airtable - faster for debugging **done**


### Interface
* *Align outputs with SCOPTI* **(Phill,Baran,Alwyn)**
* Iterative Layout / Equipment Specification **done**
* Battery operation and revenue generation

### Housekeeping
* *Sort out poetry conflicts* **(Hoshang)**
* Merge sizing and layout_optimizer
* Make scripts file
* Important files: phill_dni (create into function)
* Files to remove: parameter_extraction, system, Demo, Old Files

### Inputs
* Design point - accept multi-inputs

### TO RUN POETRY
* Create a new poetry interpreter (bottom right on PyCharm)
* This should be an existing interpreter and will allow you to install all poetry packages
* Once installed, ensure all packages are available in Python Packages, and run scripts to test if it worked.

### Alternate method to run POETRY if using Conda and pycharm on Windows 10
* Install poetry
** download install-poetry.py from https://install.python-poetry.org/
** run "python install-poetry.py" from an anaconda terminal window.
** If needed, add the path to the new poetry directory to your path (C:\Users\<username>\AppData\Roaming\Python\Scripts) 
* Create a python 3.10 conda environment, then activate it
** conda create <name> python=3.10
** conda activate <name>
* Change to the project directory and use poetry to install required packages
** cd <project directory path>
** poetry install
* In Pycharm, connect to the new conda environment
** "Add Interpreter" (bottom right on pycharm)
** Conda Environment
** Find location of python.exe in C:\Users\<username>\anaconda3\envs