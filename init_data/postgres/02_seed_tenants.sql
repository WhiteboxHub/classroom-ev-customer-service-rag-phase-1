-- ========================================================
-- EV RAG Platform — Tenant Seed Data
-- ========================================================

INSERT INTO tenants (tenant_key, name, config) VALUES
(
    'ev_technicians',
    'EV Field Technicians',
    '{"access_level": "full", "can_view_dtc": true, "can_view_hv_procedures": true, "retrieval_permissions": ["service_manuals", "dtc_codes", "technician_notes", "firmware_updates", "battery_manuals"]}'
),
(
    'ev_support_tier1',
    'EV Customer Support Tier 1',
    '{"access_level": "standard", "can_view_dtc": true, "can_view_hv_procedures": false, "retrieval_permissions": ["dtc_codes", "charging_docs", "ota_release_notes"]}'
),
(
    'ev_fleet_ops',
    'EV Fleet Operations',
    '{"access_level": "standard", "can_view_dtc": true, "can_view_hv_procedures": false, "retrieval_permissions": ["firmware_updates", "ota_release_notes", "charging_docs"]}'
),
(
    'ev_engineers',
    'EV Platform Engineers',
    '{"access_level": "admin", "can_view_dtc": true, "can_view_hv_procedures": true, "retrieval_permissions": ["all"]}'
)
ON CONFLICT (tenant_key) DO NOTHING;

-- Seed DTC Catalog with critical EV DTCs
INSERT INTO dtc_catalog (dtc_code, category, description, severity, resolution_steps) VALUES
('P0A80', 'P', 'Replace Hybrid/EV Battery Pack — Cell capacity below threshold', 'critical', 'Inspect cell voltages. Check BMS logs. Replace battery pack if SOH < 70%.'),
('P1E00', 'P', 'EVSE Communication Failure — CCS/CHAdeMO handshake error', 'warning', 'Check CCS plug for damage. Verify EVSE compatibility. Try different charging station.'),
('P1E10', 'P', 'On-Board Charger (OBC) Communication Failure', 'critical', 'Check OBC fuse. Inspect wiring harness. May require OBC module replacement.'),
('P0A1F', 'P', 'Battery Pack Voltage Out of Range', 'critical', 'Measure pack voltage with multimeter. Check for cell drift. BMS recalibration may be required.'),
('U0100', 'U', 'Lost Communication With ECM/PCM A — CAN bus fault', 'warning', 'Check CAN bus connectors. Inspect wiring. Clear DTC and retry. May need VCM firmware reflash.'),
('B2AAA', 'B', 'Infotainment Module Boot Failure', 'informational', 'Perform hard reset. Check infotainment fuse. Factory reset via Settings > System > Factory Reset.'),
('P0A94', 'P', 'DC/DC Converter Performance — Low output voltage', 'warning', 'Check 12V battery. Inspect DC/DC converter connections. May need module replacement.')
ON CONFLICT (dtc_code) DO NOTHING;
