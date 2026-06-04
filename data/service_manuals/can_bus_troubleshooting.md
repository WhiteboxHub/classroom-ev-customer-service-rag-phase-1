# CAN Bus Troubleshooting Guide — EV Platform
**Document:** SM-CAN-002 | **Version:** 2.1

## EV CAN Bus Architecture
The EV-3000/5000 uses a dual CAN bus architecture:
- **High-Speed CAN (HS-CAN):** 500 kbps — VCM, BMS, MCU, CCM, ADAS
- **Low-Speed CAN (LS-CAN):** 125 kbps — Body control, comfort, infotainment

## U0100 — Lost Communication With ECM/PCM A
**Trigger:** VCM stops sending CAN messages for >200ms

### Diagnosis Flowchart
1. **Read all DTCs first** — Multiple CAN DTCs indicate bus-level failure vs. single-module failure
2. **Check CAN bus resistance:**
   - Disconnect battery 12V negative
   - Measure resistance between CAN-H and CAN-L at OBD-II port (pins 6 and 14)
   - Expected: 60 ohms (two 120-ohm termination resistors in parallel)
   - If >60 ohms: Missing termination resistor (check VCM or BMS CAN terminator)
   - If <60 ohms: Short circuit in CAN wiring
3. **Check VCM supply voltage:**
   - VCM main supply: 11-14V from Battery Junction Box
   - VCM KL30 supply should not drop below 10V during cranking
4. **Check for firmware OTA in progress** — U0100 may appear transiently during update
5. **VCM firmware reflash:** If all wiring and power is OK, reflash VCM via DiagTool Pro > Modules > VCM > Reflash
