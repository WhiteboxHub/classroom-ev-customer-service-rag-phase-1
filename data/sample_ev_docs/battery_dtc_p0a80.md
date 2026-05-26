# Battery Diagnostic – DTC P0A80

**Vehicle Model:** XYZ Model S  
**Diagnostic Category:** battery  
**DTC Code:** P0A80  

## Description
P0A80 indicates **Replace Hybrid/EV Battery Pack** – high-voltage battery module performance deviation detected by the BMS.

## Troubleshooting Steps

### Step 1: Confirm DTC and freeze frame
1. Read DTC with OEM scan tool; verify P0A80 is current (not history only).
2. Record SOC, cell delta voltage, and max cell temperature from freeze frame.

### Step 2: Isolation and contactor check
1. Perform HV isolation test per workshop manual section HV-12.
2. Verify main contactors open/close within specification (resistance < 5 mΩ).

### Step 3: Cell imbalance assessment
- If max cell delta > 150 mV at rest: schedule battery module balance procedure BM-07.
- If delta > 300 mV: do not fast-charge; arrange battery engineering review.

### Step 4: Customer communication
Inform customer that P0A80 requires dealer inspection; do not clear DTC without completed repair validation drive cycle.

## Related Codes
P0A7F (battery weak), P1B00 (thermal derate active)
