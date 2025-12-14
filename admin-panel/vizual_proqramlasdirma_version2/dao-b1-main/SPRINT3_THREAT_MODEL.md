# Sprint 3: Threat Model One-Pager
## Quadratic Funding DAO - Security & Risk Assessment

**Date:** December 8, 2025  
**Review Cycle:** Quarterly | **Last Review:** Initial  
**Status:** In Development

---

## Executive Summary

This document outlines the top 5 security risks for the DAO quadratic funding platform, with likelihood/impact assessment and mitigation strategies. Risks range from **operational (event lag)** to **critical (injection attacks)**, with owners assigned for accountability.

---

## Risk Matrix (Likelihood × Impact)

| Risk ID | Threat | L | I | Score | Status |
|---------|--------|---|---|-------|--------|
| **T001** | Event Processing Lag | 4 | 3 | **12/25** ⚠️ | Active Monitoring |
| **T002** | Injection Attacks (SQL/Smart Contract) | 2 | 5 | **10/25** 🔴 | Controlled |
| **T003** | Unauthorized Admin Access | 2 | 5 | **10/25** 🔴 | Controlled |
| **T004** | Sensitive Data Exposure | 1 | 5 | **5/25** 🟡 | Preventive |
| **T005** | Rate-Limit Bypass / DDoS | 3 | 3 | **9/25** ⚠️ | Active Monitoring |

**L = Likelihood (1-5), I = Impact (1-5)**

---

## T001: Event Processing Lag > 60 Seconds ⚠️

**Likelihood:** 4/5 (Moderately Probable)  
**Impact:** 3/5 (Significant)  
**Risk Score:** 12/25

**Description:**  
Event indexing service falls behind real-time demands, causing UI to show stale data. Users see outdated balances, project lists, or round statuses. Erodes trust and may trigger cascading customer support issues.

### Mitigations

| Control | Owner | Status | Evidence |
|---------|-------|--------|----------|
| **Queue Monitoring & Auto-scaling** | DevOps | Implemented | CloudWatch metrics for queue depth |
| **Alert at 60s threshold** | DevOps | Implemented | Monitoring module triggers alert |
| **Circuit Breaker Pattern** | Backend Team | Planned | Fail-open to materialized view if lag detected |
| **Graceful Degradation UI** | Frontend Team | Planned | Show cached data + "data may be stale" banner |

**KPI:** Event processing lag max < 30s (99th percentile)

---

## T002: Injection Attacks (SQL / Smart Contract) 🔴

**Likelihood:** 2/5 (Rare but Catastrophic if Exploited)  
**Impact:** 5/5 (Critical - Full System Compromise)  
**Risk Score:** 10/25

**Description:**  
Attacker injects malicious SQL via API parameters or calls malicious smart contract methods via untrusted input. Could lead to data exfiltration, contract fund theft, or arbitrary code execution.

### Mitigations

| Control | Owner | Status | Evidence |
|---------|-------|--------|----------|
| **Parameterized Queries (ORM)** | Backend Team | Implemented | Django ORM prevents SQL injection |
| **Pydantic Input Validation** | Backend Team | Implemented | Type checking + max length constraints |
| **Contract ABI Validation** | Smart Contract Team | Implemented | ABIs extracted & validated in frontend |
| **Rate Limiting** | Backend Team | Implemented | SlowAPI 100req/min per IP |
| **Security Audits (Annual)** | Security Team | Planned | Budget for external audit Q2 2026 |
| **Web Application Firewall** | DevOps | Planned | Cloudflare/WAF for HTTP layer |

**KPI:** 0 successful injections (security audit confirmed)

---

## T003: Unauthorized Admin Access 🔴

**Likelihood:** 2/5 (Rare but High Impact if Breached)  
**Impact:** 5/5 (Critical - Admin Control)  
**Risk Score:** 10/25

**Description:**  
Attacker gains unauthorized access to admin dashboard (/api/admin, /admin/settings). Could modify user data, reset passwords, drain funds, or tamper with smart contract parameters.

### Mitigations

| Control | Owner | Status | Evidence |
|---------|-------|--------|----------|
| **Token-Based Authentication** | Backend Team | Implemented | DRF authtoken required for all endpoints |
| **Admin Dashboard Behind JWT** | Backend Team | Implemented | /api/admin requires valid JWT token |
| **IP Whitelist for Admin** | DevOps | Planned | Restrict /api/admin to office IPs only |
| **Login Rate Limiting** | Backend Team | Implemented | 5 failed attempts/min → account lock |
| **MFA for Admin Accounts** | Security Team | Planned | TOTP support in next sprint |
| **Admin Access Audit Log** | Backend Team | Implemented | All admin actions logged to central SIEM |

**KPI:** 0 unauthorized admin access attempts (audit logs reviewed weekly)

---

## T004: Sensitive Data Exposure 🟡

**Likelihood:** 1/5 (Rare - mainly accidental)  
**Impact:** 5/5 (Critical - Privacy Violation, GDPR)  
**Risk Score:** 5/25

**Description:**  
User PII (wallet addresses, balances), private API keys, or transaction details accidentally leaked in logs, error messages, or backups.

### Mitigations

| Control | Owner | Status | Evidence |
|---------|-------|--------|----------|
| **Data Retention Policy** | DPO | Implemented | See: Data Control section |
| **Automatic PII Redaction** | Backend Team | Planned | Log processor masks wallet addresses |
| **Encrypted Sensitive Columns** | Backend Team | Planned | Encrypt user PII at rest |
| **Access Controls on Database** | DevOps | Implemented | DB credentials rotated monthly |
| **Regular Audit of Logs** | Security Team | Planned | Monthly review of log contents |
| **GDPR Compliance** | DPO | Planned | User deletion workflow; 30-day retention for transient logs |

**KPI:** 0 data breach incidents (incident response plan reviewed quarterly)

---

## T005: Rate-Limit Bypass / DDoS ⚠️

**Likelihood:** 3/5 (Moderately Probable)  
**Impact:** 3/5 (Service Degradation)  
**Risk Score:** 9/25

**Description:**  
Attacker bypasses rate limits by spoofing IP headers, using distributed botnets, or exploiting unprotected endpoints. Results in service unavailability for legitimate users.

### Mitigations

| Control | Owner | Status | Evidence |
|---------|-------|--------|----------|
| **Rate Limiting (Token Bucket)** | Backend Team | Implemented | SlowAPI 100req/min per IP |
| **Rate Limit by User ID** | Backend Team | Implemented | Also track per user_id, not just IP |
| **Detect Distributed Patterns** | Monitoring | Implemented | Alert if 20+ IPs same user_id in 1min |
| **WAF with DDoS Protection** | DevOps | Planned | Cloudflare DDoS mitigation |
| **Monitor Rate-Limit Hooks** | DevOps | Implemented | Alert on rate-limit violations |
| **Proof-of-Work Challenge** | Frontend Team | Planned | Client-side hash validation on burst |

**KPI:** Event processing latency < 500ms (p95) during attack simulation

---

## Owners & Escalation Path

| Owner Role | Name | Escalation | Review Freq |
|------------|------|-----------|------------|
| **DevOps Lead** | [TBD] | CTO | Monthly |
| **Backend Team Lead** | [TBD] | Engineering Manager | Weekly |
| **Security Team** | [TBD] | Chief Security Officer | Quarterly |
| **DPO (Data Protection Officer)** | [TBD] | Legal | Quarterly |

---

## Response Procedures

### Incident Report Template
```
INCIDENT ID: [INC-YYYYMMDD-NNN]
Severity: [CRITICAL / HIGH / MEDIUM / LOW]
Threat ID: [T001-T005]
Discoverer: [Name]
Time Detected: [ISO timestamp]
Time Resolved: [ISO timestamp]
Root Cause: [Description]
Impact: [# users affected, $ loss, etc]
Remediation: [Actions taken]
Prevention: [Changes to prevent recurrence]
```

### Escalation Levels
1. **CRITICAL:** Immediate notification to CTO + On-call Security Lead
2. **HIGH:** Engineering Manager + Security Team within 1 hour
3. **MEDIUM:** Team Lead + Security Review within 24 hours
4. **LOW:** Team Lead + Next sprint planning

---

## References

- **SIEM/SOAR Integration:** See `backend/siem_soar.py`
- **Monitoring Dashboard:** See `backend/dashboard.py`
- **Data Retention Policy:** See Sprint 3 Data Science Notebook
- **Rate-Limiting Configuration:** See `backend/monitoring.py`
- **Compliance:** GDPR Article 32 (security); SOC 2 Type II audit roadmap

---

**Approved By:** [Pending]  
**Next Review:** [90 days / Q1 2026]
