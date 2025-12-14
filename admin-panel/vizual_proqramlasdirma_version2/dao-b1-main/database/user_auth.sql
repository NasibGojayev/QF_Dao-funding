-- ============================================================
-- User Authentication SQL Functions
-- Registration, Login, Session Management
-- ============================================================

-- ============================================================
-- REGISTER NEW USER
-- ============================================================
CREATE OR REPLACE FUNCTION register_user(
    p_username VARCHAR(100),
    p_email VARCHAR(255),
    p_password_hash VARCHAR(255)
) RETURNS TABLE(
    success BOOLEAN,
    message VARCHAR(255),
    donor_id UUID
) AS $$
DECLARE
    v_donor_id UUID;
BEGIN
    -- Check if username exists
    IF EXISTS (SELECT 1 FROM donors WHERE username = p_username) THEN
        RETURN QUERY SELECT FALSE, 'Username already exists'::VARCHAR(255), NULL::UUID;
        RETURN;
    END IF;
    
    -- Check if email exists
    IF p_email IS NOT NULL AND EXISTS (SELECT 1 FROM donors WHERE email = p_email) THEN
        RETURN QUERY SELECT FALSE, 'Email already registered'::VARCHAR(255), NULL::UUID;
        RETURN;
    END IF;
    
    -- Insert new donor
    INSERT INTO donors (username, email, password_hash)
    VALUES (p_username, p_email, p_password_hash)
    RETURNING donors.donor_id INTO v_donor_id;
    
    RETURN QUERY SELECT TRUE, 'Registration successful'::VARCHAR(255), v_donor_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- USER LOGIN
-- ============================================================
CREATE OR REPLACE FUNCTION login_user(
    p_username VARCHAR(100),
    p_password_hash VARCHAR(255),
    p_ip_address VARCHAR(45) DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
) RETURNS TABLE(
    success BOOLEAN,
    message VARCHAR(255),
    token VARCHAR(255),
    donor_id UUID,
    username VARCHAR(100)
) AS $$
DECLARE
    v_donor_id UUID;
    v_username VARCHAR(100);
    v_stored_hash VARCHAR(255);
    v_is_active BOOLEAN;
    v_token VARCHAR(255);
BEGIN
    -- Get user info
    SELECT d.donor_id, d.username, d.password_hash, d.is_active
    INTO v_donor_id, v_username, v_stored_hash, v_is_active
    FROM donors d
    WHERE d.username = p_username;
    
    -- Check if user exists
    IF v_donor_id IS NULL THEN
        RETURN QUERY SELECT FALSE, 'User not found'::VARCHAR(255), NULL::VARCHAR(255), NULL::UUID, NULL::VARCHAR(100);
        RETURN;
    END IF;
    
    -- Check if account is active
    IF NOT v_is_active THEN
        RETURN QUERY SELECT FALSE, 'Account is deactivated'::VARCHAR(255), NULL::VARCHAR(255), NULL::UUID, NULL::VARCHAR(100);
        RETURN;
    END IF;
    
    -- Verify password (in production, use bcrypt comparison in application layer)
    IF v_stored_hash != p_password_hash THEN
        RETURN QUERY SELECT FALSE, 'Invalid password'::VARCHAR(255), NULL::VARCHAR(255), NULL::UUID, NULL::VARCHAR(100);
        RETURN;
    END IF;
    
    -- Generate session token
    v_token := encode(gen_random_bytes(32), 'hex');
    
    -- Create session
    INSERT INTO user_sessions (donor_id, token, ip_address, user_agent, expires_at)
    VALUES (v_donor_id, v_token, p_ip_address, p_user_agent, CURRENT_TIMESTAMP + INTERVAL '8 hours');
    
    -- Update last login
    UPDATE donors SET last_login = CURRENT_TIMESTAMP WHERE donors.donor_id = v_donor_id;
    
    RETURN QUERY SELECT TRUE, 'Login successful'::VARCHAR(255), v_token, v_donor_id, v_username;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- VALIDATE SESSION
-- ============================================================
CREATE OR REPLACE FUNCTION validate_session(
    p_token VARCHAR(255)
) RETURNS TABLE(
    is_valid BOOLEAN,
    donor_id UUID,
    username VARCHAR(100),
    role VARCHAR(20)
) AS $$
DECLARE
    v_donor_id UUID;
    v_username VARCHAR(100);
    v_expires_at TIMESTAMP;
    v_is_active BOOLEAN;
    v_role VARCHAR(20);
BEGIN
    -- Get session info
    SELECT s.donor_id, s.expires_at, s.is_active
    INTO v_donor_id, v_expires_at, v_is_active
    FROM user_sessions s
    WHERE s.token = p_token;
    
    -- Check if session exists and is valid
    IF v_donor_id IS NULL OR NOT v_is_active OR v_expires_at < CURRENT_TIMESTAMP THEN
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::VARCHAR(100), NULL::VARCHAR(20);
        RETURN;
    END IF;
    
    -- Get user info and role
    SELECT d.username, COALESCE(g.role, 'member')
    INTO v_username, v_role
    FROM donors d
    LEFT JOIN wallets w ON d.wallet_id = w.wallet_id
    LEFT JOIN governance_token g ON w.wallet_id = g.wallet_id
    WHERE d.donor_id = v_donor_id;
    
    RETURN QUERY SELECT TRUE, v_donor_id, v_username, v_role;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- LOGOUT USER
-- ============================================================
CREATE OR REPLACE FUNCTION logout_user(
    p_token VARCHAR(255)
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE user_sessions 
    SET is_active = FALSE 
    WHERE token = p_token;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- CONNECT WALLET TO USER
-- ============================================================
CREATE OR REPLACE FUNCTION connect_wallet(
    p_donor_id UUID,
    p_wallet_address VARCHAR(66)
) RETURNS TABLE(
    success BOOLEAN,
    message VARCHAR(255),
    wallet_id UUID
) AS $$
DECLARE
    v_wallet_id UUID;
BEGIN
    -- Check if wallet already exists
    SELECT w.wallet_id INTO v_wallet_id
    FROM wallets w
    WHERE w.address = p_wallet_address;
    
    -- Create wallet if it doesn't exist
    IF v_wallet_id IS NULL THEN
        INSERT INTO wallets (address)
        VALUES (p_wallet_address)
        RETURNING wallets.wallet_id INTO v_wallet_id;
    END IF;
    
    -- Check if wallet is already connected to another user
    IF EXISTS (SELECT 1 FROM donors WHERE donors.wallet_id = v_wallet_id AND donors.donor_id != p_donor_id) THEN
        RETURN QUERY SELECT FALSE, 'Wallet already connected to another account'::VARCHAR(255), NULL::UUID;
        RETURN;
    END IF;
    
    -- Connect wallet to user
    UPDATE donors SET wallet_id = v_wallet_id WHERE donors.donor_id = p_donor_id;
    
    -- Initialize sybil score
    INSERT INTO sybil_scores (wallet_id, score, verified_by)
    VALUES (v_wallet_id, 0.5, 'system')
    ON CONFLICT DO NOTHING;
    
    RETURN QUERY SELECT TRUE, 'Wallet connected successfully'::VARCHAR(255), v_wallet_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- GET USER PROFILE
-- ============================================================
CREATE OR REPLACE FUNCTION get_user_profile(
    p_donor_id UUID
) RETURNS TABLE(
    donor_id UUID,
    username VARCHAR(100),
    email VARCHAR(255),
    wallet_address VARCHAR(66),
    reputation_score FLOAT,
    sybil_score FLOAT,
    voting_power DECIMAL,
    role VARCHAR(20),
    joined_at TIMESTAMP,
    total_donations DECIMAL,
    proposals_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.donor_id,
        d.username,
        d.email,
        w.address,
        d.reputation_score,
        ss.score,
        COALESCE(g.voting_power, 0::DECIMAL),
        COALESCE(g.role, 'member'::VARCHAR(20)),
        d.joined_at,
        COALESCE(SUM(dn.amount), 0::DECIMAL),
        COUNT(DISTINCT p.proposal_id)
    FROM donors d
    LEFT JOIN wallets w ON d.wallet_id = w.wallet_id
    LEFT JOIN sybil_scores ss ON w.wallet_id = ss.wallet_id
    LEFT JOIN governance_token g ON w.wallet_id = g.wallet_id
    LEFT JOIN donations dn ON d.donor_id = dn.donor_id
    LEFT JOIN proposals p ON d.donor_id = p.proposer_id
    WHERE d.donor_id = p_donor_id
    GROUP BY d.donor_id, d.username, d.email, w.address, d.reputation_score, 
             ss.score, g.voting_power, g.role, d.joined_at;
END;
$$ LANGUAGE plpgsql;
