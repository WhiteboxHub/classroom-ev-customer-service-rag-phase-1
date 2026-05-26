# Firmware OTA Update Recovery Procedure

**Firmware Version:** 4.2.x  
**Diagnostic Category:** firmware  

## When to Use
Customer reports failed OTA, vehicle stuck on "Update paused", or repeated rollback to previous build.

## Recovery Steps

### Step 1: Preconditions
- Vehicle SOC must be between 40% and 80%.
- Connect to stable Wi-Fi or cellular with > 10 Mbps.
- Parking brake engaged, vehicle in Park.

### Step 2: Clear OTA cache
1. Infotainment: **Settings > System > Software > Clear download cache**.
2. Restart infotainment (hold power 10 sec).

### Step 3: Manual OTA retry
1. **Settings > System > Software > Check for updates**.
2. If update 4.2.1 available, download on Wi-Fi only.
3. Do not drive during install; expect 25–45 minutes.

### Step 4: Workshop recovery (failed twice)
1. Connect diagnostic tool; run **OTA > Force recovery mode**.
2. Apply package OTA-4.2.1-REC from secure service portal.
3. Validate all ECUs report matching version post-install.

## Post-Update Validation
- Verify charging profile version ≥ 4.2.1-C
- Clear history DTCs after 10 min power cycle
