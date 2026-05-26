# EV Charging Failure After OTA Update

**Vehicle Model:** XYZ Model E  
**Firmware Version:** 4.2.1  
**Diagnostic Category:** charging  
**Charging Type:** CCS  

## Symptom
Vehicle does not initiate DC fast charging after completing OTA firmware update 4.2.1. Charge port LED blinks amber; infotainment shows "Charging unavailable – schedule service if persistent."

## Procedure

### Step 1: Verify charge port and cable
1. Inspect CCS inlet for debris, moisture, or bent pins.
2. Reseat the DC fast charge connector until the latch clicks.
3. Retry on a known-good CCS station (minimum 50 kW).

### Step 2: Soft reset charging ECU
1. Shift to Park, power off vehicle for 2 minutes.
2. Power on without plugging in; wait 30 seconds.
3. Plug in and confirm charge session starts within 60 seconds.

### Step 3: Re-apply charging profile (FW 4.2.1)
1. Connect to workshop diagnostic tool.
2. Navigate: **Body > Charging > Reset charge profile**.
3. Apply service bulletin SB-CHG-0421 patch if profile version is below 4.2.1-C.

### Step 4: Escalation
If charging still fails, capture DTCs and escalate to Tier-2 with VIN, OTA build, and station ID.

## Safety
Do not bypass interlocks or modify high-voltage components without HV certification.
