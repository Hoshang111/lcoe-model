# Use
Run montecarlo.py (can be done through a terminal using python3 montecarlo.py)

# Post-Report priorities
* time shift to centre of period (for sun angle etc.)
* Implement Bi-facial
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

### Inputs
* Design point - accept multi-inputs

