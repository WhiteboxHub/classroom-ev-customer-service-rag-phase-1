# CCS DC Fast Charging Procedure
**Document:** CHG-CCS-001 | **Version:** 2.3 | **Platform:** EV-3000, EV-5000

## Overview
Combined Charging System (CCS2 / Combo2) enables DC fast charging at up to 150kW on the EV-3000 platform and 250kW on EV-5000. Uses ISO 15118 PLC communication protocol.

## Supported Charging Standards
- **CCS2 (Combined Charging System Type 2):** Primary DC fast charge standard
- **ISO 15118:** Vehicle-to-EVSE digital communication (Plug & Charge enabled)
- **DIN 70121:** Fallback protocol for older EVSE
- **CHAdeMO:** NOT supported on EV-3000/5000 platforms

## Charging Procedure

### Step 1: Pre-Charge Checks
1. Verify SoC is above 5% (vehicle will not accept charge below 2%)
2. Check for active DTCs related to charging (P1E00, P1E10)
3. Ensure charge port latch is clean and undamaged
4. Battery temperature should be above 5°C for DC fast charging

### Step 2: EVSE Connection
1. Insert CCS2 plug into charge port until you hear the latch click
2. Vehicle will verify EVSE capabilities via PLC within 10 seconds
3. Charging begins automatically after handshake (≤30 seconds)
4. Dashboard will show: Charging Active, Target Range, ETA to 80%

### Step 3: Charging Rates
| SoC Range | Charging Rate (EV-3000) | Charging Rate (EV-5000) |
|-----------|------------------------|------------------------|
| 5-20% | 150kW peak | 250kW peak |
| 20-80% | 100-150kW | 150-250kW |
| 80-90% | 50-80kW | 80-120kW |
| 90-100% | 10-30kW | 20-50kW |

### Step 4: Completing Charge
1. Charging automatically tapers at 80% SoC
2. Press Unlock button on fob or app to release plug
3. Plug will disengage after door handle touch confirmation

## DTC P1E00 — EVSE Communication Failure
**Cause:** ISO 15118 / DIN 70121 handshake failure
**Diagnosis:**
1. Try different CCS plug on same EVSE
2. Try different EVSE at same location
3. Check charge port for moisture or debris
4. Check for active firmware update (do not charge during OTA)
5. Verify firmware is 4.0.0 or later (CCS protocol fixes)
