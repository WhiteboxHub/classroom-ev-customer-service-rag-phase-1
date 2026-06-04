# Battery State of Health (SoH) Diagnostic Procedure
**Document:** SOH-DIAG-002 | **Version:** 2.1 | **Platform:** EV-3000, EV-5000, EV-7000

## Purpose
This procedure defines the standard method for assessing EV battery State of Health (SoH) for warranty determination, service planning, and fleet management.

## Prerequisites
- Approved OBD-II interface (XYZ DiagTool Pro v2.0+)
- Vehicle SoC: 15-25% (test will fail if SoC >40%)
- Ambient temperature: 10-35°C
- Vehicle must not have been driven in the last 30 minutes

## Procedure Steps

### Step 1: Pre-Test Inspection
1. Check for active DTCs — clear non-critical DTCs before test
2. Verify coolant level is at MIN line or above
3. Confirm firmware version is 4.0.0 or later
4. Ensure vehicle is plugged into AC Level 2 EVSE for the test duration

### Step 2: Initiate SoH Test
1. Connect DiagTool Pro and navigate to: Battery > Health Assessment > Start SoH Test
2. Confirm pre-conditions are met (green checkmarks on all pre-test items)
3. Press **Start Test** — test runs automatically for 35-50 minutes

### Step 3: Results Interpretation
After test completion, review:
- **Measured Capacity (kWh):** Actual available capacity
- **SoH Percentage:** Measured / Nominal × 100
- **Cell Spread:** Max - Min cell voltage
- **Temperature Delta:** Max - Min cell temperature during test
- **Cycle Count:** Total charge cycles (from BMS lifetime log)

### Step 4: Documentation
1. Export full test report: Test Complete > Export PDF
2. Log document ID and test date in service management system
3. If SoH < 70%, initiate warranty claim process

## Expected Values by Mileage
| Mileage (miles) | Expected SoH Range |
|-----------------|--------------------|
| 0 - 20,000 | 95-100% |
| 20,000 - 50,000 | 88-95% |
| 50,000 - 100,000 | 80-90% |
| 100,000 - 150,000 | 72-85% |
| 150,000+ | 65-80% |
