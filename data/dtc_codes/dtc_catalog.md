# EV DTC Diagnostic Trouble Code Catalog
**Document:** DTC-CAT-001 | **Version:** 4.2 | **Updated with Firmware:** 4.2.1

## DTC Categories
- **P codes:** Powertrain (battery, motor, charging, BMS)
- **C codes:** Chassis (brake system, suspension interaction)
- **B codes:** Body (infotainment, HMI, convenience)
- **U codes:** Network (CAN bus, module communication)

## Critical DTC Reference Table

### P0A80 — Replace Hybrid/EV Battery Pack
- **System:** Battery Management System (BMS)
- **Severity:** CRITICAL
- **Trigger:** SoH < 70% OR cell spread > 0.15V
- **Symptoms:** Reduced range, range estimation inaccurate, possibly reduced performance
- **Diagnosis Steps:**
  1. Run SoH diagnostic test (35-50 minutes)
  2. Check individual cell voltages for outliers
  3. Inspect thermal management system
  4. Export BMS logs for warranty documentation
- **Resolution:** Battery pack replacement (warrant claimable < 150,000 miles / 8 years)
- **Related DTCs:** P0A94 (DC/DC issue may cause false readings)
- **Firmware Note:** 4.1.0 fixed false positives in temperatures below -10°C

### P1E00 — EVSE Communication Failure
- **System:** Charging Control Module (CCM)
- **Severity:** WARNING
- **Trigger:** ISO 15118 or DIN 70121 handshake timeout (>30 seconds)
- **Symptoms:** DC fast charging not starting, charging session aborted
- **Diagnosis Steps:**
  1. Try different CCS cable on same EVSE
  2. Try different EVSE
  3. Inspect CCS port for moisture or damage
  4. Verify firmware is 4.0.0+ (CCS protocol improvements)
- **Resolution:** Usually resolved by trying different EVSE. If persistent, CCM module inspection required.

### P1E10 — On-Board Charger (OBC) Communication Failure
- **System:** On-Board Charger
- **Severity:** CRITICAL
- **Trigger:** Loss of CAN communication with OBC module
- **Symptoms:** AC Level 2 charging unavailable, possibly DC charging unavailable
- **Diagnosis Steps:**
  1. Check OBC fuse (F47, 40A in EV junction box)
  2. Inspect OBC CAN bus connector (gray 8-pin connector, passenger side)
  3. Check OBC 12V supply voltage (should be 11-14V)
  4. If fuse OK and CAN OK, OBC module may require replacement
- **Resolution:** OBC fuse replacement or OBC module replacement

### P0A94 — DC/DC Converter Performance
- **System:** DC/DC Converter (HV to 12V)
- **Severity:** WARNING
- **Trigger:** 12V bus voltage < 12.0V during HV conversion
- **Symptoms:** 12V battery warning light, possible vehicle power-down
- **Diagnosis Steps:**
  1. Measure 12V battery voltage (should be >12.4V at rest)
  2. Check DC/DC converter fuse (F48, 200A in HV junction box)
  3. Inspect 12V battery for age and condition
- **Resolution:** 12V battery replacement or DC/DC module service

### P0A1F — Battery Pack Voltage Out of Range
- **System:** Battery Management System
- **Severity:** CRITICAL
- **Trigger:** Pack voltage deviation >5% from expected value for SoC
- **Symptoms:** Sudden SoC drop, reduced range, possible limp mode
- **Diagnosis Steps:**
  1. Check individual cell voltages for extreme outliers (>4.25V or <2.8V)
  2. Check contactors for welding (perform contactor test via DiagTool)
  3. Check BMS calibration — recalibrate if last calibration >2 years ago
- **Resolution:** Cell module replacement or BMS recalibration

### U0100 — Lost Communication With ECM/PCM A (CAN Bus Fault)
- **System:** Vehicle Control Module (VCM) / CAN Network
- **Severity:** WARNING
- **Trigger:** No CAN messages from VCM for >200ms
- **Symptoms:** Multiple warning lights, possible limp mode, ADAS disabled
- **Diagnosis Steps:**
  1. Check CAN bus connector at VCM (large white 48-pin connector, center console area)
  2. Test CAN bus resistance — should be 120 ohms between CAN-H and CAN-L
  3. Check for damaged wiring in the main vehicle wiring harness
  4. Check for firmware update (U0100 can appear during OTA update)
  5. Clear DTC and perform ignition cycle test
- **Resolution:** Wiring repair or VCM firmware reflash

### B2AAA — Infotainment Module Boot Failure
- **System:** Infotainment / HMI
- **Severity:** INFORMATIONAL
- **Trigger:** Infotainment module failed to boot within 60 seconds
- **Symptoms:** Black screen on center display, audio unavailable
- **Diagnosis Steps:**
  1. Perform hard reset: hold Power button 10 seconds
  2. Check infotainment fuse (F22, 10A, interior fuse box)
  3. Check for pending software update causing boot loop
- **Resolution:** Hard reset (90% of cases). If persistent, factory reset via Settings > System > Factory Reset.
