-- ============================================================
-- DAO Workflow SQL Queries
-- Complete user journey from registration to payout
-- ============================================================

-- ============================================================
-- 1. USER REGISTRATION WORKFLOW
-- ============================================================

-- Check if username is available
SELECT NOT EXISTS (SELECT 1 FROM donors WHERE username = 'new_user') AS available;

-- Register new user
INSERT INTO donors (username, email, password_hash)
VALUES ('new_user', 'new@user.com', '$2b$12$hashed_password_here')
RETURNING donor_id, username, joined_at;

-- ============================================================
-- 2. USER LOGIN WORKFLOW
-- ============================================================

-- Authenticate user (verify credentials in application layer)
SELECT donor_id, username, password_hash, is_active
FROM donors
WHERE username = 'alice_dao';

-- Create session on successful login
INSERT INTO user_sessions (donor_id, token, ip_address, expires_at)
VALUES ('aaaa1111-aaaa-1111-aaaa-111111111111', 'generated_token_here', '192.168.1.1', NOW() + INTERVAL '8 hours')
RETURNING session_id, token;

-- Update last login
UPDATE donors SET last_login = NOW() WHERE donor_id = 'aaaa1111-aaaa-1111-aaaa-111111111111';

-- ============================================================
-- 3. SESSION VALIDATION WORKFLOW
-- ============================================================

-- Validate session token
SELECT 
    s.donor_id,
    d.username,
    COALESCE(g.role, 'member') AS role,
    s.expires_at > NOW() AS is_valid
FROM user_sessions s
JOIN donors d ON s.donor_id = d.donor_id
LEFT JOIN wallets w ON d.wallet_id = w.wallet_id
LEFT JOIN governance_token g ON w.wallet_id = g.wallet_id
WHERE s.token = 'user_token_here' AND s.is_active = TRUE;

-- ============================================================
-- 4. WALLET CONNECTION WORKFLOW
-- ============================================================

-- Create or get wallet
INSERT INTO wallets (address)
VALUES ('0x1234567890123456789012345678901234567890')
ON CONFLICT (address) DO UPDATE SET last_activity = NOW()
RETURNING wallet_id;

-- Link wallet to user
UPDATE donors SET wallet_id = 'wallet_uuid_here' WHERE donor_id = 'donor_uuid_here';

-- Initialize sybil score for new wallet
INSERT INTO sybil_scores (wallet_id, score, verified_by)
VALUES ('wallet_uuid_here', 0.5, 'Initial');

-- ============================================================
-- 5. VIEW ACTIVE ROUNDS
-- ============================================================

SELECT 
    r.round_id,
    r.title,
    r.description,
    r.start_date,
    r.end_date,
    r.status,
    mp.total_funds,
    mp.allocated_funds,
    (mp.total_funds - mp.allocated_funds) AS available_funds,
    COUNT(DISTINCT p.proposal_id) AS proposals_count
FROM rounds r
LEFT JOIN matching_pool mp ON r.matching_pool_id = mp.pool_id
LEFT JOIN proposals p ON r.round_id = p.round_id
WHERE r.status = 'active'
GROUP BY r.round_id, r.title, r.description, r.start_date, r.end_date, r.status,
         mp.total_funds, mp.allocated_funds;

-- ============================================================
-- 6. VIEW PROPOSALS IN ROUND
-- ============================================================

SELECT 
    p.proposal_id,
    p.title,
    p.description,
    p.status,
    p.total_donations,
    d.username AS proposer,
    COALESCE(m.matched_amount, 0) AS matched_amount,
    (p.total_donations + COALESCE(m.matched_amount, 0)) AS total_funding,
    COUNT(DISTINCT dn.donation_id) AS donor_count
FROM proposals p
JOIN donors d ON p.proposer_id = d.donor_id
LEFT JOIN matches m ON p.proposal_id = m.proposal_id
LEFT JOIN donations dn ON p.proposal_id = dn.proposal_id
WHERE p.round_id = 'r3333333-3333-3333-3333-333333333333'
  AND p.status IN ('approved', 'pending')
GROUP BY p.proposal_id, p.title, p.description, p.status, p.total_donations,
         d.username, m.matched_amount
ORDER BY total_funding DESC;

-- ============================================================
-- 7. SUBMIT PROPOSAL WORKFLOW
-- ============================================================

-- Create new proposal
INSERT INTO proposals (title, description, proposer_id, round_id)
VALUES (
    'My Amazing Project',
    'Detailed description of the project...',
    'aaaa1111-aaaa-1111-aaaa-111111111111',
    'r3333333-3333-3333-3333-333333333333'
)
RETURNING proposal_id, created_at;

-- Log contract event
INSERT INTO contract_events (event_type, round_id, proposal_id, tx_hash, block_number)
VALUES ('ProposalSubmitted', 'r3333333-3333-3333-3333-333333333333', 'new_proposal_id', '0xtxhash...', 19600000);

-- ============================================================
-- 8. DONATE TO PROPOSAL WORKFLOW
-- ============================================================

-- Get donor's sybil score
SELECT ss.score FROM sybil_scores ss
JOIN wallets w ON ss.wallet_id = w.wallet_id
JOIN donors d ON d.wallet_id = w.wallet_id
WHERE d.donor_id = 'aaaa1111-aaaa-1111-aaaa-111111111111';

-- Create donation
INSERT INTO donations (donor_id, proposal_id, amount, sybil_score, tx_hash)
VALUES (
    'aaaa1111-aaaa-1111-aaaa-111111111111',
    'p2222222-2222-2222-2222-222222222222',
    50.000000000000000000,
    0.92,
    '0xdonation_tx_hash...'
)
RETURNING donation_id, created_at;

-- Update proposal total
UPDATE proposals 
SET total_donations = total_donations + 50.000000000000000000,
    updated_at = NOW()
WHERE proposal_id = 'p2222222-2222-2222-2222-222222222222';

-- Update donor reputation
UPDATE donors 
SET reputation_score = LEAST(1.0, reputation_score + 0.01)
WHERE donor_id = 'aaaa1111-aaaa-1111-aaaa-111111111111';

-- Log event
INSERT INTO contract_events (event_type, round_id, proposal_id, tx_hash)
VALUES ('DonationReceived', 'r3333333-3333-3333-3333-333333333333', 'p2222222-2222-2222-2222-222222222222', '0xdonation_tx_hash...');

-- ============================================================
-- 9. QUADRATIC FUNDING CALCULATION
-- ============================================================

-- Calculate QF match for a proposal using sum of square roots formula
WITH donation_roots AS (
    SELECT 
        proposal_id,
        SQRT(amount * sybil_score) AS weighted_sqrt
    FROM donations
    WHERE proposal_id = 'p2222222-2222-2222-2222-222222222222'
),
qf_calculation AS (
    SELECT 
        proposal_id,
        POWER(SUM(weighted_sqrt), 2) - SUM(weighted_sqrt * weighted_sqrt) AS qf_match
    FROM donation_roots
    GROUP BY proposal_id
)
INSERT INTO qf_results (round_id, proposal_id, calculated_match)
SELECT 'r3333333-3333-3333-3333-333333333333', proposal_id, qf_match
FROM qf_calculation
ON CONFLICT DO NOTHING;

-- ============================================================
-- 10. USER DASHBOARD DATA
-- ============================================================

-- Get user's donations with proposal info
SELECT 
    dn.donation_id,
    dn.amount,
    dn.created_at,
    p.title AS proposal_title,
    p.status AS proposal_status,
    r.title AS round_title
FROM donations dn
JOIN proposals p ON dn.proposal_id = p.proposal_id
LEFT JOIN rounds r ON p.round_id = r.round_id
WHERE dn.donor_id = 'aaaa1111-aaaa-1111-aaaa-111111111111'
ORDER BY dn.created_at DESC;

-- Get user's proposals
SELECT 
    p.proposal_id,
    p.title,
    p.status,
    p.total_donations,
    COALESCE(m.matched_amount, 0) AS matched_amount,
    r.title AS round_title,
    COUNT(DISTINCT dn.donation_id) AS supporters
FROM proposals p
LEFT JOIN matches m ON p.proposal_id = m.proposal_id
LEFT JOIN rounds r ON p.round_id = r.round_id
LEFT JOIN donations dn ON p.proposal_id = dn.proposal_id
WHERE p.proposer_id = 'aaaa1111-aaaa-1111-aaaa-111111111111'
GROUP BY p.proposal_id, p.title, p.status, p.total_donations, m.matched_amount, r.title;

-- ============================================================
-- 11. ADMIN: APPROVE/REJECT PROPOSAL
-- ============================================================

-- Approve proposal
UPDATE proposals 
SET status = 'approved', updated_at = NOW()
WHERE proposal_id = 'p4444444-4444-4444-4444-444444444444';

-- Reject proposal
UPDATE proposals 
SET status = 'rejected', updated_at = NOW()
WHERE proposal_id = 'p5555555-5555-5555-5555-555555555555';

-- Log admin action
INSERT INTO contract_events (event_type, proposal_id)
VALUES ('ProposalApproved', 'p4444444-4444-4444-4444-444444444444');

-- ============================================================
-- 12. PAYOUT DISTRIBUTION
-- ============================================================

-- Create payout record
INSERT INTO payouts (proposal_id, round_id, amount, tx_hash, status)
VALUES (
    'p2222222-2222-2222-2222-222222222222',
    'r3333333-3333-3333-3333-333333333333',
    7700.000000000000000000,  -- donations + match
    '0xpayout_tx_hash...',
    'pending'
);

-- Update to completed
UPDATE payouts 
SET status = 'completed', distributed_at = NOW()
WHERE proposal_id = 'p2222222-2222-2222-2222-222222222222' 
  AND round_id = 'r3333333-3333-3333-3333-333333333333';

-- Update proposal status
UPDATE proposals SET status = 'funded' WHERE proposal_id = 'p2222222-2222-2222-2222-222222222222';

-- ============================================================
-- 13. LOGOUT
-- ============================================================

UPDATE user_sessions SET is_active = FALSE WHERE token = 'user_token_here';
