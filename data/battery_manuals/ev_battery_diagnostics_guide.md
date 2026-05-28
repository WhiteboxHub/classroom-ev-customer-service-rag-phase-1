# EV Battery Diagnostics Guide — XYZ EV Corp
**Document Version:** 3.2.1 | **Firmware Compatibility:** 4.0.x - 4.2.x | **Platform:** EV-3000, EV-5000

## Overview
This guide covers comprehensive battery diagnostics for XYZ EV Corp platforms. The Battery Management System (BMS) continuously monitors cell voltage, temperature, state of charge (SoC), and state of health (SoH).

## 1. Battery Pack Architecture

### 1.1 Cell Configuration
- **Cell Chemistry:** Lithium Nickel Manganese Cobalt Oxide (NMC 811)
- **Cell Voltage Range:** 3.0V (min) — 4.2V (max), nominal 3.6V
- **Pack Configuration:** EV-3000: 108S4P | EV-5000: 120S4P
- **Pack Voltage:** EV-3000: 388.8V nominal | EV-5000: 432V nominal
- **Pack Capacity:** EV-3000: 82kWh | EV-5000: 100kWh

### 1.2 Thermal Management
- Liquid cooling system with dedicated EV coolant loop
- Operating temperature range: -30°C to +55°C
- Optimal charging temperature: 15°C to 40°C
- Optimal performance temperature: 20°C to 35°C

## 2. State of Health (SoH) Diagnostics

### 2.1 SoH Assessment Procedure
1. Connect approved OBD-II diagnostic tool (XYZ DiagTool Pro v2.x or later)
2. Navigate to: **BMS > Battery Health > SoH Analysis**
3. Ensure vehicle SoC is between 15-25% before starting test
4. Run Full Capacity Test (30-45 minutes)
5. System charges to 100% SoC then discharges to 10% under controlled load
6. BMS calculates actual capacity vs nominal capacity

### 2.2 SoH Interpretation
| SoH Range | Status | Action Required |
|-----------|--------|-----------------|
| 90-100% | Excellent | No action required |
| 80-90% | Good | Monitor during next service |
| 70-80% | Fair | Schedule reconditioning service |
| 60-70% | Poor | Battery replacement recommended (DTC P0A80) |
| <60% | Critical | Immediate battery replacement required |

### 2.3 Cell Voltage Spread Analysis
- **Acceptable spread:** < 0.05V across all cells
- **Caution threshold:** 0.05V - 0.1V spread
- **Replacement trigger:** > 0.1V spread between highest and lowest cell voltage
- Access via: BMS > Cell Diagnostics > Individual Cell Voltages

## 3. DTC P0A80 — Replace Hybrid/EV Battery Pack

### 3.1 Trigger Conditions
DTC P0A80 is set when:
- SoH drops below 70% threshold
- Cell voltage spread exceeds 0.15V
- BMS detects irreversible capacity loss pattern
- Battery pack fails the Full Capacity Test

### 3.2 Diagnostic Steps
**Step 1:** Connect OBD-II tool and read all pending/active DTCs
**Step 2:** Export BMS log file (BMS > Logs > Export > USB)
**Step 3:** Verify SoH reading (should show <70%)
**Step 4:** Check individual cell voltages for outliers
**Step 5:** Inspect cooling system for blockages or coolant leaks
**Step 6:** If cooling is intact and SoH <70%, proceed with warranty/replacement claim

### 3.3 Firmware Consideration
Firmware 4.1.0 resolved false-positive P0A80 triggers in temperatures below -10°C. If vehicle is running firmware <4.1.0 and DTC appears in cold weather, update firmware first and retest.

## 4. Thermal Warning Events

### 4.1 BMS_TEMP_HIGH Warning
**Trigger:** Cell temperature > 55°C
**Immediate Actions:**
1. STOP charging immediately if charging is active
2. Do NOT drive the vehicle
3. Move to ventilated area away from structures
4. Check ambient temperature — allow cooling if > 40°C ambient
5. Check coolant level and inspect for leaks
6. Read BMS fault log for thermal event timeline
7. If cell temperature exceeds 65°C — call emergency services (thermal runaway risk)

### 4.2 BMS_TEMP_LOW Warning
**Trigger:** Cell temperature < -15°C
**Actions:**
1. Enable battery pre-conditioning (Settings > Charging > Pre-Conditioning)
2. Allow 15-20 minutes warm-up before DC fast charging
3. Use AC Level 2 charging only until cells reach > 5°C
4. Range reduction of 20-35% is normal at -15°C

## 5. Battery Reconditioning Service
**Service Interval:** When SoH reaches 75-80%
**Procedure Duration:** 4-6 hours
**Process:**
1. Full discharge to 5% SoC under controlled load
2. 2-hour rest period at ambient temperature
3. Controlled slow charge at 0.2C rate to 100% SoC
4. BMS cell balancing cycle (automated)
5. Final SoH assessment
**Expected improvement:** 3-8% SoH recovery
