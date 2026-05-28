# AC Level 2 Charging Troubleshooting Guide
**Document:** CHG-AC-002 | **Version:** 1.8 | **Platform:** All EV Platforms

## Overview
AC Level 2 charging uses the J1772 / IEC 62196 Type 2 standard. The On-Board Charger (OBC) converts AC power to DC for battery charging.

## On-Board Charger Specifications
- **EV-3000 OBC:** 11.5kW (single-phase 32A) or 22kW (three-phase 32A)
- **EV-5000 OBC:** 22kW (three-phase 32A)
- **Input voltage:** 100-240V AC single-phase | 200-480V AC three-phase
- **Frequency:** 50-60Hz

## J1772 Pilot Signal Troubleshooting

The pilot signal is a 1kHz PWM signal between EVSE and vehicle that negotiates charging current.

| Pilot Signal | Meaning | Action |
|-------------|---------|--------|
| +12V DC static | EVSE ready, no vehicle connected | Check charge port latch sensor |
| +9V / -12V PWM | EVSE ready, vehicle connected | Normal — charge should start |
| +6V / -12V PWM | EVSE ready, vehicle charging | Normal — charging active |
| 0V | EVSE fault or no power | Check EVSE breaker, GFCI |
| -12V static | EVSE error state | Reset EVSE |

## Common AC Level 2 Issues

### Issue: Charging Not Starting
1. Check EVSE circuit breaker (40A minimum for 32A EVSE)
2. Check GFCI outlet if using Level 2 adapter
3. Verify pilot signal is PWM (not +12V static)
4. Ensure charge port door is fully closed
5. Check DTC P1E10 (OBC Communication Failure)
6. Try scheduling charge via app (some EVSEs have delayed start by default)

### Issue: Charging Stops After a Few Minutes
1. Check for thermal events (BMS_TEMP_HIGH)
2. Verify EVSE ground fault — common with older home wiring
3. Check DTC B2AAA (system error during charge)
4. Inspect OBC cooling — OBC has its own cooling circuit on EV-5000

### Issue: Slow Charging Speed
1. Verify EVSE amperage rating — many 7.2kW EVSEs are limited to 30A
2. Check OBC amperage setting: Settings > Charging > Max Charge Current
3. Confirm three-phase EVSE for 22kW OBC
4. Cold battery will limit charging speed (pre-condition battery first)
