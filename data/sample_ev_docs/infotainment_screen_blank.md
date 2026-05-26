# Infotainment – Blank Screen / HMI Reset

**Diagnostic Category:** infotainment  
**Vehicle Model:** XYZ Model X  

## Symptoms
Center display blank after startup, touch unresponsive, or cyclic reboot during drive.

## Procedure

### Step 1: Hard reset HMI
1. Press and hold steering-wheel voice + volume-up for 12 seconds until logo appears.
2. Allow 3-minute reboot; do not shift out of Park during reset.

### Step 2: Check fuses (workshop)
- Fuse F42 (HMI power) in cabin fuse box – replace if open.

### Step 3: Software recovery
1. Diagnostic tool: **Infotainment > Reload UI bundle**.
2. If build < 3.8.0, apply patch INF-380-HF before release.

### Step 4: Escalation
Persistent blank screen after two resets requires HMI module replacement per RMA workflow INF-RMA-01.
