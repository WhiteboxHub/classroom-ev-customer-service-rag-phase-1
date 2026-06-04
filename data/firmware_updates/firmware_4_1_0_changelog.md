# Firmware 4.1.0 — Release Notes and Changelog
**Version:** 4.1.0 | **Release Date:** 2023-07-20 | **Type:** Minor Update
**Platform:** EV-3000, EV-5000 | **Mandatory OTA:** NO (recommended)

## Summary
Firmware 4.1.0 introduces the Adaptive Thermal Management Algorithm v2 (ATMA v2), improved cold-weather performance, and BMS calibration improvements.

## New Features

### ATMA v2 — Adaptive Thermal Management Algorithm v2
- Dynamic coolant pump speed control (previously fixed 3-speed, now continuously variable 150-3500 RPM)
- Pre-conditioning: Battery automatically pre-heats/cools to 20-30°C when DC fast charging is initiated via navigation or app
- Predictive cooling during high-performance driving based on route gradient
- Improved BMS cell balancing during thermal events

### Cold Weather Improvements
- P0A80 false positive fix: DTC P0A80 was incorrectly triggered below -10°C due to reduced apparent capacity. Fixed with temperature-compensated SoH calculation.
- Range estimation accuracy improved by 8% in temperatures below -5°C
- Pre-conditioning via app now available without active charging session

## Bug Fixes
- Fixed: U0100 intermittent during OBC initialization (reduced from 0.3% occurrence to 0.02%)
- Fixed: DC/DC converter efficiency drop above 45°C ambient (P0A94 false trigger)
- Fixed: Cell balancing stuck in loop after 48 hours of storage

## Known Issues
- None at time of release
