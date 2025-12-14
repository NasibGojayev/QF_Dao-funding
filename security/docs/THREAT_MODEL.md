# DonCoin DAO - Threat Model One-Pager

## Overview
This document identifies the top 5 security risks for the DonCoin DAO platform and provides mitigation strategies.

---

## Risk Assessment Matrix

| ID | Threat | Likelihood | Impact | Risk Level | Owner |
|----|--------|------------|--------|------------|-------|
| T1 | Event Lag / Stale UI | Medium | High | **High** | Backend Team |
| T2 | Fake Event Injection | Low | Critical | **High** | Smart Contract Team |
| T3 | Unauthorized Admin Access | Medium | Critical | **Critical** | Security Team |
| T4 | API Abuse / DDoS | High | Medium | **High** | Infrastructure Team |
| T5 | Sybil Attack on Voting | Medium | High | **High** | Data Science Team |

---

## Threat Details & Mitigations

### T1: Event Lag Leading to Stale UI

**Description:** Delays in indexing blockchain events could show outdated proposal/donation data.

**Attack Vector:** 
- Network latency or indexer failure
- Database bottleneck during high load

**Impact:**
- Users see incorrect funding status
- Potential duplicate donations
- Loss of trust

**Mitigations:**
| Control | Implementation | Status |
|---------|----------------|--------|
| Real-time lag monitoring | System KPI: event_processing_lag | ✅ Implemented |
| Alert on lag > 60s | Alert rule configured | ✅ Implemented |
| Indexer health endpoint | /health check for indexer | ✅ Implemented |
| Frontend staleness indicator | Show "last updated" timestamp | 🔲 Pending |

---

### T2: Injection of Fake Events

**Description:** Attacker could inject fake blockchain events into the indexer.

**Attack Vector:**
- Compromised RPC endpoint
- Man-in-the-middle on indexer connection
- Direct database access

**Impact:**
- Fraudulent donations displayed
- Incorrect matching pool calculations
- Financial loss

**Mitigations:**
| Control | Implementation | Status |
|---------|----------------|--------|
| Event signature verification | Verify event comes from known contracts | ✅ Implemented |
| RPC endpoint authentication | Use authenticated RPC providers | ✅ Implemented |
| Idempotent event processing | Dedupe by tx_hash + log_index | ✅ Implemented |
| Audit log for all indexed events | ContractEvent model logs all | ✅ Implemented |
| Chain reorganization handling | Re-validate on reorg | 🔲 Pending |

---

### T3: Unauthorized Admin Access

**Description:** Unauthorized access to admin dashboard or privileged API endpoints.

**Attack Vector:**
- Credential theft / phishing
- Brute force login attempts
- Session hijacking
- Insider threat

**Impact:**
- Data exfiltration
- Configuration tampering
- Service disruption

**Mitigations:**
| Control | Implementation | Status |
|---------|----------------|--------|
| JWT-based authentication | Required for all admin endpoints | ✅ Implemented |
| Strong password policy | Min 12 chars, complexity required | ✅ Implemented |
| Rate limiting on login | 5 attempts per minute | ✅ Implemented |
| Admin access logging | All actions logged with user/IP | ✅ Implemented |
| Session timeout | 30-minute token expiry | ✅ Implemented |
| IP allowlisting | Optional restriction to trusted IPs | 🔲 Optional |
| MFA / 2FA | Future enhancement | 🔲 Planned |

---

### T4: API Abuse / DDoS

**Description:** Excessive API requests causing service degradation or denial.

**Attack Vector:**
- Automated bots
- Competitive attack
- Unintentional client bugs

**Impact:**
- Service unavailability
- Increased infrastructure costs
- Poor user experience

**Mitigations:**
| Control | Implementation | Status |
|---------|----------------|--------|
| Rate limiting | Per-IP and per-endpoint limits | ✅ Implemented |
| Rate limit monitoring | Log and alert on violations | ✅ Implemented |
| Request throttling | Slowdown under load | ✅ Implemented |
| WAF/CDN protection | External provider (Cloudflare) | 🔲 Production |
| Burst protection | Short-term spike handling | ✅ Implemented |

---

### T5: Sybil Attack on Voting/Matching

**Description:** Attacker creates multiple fake identities to manipulate QF matching.

**Attack Vector:**
- Multiple wallets from same entity
- Airdrop farming
- Wash trading donations

**Impact:**
- Unfair matching fund distribution
- Legitimate projects disadvantaged
- Platform credibility damage

**Mitigations:**
| Control | Implementation | Status |
|---------|----------------|--------|
| Sybil score integration | Scores from Gitcoin Passport | ✅ Implemented |
| Risk scorer model | ML-based anomaly detection | ✅ Implemented |
| Suspicious TX flagging | Real-time outlier detection | ✅ Implemented |
| Donation velocity limits | Max donations per wallet/time | ✅ Implemented |
| Manual review queue | Flag for human review | ✅ Implemented |
| On-chain identity verification | Future: zkProofs, POH | 🔲 Planned |

---

## Security Architecture Diagram

```
                    ┌─────────────────────────────────────────┐
                    │              EXTERNAL                   │
                    │  Users, Wallets, RPC Nodes              │
                    └─────────────┬───────────────────────────┘
                                  │
                    ┌─────────────▼───────────────────────────┐
                    │           WAF / CDN                     │
                    │     (Cloudflare - Production)           │
                    └─────────────┬───────────────────────────┘
                                  │
                    ┌─────────────▼───────────────────────────┐
                    │         RATE LIMITER                    │
                    │   Redis-backed, per-IP/endpoint         │
                    └─────────────┬───────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
┌────────▼───────┐    ┌───────────▼──────────┐    ┌───────▼────────┐
│   Frontend     │    │   Backend API        │    │  Admin API     │
│   (Public)     │    │   (Auth optional)    │    │  (Auth req.)   │
└────────────────┘    └───────────┬──────────┘    └───────┬────────┘
                                  │                       │
                    ┌─────────────▼───────────────────────▼─────┐
                    │              DATABASE                     │
                    │   PostgreSQL (encrypted at rest)          │
                    └─────────────┬─────────────────────────────┘
                                  │
                    ┌─────────────▼─────────────────────────────┐
                    │           SIEM / SOAR                     │
                    │  Log aggregation, alerting, response      │
                    └───────────────────────────────────────────┘
```

---

## Incident Response Playbooks

### Playbook 1: High Event Lag Alert
1. Check indexer health: `/health` endpoint
2. Verify RPC connectivity
3. Check database performance (slow queries)
4. Restart indexer if needed
5. Document in incident log

### Playbook 2: Brute Force Detection
1. Alert fires on 5+ failed logins
2. Automatically block IP for 15 minutes
3. Notify security team via webhook
4. Review logs for patterns
5. Consider permanent blocklist if repeated

### Playbook 3: Suspicious Transaction Spike
1. Alert fires when flagged TX > 10/hour
2. Review flagged transactions in dashboard
3. Check for common patterns (same origin, amounts)
4. Escalate to manual review if confirmed
5. Update risk scorer model if false positive

---

## Compliance & Audit Trail

| Requirement | Implementation |
|-------------|----------------|
| All admin actions logged | ✅ SIEM event logging |
| Audit logs immutable | ✅ Append-only JSONL files |
| Retention: 2 years | ✅ Configured in settings |
| Access logs include IP, user, timestamp | ✅ Structured logging |
| Failed auth attempts logged | ✅ SIEM integration |

---

## Review Schedule

| Review Type | Frequency | Owner |
|-------------|-----------|-------|
| Threat model update | Quarterly | Security Team |
| Penetration testing | Annually | External Vendor |
| Access review | Monthly | Admin |
| Alert rule tuning | Weekly | Operations |

---

*Document Version: 1.0*  
*Last Updated: December 2024*  
*Next Review: March 2025*
