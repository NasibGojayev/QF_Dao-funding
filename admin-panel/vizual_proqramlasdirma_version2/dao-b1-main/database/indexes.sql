-- ============================================================
-- DAO Database Indexes - PostgreSQL
-- ============================================================
-- Hot-path indexes for common query patterns
-- ============================================================

-- ============================================================
-- USERS INDEXES
-- ============================================================

-- Primary lookup by wallet address (Web3 authentication)
CREATE INDEX IF NOT EXISTS ix_users_wallet ON users(wallet);

-- ============================================================
-- PROJECTS INDEXES
-- ============================================================

-- Find projects by owner (My Projects page)
CREATE INDEX IF NOT EXISTS ix_projects_owner_id ON projects(owner_id);

-- Sort projects by creation date
CREATE INDEX IF NOT EXISTS ix_projects_created_at ON projects(created_at DESC);

-- Filter active projects only
CREATE INDEX IF NOT EXISTS ix_projects_active ON projects(is_active) WHERE is_active = TRUE;

-- ============================================================
-- TRANSACTIONS INDEXES
-- ============================================================

-- Unique lookup by transaction hash (idempotent inserts)
CREATE UNIQUE INDEX IF NOT EXISTS ix_transactions_tx_hash ON transactions(tx_hash);

-- Filter by user (user transaction history)
CREATE INDEX IF NOT EXISTS ix_transactions_user_id ON transactions(user_id);

-- Filter by project (project donation history)
CREATE INDEX IF NOT EXISTS ix_transactions_project_id ON transactions(project_id);

-- Filter by tag (analytics)
CREATE INDEX IF NOT EXISTS ix_transactions_tag_id ON transactions(tag_id);

-- Time-series queries (dashboard, recent activity)
CREATE INDEX IF NOT EXISTS ix_transactions_created_at ON transactions(created_at DESC);

-- Block number for backfill range queries
CREATE INDEX IF NOT EXISTS ix_transactions_block_number ON transactions(block_number);

-- COMPOSITE: User's transactions ordered by time (HOT PATH!)
-- Supports: SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50
CREATE INDEX IF NOT EXISTS ix_transactions_user_created 
    ON transactions(user_id, created_at DESC);

-- COMPOSITE: Project's transactions ordered by time
CREATE INDEX IF NOT EXISTS ix_transactions_project_created 
    ON transactions(project_id, created_at DESC);

-- PARTIAL: Only successful transactions (common filter)
CREATE INDEX IF NOT EXISTS ix_transactions_success 
    ON transactions(user_id, created_at DESC) 
    WHERE success = TRUE;

-- Event type for ETL processing
CREATE INDEX IF NOT EXISTS ix_transactions_event_type ON transactions(event_type);

-- ============================================================
-- MILESTONES INDEXES
-- ============================================================

-- Get all milestones for a project
CREATE INDEX IF NOT EXISTS ix_milestones_project_id ON milestones(project_id);

-- Find unresolved milestones
CREATE INDEX IF NOT EXISTS ix_milestones_unresolved 
    ON milestones(project_id) 
    WHERE resolved = FALSE;

-- ============================================================
-- PROJECT_TAGS INDEXES
-- ============================================================

-- Get all tags for a project
CREATE INDEX IF NOT EXISTS ix_project_tags_project_id ON project_tags(project_id);

-- Get all projects with a specific tag
CREATE INDEX IF NOT EXISTS ix_project_tags_tag_id ON project_tags(tag_id);

-- ============================================================
-- EVENT_LOGS INDEXES
-- ============================================================

-- Range queries for backfill
CREATE INDEX IF NOT EXISTS ix_event_logs_block_number ON event_logs(block_number);

-- Find unprocessed events
CREATE INDEX IF NOT EXISTS ix_event_logs_unprocessed 
    ON event_logs(created_at) 
    WHERE processed = FALSE;

-- Filter by event type
CREATE INDEX IF NOT EXISTS ix_event_logs_event_name ON event_logs(event_name);

-- ============================================================
-- INDEXER_STATE INDEXES
-- ============================================================

-- Lookup by contract (already has unique constraint, this is explicit)
CREATE INDEX IF NOT EXISTS ix_indexer_state_contract ON indexer_state(contract_address);
