# Field Technician Notes — MSD Procedure
**Author:** Senior EV Technician Team | **Last Updated:** 2024-01-10

## Common MSD Mistakes (Lessons Learned)

### Mistake 1: Not waiting the full 5 minutes
Do not rush the capacitor discharge period. We had an incident where a tech attempted to test voltage at 3 minutes and measured 180V. Wait the FULL 5 minutes. In cold weather (<0°C), wait 8 minutes — capacitors discharge slower in cold.

### Mistake 2: Touching orange HV cables
The orange cables near the MSD are ALWAYS live even with MSD pulled if you haven't isolated upstream. Never touch orange-colored cables or components without verifying isolation.

### Mistake 3: Not verifying isolation with multimeter
Always verify with a CAT III multimeter. We've had cases where the MSD was pulled but the 12V to HV contactor coil was still energized, keeping the contactor closed. Voltage check is NON-NEGOTIABLE.

### Mistake 4: Wrong LOTO device
Use only EV-approved LOTO devices. Standard mechanical padlocks on MSD can crack the plastic housing. Use the XYZ LOTO-EV kit (Part No: XYZ-LOTO-001).

## Tips for EV-5000 MSD Access
The EV-5000 rear seat MSD access is tricky. The seat cushion uses 3 plastic clips at the front edge. Lift from the front — do NOT pull from the rear or you'll break the rear clips. Use a plastic trim removal tool (never metal).

## After MSD Re-engagement
After re-engaging MSD, always do the following before handing vehicle back:
1. Clear all DTCs (MSD pull generates DTCs)
2. Perform HV system self-test: DiagTool > System Tests > HV Integrity Check
3. Verify charge port works with a Level 2 test charge (minimum 5 minutes)
4. Document in vehicle service record
