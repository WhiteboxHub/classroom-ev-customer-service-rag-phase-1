# EV Thermal Management System Guide
**Document:** TMS-003 | **Version:** 1.4 | **Firmware:** 4.1.0+

## System Overview
The XYZ EV Corp Thermal Management System (TMS) maintains battery pack temperature within the optimal operating window using:
- Liquid cooling loop with dedicated EV-grade coolant (XYZ CoolFluid G48)
- Variable-speed coolant pump (150-3500 RPM)
- Chiller unit for active cooling (driven by A/C compressor)
- PTC heater for cold-weather pre-conditioning
- Adaptive Thermal Management Algorithm (ATMA v2 — introduced in firmware 4.1.0)

## ATMA v2 Improvements (Firmware 4.1.0)
- Dynamic pump speed based on predicted thermal load from drive profile
- Pre-conditioning battery to 20-30°C before DC fast charging starts
- Predictive cooling during regenerative braking
- Improved cell balancing during thermal events

## Coolant Specifications
- **Type:** XYZ CoolFluid G48 (ethylene glycol-based, orange color)
- **Concentration:** 50% coolant / 50% distilled water
- **Change interval:** Every 5 years or 100,000 miles
- **Capacity:** EV-3000: 8.5L | EV-5000: 10.2L
- **DO NOT** use standard automotive coolant — will damage EV-specific seals

## Thermal Warning Thresholds
| Parameter | Warning | Critical | Emergency |
|-----------|---------|----------|----------|
| Cell Temp High | 50°C | 58°C | 65°C |
| Cell Temp Low | -10°C | -20°C | N/A |
| Coolant Temp | 55°C | 65°C | 70°C |
| Temp Delta | 8°C | 12°C | 15°C |
