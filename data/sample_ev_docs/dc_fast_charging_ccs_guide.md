# DC Fast Charging (CCS) Troubleshooting Guide

**Charging Type:** CCS  
**Diagnostic Category:** charging  

## Common Issues

### Issue: Session starts then stops within 2 minutes
**Likely causes:** Battery thermal derate, payment handshake failure, incompatible station firmware.

**Resolution:**
1. Check battery inlet temperature; if > 45°C, advise cooldown 15 minutes.
2. Retry with alternate CCS stall.
3. If repeat failure, pull logs: `Charging > Session log > Export last 3 sessions`.

### Issue: "Incompatible charger" message
1. Confirm vehicle supports CCS Combo 1 (North America) or Combo 2 (EU) per build sheet.
2. Verify station is CCS (not CHAdeMO-only).

### Issue: Reduced charge rate below 50 kW on capable station
1. Check SOC; ramp tapers above 80% SOC by design.
2. Review BMS derate flags for P1B00 thermal active.

## Technical Reference
- Max DC current (Model E): 500 A peak, 10 min
- Port pinout: CCS pins 1-7 per ISO 15118
