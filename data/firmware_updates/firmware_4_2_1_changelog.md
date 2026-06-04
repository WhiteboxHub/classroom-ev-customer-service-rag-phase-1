# Firmware 4.2.1 — Release Notes and Changelog
**Version:** 4.2.1 | **Release Date:** 2024-01-15 | **Type:** Minor Update + Critical Bug Fix
**Platform:** EV-3000, EV-5000 | **Mandatory OTA:** YES (within 90 days)

## Summary
Firmware 4.2.1 includes critical fixes for CCS charging handshake stability, a battery thermal management improvement, and an OTA delivery reliability improvement.

## Critical Fixes

### [CRITICAL] CCS Charging Handshake Stability Fix
- **Issue:** Some EV-3000 vehicles experienced P1E00 after OTA 4.2.0 update
- **Root cause:** ISO 15118 TLS handshake timeout regression in 4.2.0 (30s → 15s unintentionally)
- **Fix:** Restored ISO 15118 TLS timeout to 30 seconds. Added DIN 70121 fallback retry logic
- **DTC resolved:** P1E00 (EVSE Communication Failure)
- **Affected builds:** 4.2.0 only

### [CRITICAL] OTA Delivery Reliability
- **Issue:** OTA_INSTALL_FAIL_3 (checksum mismatch) occurring on vehicles with intermittent WiFi
- **Root cause:** Partial firmware package download without retry logic
- **Fix:** Added 3-retry download with chunk-based validation
- **Error resolved:** OTA_INSTALL_FAIL_3

## Improvements
- CAN bus message prioritization for charging control (reduces U0100 during charge start)
- BMS cold-weather SoC estimation accuracy +3% below -5°C
- Regen braking thermal prediction update (ATMA v2.1)
- OTA UI: Added detailed progress percentage display (was binary start/complete)

## Known Issues in 4.2.1
- AC Level 2 charging may show incorrect time-to-full on 3-phase 22kW EVSE (cosmetic only, actual charging is correct)
- Navigation map tiles may load slowly for 30 seconds after cold boot (fix in 4.3.0)

## Installation
- **OTA:** Settings > Software Update > Check for Updates
- **Manual:** Via USB drive (contact support for USB package)
- **Estimated install time:** 18-25 minutes
- **Downtime:** Vehicle unavailable during installation
- **Rollback:** Rollback to 4.2.0 available for 72 hours via DiagTool Pro
