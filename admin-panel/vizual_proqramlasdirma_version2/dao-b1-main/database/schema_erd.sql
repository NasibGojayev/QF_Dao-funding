-- ============================================================
-- DAO Quadratic Funding - Complete Database Schema
-- Based on ERD: Entity Relationship Diagram
-- ============================================================
-- Tables: donors, wallets, sybil_scores, governance_token,
--         contract_events, matching_pool, rounds, proposals,
--         matches, donations, qf_results, payouts
-- ============================================================

-- Drop existing tables (for clean setup)
DROP TABLE IF EXISTS payouts CASCADE;
DROP TABLE IF EXISTS qf_results CASCADE;
DROP TABLE IF EXISTS donations CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS proposals CASCADE;
DROP TABLE IF EXISTS contract_events CASCADE;
DROP TABLE IF EXISTS rounds CASCADE;
DROP TABLE IF EXISTS matching_pool CASCADE;
DROP TABLE IF EXISTS governance_token CASCADE;
DROP TABLE IF EXISTS sybil_scores CASCADE;
DROP TABLE IF EXISTS wallets CASCADE;
DROP TABLE IF EXISTS donors CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;

-- ============================================================
-- DONORS TABLE (User Registration/Login)
-- ============================================================
CREATE TABLE donors (
    donor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID,  -- FK to wallets, set after wallet connection
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hashed
    reputation_score FLOAT DEFAULT 0.0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

COMMENT ON TABLE donors IS 'User accounts with registration and login support';
COMMENT ON COLUMN donors.password_hash IS 'Bcrypt hashed password for authentication';
COMMENT ON COLUMN donors.reputation_score IS 'User trust score based on activity';

-- ============================================================
-- USER_SESSIONS TABLE (Login Session Management)
-- ============================================================
CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id UUID NOT NULL REFERENCES donors(donor_id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE user_sessions IS 'Active user sessions for authentication';

-- ============================================================
-- WALLETS TABLE
-- ============================================================
CREATE TABLE wallets (
    wallet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address VARCHAR(66) NOT NULL UNIQUE,
    balance DECIMAL(36, 18) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'frozen', 'flagged')),
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_wallet_address CHECK (address ~ '^0x[a-fA-F0-9]{40}$')
);

COMMENT ON TABLE wallets IS 'Ethereum wallet addresses linked to donors';

-- Add FK from donors to wallets
ALTER TABLE donors ADD CONSTRAINT fk_donor_wallet 
    FOREIGN KEY (wallet_id) REFERENCES wallets(wallet_id) ON DELETE SET NULL;

-- ============================================================
-- SYBIL_SCORES TABLE
-- ============================================================
CREATE TABLE sybil_scores (
    score_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID NOT NULL REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    score FLOAT NOT NULL CHECK (score >= 0 AND score <= 1),
    verified_by VARCHAR(100),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sybil_scores IS 'Sybil resistance scores for wallets';

-- ============================================================
-- GOVERNANCE_TOKEN TABLE
-- ============================================================
CREATE TABLE governance_token (
    holder_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID NOT NULL REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    voting_power DECIMAL(36, 18) DEFAULT 0,
    role VARCHAR(20) DEFAULT 'member' CHECK (role IN ('member', 'admin', 'council')),
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE governance_token IS 'Governance token holdings and voting power';

-- ============================================================
-- MATCHING_POOL TABLE
-- ============================================================
CREATE TABLE matching_pool (
    pool_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    total_funds DECIMAL(36, 18) NOT NULL DEFAULT 0,
    allocated_funds DECIMAL(36, 18) DEFAULT 0,
    replenished_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE matching_pool IS 'Quadratic funding matching pool funds';

-- ============================================================
-- ROUNDS TABLE
-- ============================================================
CREATE TABLE rounds (
    round_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    matching_pool_id UUID REFERENCES matching_pool(pool_id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'upcoming' CHECK (status IN ('active', 'closed', 'upcoming')),
    title VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_round_dates CHECK (end_date > start_date)
);

COMMENT ON TABLE rounds IS 'Funding rounds with matching pools';

-- ============================================================
-- PROPOSALS TABLE
-- ============================================================
CREATE TABLE proposals (
    proposal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    proposer_id UUID NOT NULL REFERENCES donors(donor_id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'funded')),
    round_id UUID REFERENCES rounds(round_id) ON DELETE SET NULL,
    total_donations DECIMAL(36, 18) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE proposals IS 'Project proposals submitted for funding';

-- ============================================================
-- CONTRACT_EVENTS TABLE
-- ============================================================
CREATE TABLE contract_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    round_id UUID REFERENCES rounds(round_id) ON DELETE SET NULL,
    proposal_id UUID REFERENCES proposals(proposal_id) ON DELETE SET NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tx_hash VARCHAR(66) UNIQUE,
    block_number INTEGER,
    event_data JSONB,
    
    CONSTRAINT valid_tx_hash CHECK (tx_hash IS NULL OR tx_hash ~ '^0x[a-fA-F0-9]{64}$')
);

COMMENT ON TABLE contract_events IS 'Smart contract events for auditing';

-- ============================================================
-- MATCHES TABLE
-- ============================================================
CREATE TABLE matches (
    match_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    round_id UUID NOT NULL REFERENCES rounds(round_id) ON DELETE CASCADE,
    matched_amount DECIMAL(36, 18) NOT NULL DEFAULT 0,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE matches IS 'Quadratic matching amounts for proposals';

-- ============================================================
-- DONATIONS TABLE
-- ============================================================
CREATE TABLE donations (
    donation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id UUID NOT NULL REFERENCES donors(donor_id) ON DELETE CASCADE,
    proposal_id UUID NOT NULL REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    amount DECIMAL(36, 18) NOT NULL CHECK (amount > 0),
    sybil_score FLOAT,
    tx_hash VARCHAR(66),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_donation_tx CHECK (tx_hash IS NULL OR tx_hash ~ '^0x[a-fA-F0-9]{64}$')
);

COMMENT ON TABLE donations IS 'Individual donations to proposals';

-- ============================================================
-- QF_RESULTS TABLE (Quadratic Funding Results)
-- ============================================================
CREATE TABLE qf_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    round_id UUID NOT NULL REFERENCES rounds(round_id) ON DELETE CASCADE,
    proposal_id UUID NOT NULL REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    calculated_match DECIMAL(36, 18) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE qf_results IS 'Quadratic funding calculation results';

-- ============================================================
-- PAYOUTS TABLE
-- ============================================================
CREATE TABLE payouts (
    payout_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(proposal_id) ON DELETE CASCADE,
    round_id UUID NOT NULL REFERENCES rounds(round_id) ON DELETE CASCADE,
    amount DECIMAL(36, 18) NOT NULL,
    tx_hash VARCHAR(66),
    distributed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    
    CONSTRAINT valid_payout_tx CHECK (tx_hash IS NULL OR tx_hash ~ '^0x[a-fA-F0-9]{64}$')
);

COMMENT ON TABLE payouts IS 'Fund distributions to proposals';

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- Donors indexes
CREATE INDEX idx_donors_username ON donors(username);
CREATE INDEX idx_donors_email ON donors(email);
CREATE INDEX idx_donors_wallet ON donors(wallet_id);

-- Sessions indexes
CREATE INDEX idx_sessions_donor ON user_sessions(donor_id);
CREATE INDEX idx_sessions_token ON user_sessions(token);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);

-- Wallets indexes
CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_wallets_status ON wallets(status);

-- Proposals indexes
CREATE INDEX idx_proposals_proposer ON proposals(proposer_id);
CREATE INDEX idx_proposals_round ON proposals(round_id);
CREATE INDEX idx_proposals_status ON proposals(status);

-- Donations indexes
CREATE INDEX idx_donations_donor ON donations(donor_id);
CREATE INDEX idx_donations_proposal ON donations(proposal_id);
CREATE INDEX idx_donations_created ON donations(created_at);

-- Rounds indexes
CREATE INDEX idx_rounds_status ON rounds(status);
CREATE INDEX idx_rounds_dates ON rounds(start_date, end_date);

-- Contract events indexes
CREATE INDEX idx_events_type ON contract_events(event_type);
CREATE INDEX idx_events_timestamp ON contract_events(timestamp);
CREATE INDEX idx_events_round ON contract_events(round_id);
