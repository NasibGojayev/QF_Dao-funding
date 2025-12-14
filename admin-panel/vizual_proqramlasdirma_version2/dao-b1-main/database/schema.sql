-- ============================================================
-- DAO Database Schema - PostgreSQL DDL
-- ============================================================
-- Aligned with SDF1 ERD
-- Normalized to 4NF/5NF
-- ============================================================

-- Drop existing tables (for clean setup)
DROP TABLE IF EXISTS event_logs CASCADE;
DROP TABLE IF EXISTS indexer_state CASCADE;
DROP TABLE IF EXISTS project_tags CASCADE;
DROP TABLE IF EXISTS milestones CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================
-- USERS TABLE
-- ============================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(66) NOT NULL UNIQUE,
    email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Wallet must be valid Ethereum address format
    CONSTRAINT valid_wallet_format CHECK (wallet ~ '^0x[a-fA-F0-9]{40}$')
);

COMMENT ON TABLE users IS 'User accounts identified by Ethereum wallet address';
COMMENT ON COLUMN users.wallet IS 'Ethereum wallet address (0x + 40 hex chars)';

-- ============================================================
-- PROJECTS TABLE
-- ============================================================
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE projects IS 'Funding projects created by users';

-- ============================================================
-- TAGS TABLE
-- ============================================================
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

COMMENT ON TABLE tags IS 'Categorization tags for projects and transactions';

-- ============================================================
-- TRANSACTIONS TABLE
-- ============================================================
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    tx_hash VARCHAR(66) NOT NULL UNIQUE,
    block_number INTEGER,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    tag_id INTEGER REFERENCES tags(id) ON DELETE SET NULL,
    amount NUMERIC(36, 18) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    event_type VARCHAR(50),
    
    -- Transaction hash must be valid format
    CONSTRAINT valid_tx_hash_format CHECK (tx_hash ~ '^0x[a-fA-F0-9]{64}$')
);

COMMENT ON TABLE transactions IS 'Blockchain transaction records';
COMMENT ON COLUMN transactions.amount IS 'Amount in ETH with wei precision (18 decimals)';
COMMENT ON COLUMN transactions.event_type IS 'Contract event: TransactionCreated, MilestoneResolved, TagAssigned';

-- ============================================================
-- MILESTONES TABLE
-- ============================================================
CREATE TABLE milestones (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_amount NUMERIC(36, 18),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolved_tx_hash VARCHAR(66)
);

COMMENT ON TABLE milestones IS 'Project milestones for staged funding release';

-- ============================================================
-- PROJECT_TAGS TABLE (Junction - Many-to-Many)
-- ============================================================
CREATE TABLE project_tags (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent duplicate tag assignments
    CONSTRAINT uq_project_tag UNIQUE (project_id, tag_id)
);

COMMENT ON TABLE project_tags IS 'Many-to-many relationship between projects and tags';

-- ============================================================
-- INDEXER_STATE TABLE (ETL Progress Tracking)
-- ============================================================
CREATE TABLE indexer_state (
    id SERIAL PRIMARY KEY,
    contract_address VARCHAR(66) NOT NULL UNIQUE,
    last_block_processed INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE indexer_state IS 'Tracks indexer/ETL progress for resumption and backfill';

-- ============================================================
-- EVENT_LOGS TABLE (Raw Event Audit Log)
-- ============================================================
CREATE TABLE event_logs (
    id SERIAL PRIMARY KEY,
    tx_hash VARCHAR(66) NOT NULL,
    block_number INTEGER NOT NULL,
    log_index INTEGER NOT NULL,
    contract_address VARCHAR(66) NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    event_data TEXT,  -- JSON string
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique event identification
    CONSTRAINT uq_event_log UNIQUE (tx_hash, log_index)
);

COMMENT ON TABLE event_logs IS 'Raw blockchain event logs for auditing and SIEM integration';
