-- ========================================================
-- EV RAG Platform — PostgreSQL Schema
-- Database: evragdb
-- Manages: document lifecycle, versions, DTC catalog,
--          firmware catalog, retrieval sessions, tenants
-- ========================================================

-- Tenants (multi-tenant isolation)
CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    tenant_key VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Documents (document lifecycle tracking)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR(64) UNIQUE NOT NULL,
    source_file VARCHAR(512) NOT NULL,
    file_type VARCHAR(32),
    doc_category VARCHAR(128),
    vehicle_platform VARCHAR(64),
    firmware_version VARCHAR(64),
    lifecycle_state VARCHAR(32) DEFAULT 'active',  -- active, deprecated, deleted
    tenant_id VARCHAR(64) REFERENCES tenants(tenant_key),
    chunk_count INTEGER DEFAULT 0,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Document Versions (version lineage tracking)
CREATE TABLE IF NOT EXISTS document_versions (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL,
    version VARCHAR(32) NOT NULL,
    previous_version VARCHAR(32),
    change_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(128)
);

-- DTC Catalog (Diagnostic Trouble Code reference)
CREATE TABLE IF NOT EXISTS dtc_catalog (
    id SERIAL PRIMARY KEY,
    dtc_code VARCHAR(16) UNIQUE NOT NULL,
    category VARCHAR(64),            -- P=powertrain, C=chassis, B=body, U=network
    description TEXT NOT NULL,
    severity VARCHAR(32),            -- critical, warning, informational
    vehicle_platforms JSONB,         -- which vehicle models this DTC applies to
    resolution_steps TEXT,
    related_dtcs JSONB,
    firmware_versions JSONB,         -- firmware versions where this DTC exists
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Firmware Catalog
CREATE TABLE IF NOT EXISTS firmware_catalog (
    id SERIAL PRIMARY KEY,
    version VARCHAR(32) UNIQUE NOT NULL,
    vehicle_platform VARCHAR(64),
    release_date DATE,
    release_type VARCHAR(32),        -- major, minor, patch, hotfix, ota_mandatory
    changelog TEXT,
    known_issues JSONB,
    fixed_dtcs JSONB,
    is_current BOOLEAN DEFAULT FALSE,
    rollback_allowed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Retrieval Sessions (for analytics and memory)
CREATE TABLE IF NOT EXISTS retrieval_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    tenant_id VARCHAR(64),
    user_query TEXT NOT NULL,
    retrieved_chunks JSONB,
    answer_generated TEXT,
    retrieval_latency_ms FLOAT,
    generation_latency_ms FLOAT,
    retrieval_mode VARCHAR(64),
    grounded BOOLEAN,
    top_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat History (persistent conversation memory)
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    turn_index INTEGER NOT NULL,
    user_message TEXT NOT NULL,
    assistant_message TEXT NOT NULL,
    sources_cited JSONB,
    grounded BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_documents_document_id ON documents(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_lifecycle ON documents(lifecycle_state);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(doc_category);
CREATE INDEX IF NOT EXISTS idx_dtc_catalog_code ON dtc_catalog(dtc_code);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON retrieval_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id);
