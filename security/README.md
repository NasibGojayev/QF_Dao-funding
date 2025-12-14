# DonCoin DAO - Security Module

A comprehensive security and monitoring implementation for the DonCoin DAO platform, including authentication, rate limiting, alerting, SIEM/SOAR, and a security operations dashboard.

## 🛡️ Features

### 1. Authentication & Authorization
- JWT-based authentication for admin endpoints
- Password hashing with bcrypt
- Session management with configurable expiry
- All admin access logged for audit trail

### 2. Rate Limiting
- Per-IP and per-endpoint rate limits
- Redis-backed storage (with in-memory fallback)
- Brute force detection and IP blocking
- Rate limit monitoring and statistics

### 3. Monitoring & KPIs
| KPI | Target | Alert Threshold |
|-----|--------|-----------------|
| Event Processing Lag | < 5s | > 60s (critical) |
| Error Rate | < 0.1% | > 2% (critical) |
| API Response Latency | < 200ms | > 1000ms (warning) |
| Suspicious TX Count | < 10/hr | > 10 (critical) |

### 4. Alerting System
- Configurable alert rules with thresholds
- Multi-channel notifications (log, email, webhook)
- Alert cooldown to prevent alert fatigue
- History and acknowledgment tracking

### 5. SIEM/SOAR
- Security event ingestion and logging
- Correlation rules for threat detection
- Automated response playbooks
- Case management for incidents

### 6. Data Retention
- Configurable retention policies per data type
- Automatic log rotation and archiving
- Compliance-ready audit logs (2-year retention)

## 🚀 Quick Start

### Installation

```bash
cd security

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Start Security API

```bash
python api/endpoints.py
# Open http://localhost:8070/docs for Swagger UI
```

### Start SOC Dashboard

```bash
python dashboard/app.py
# Open http://localhost:8060
```

### Run Tests

```bash
pytest tests/ -v
```

## 📁 Project Structure

```
security/
├── config/
│   ├── __init__.py
│   └── settings.py        # Central configuration
├── auth/
│   ├── __init__.py
│   └── authentication.py  # JWT auth, password hashing
├── middleware/
│   ├── __init__.py
│   └── rate_limiter.py    # Rate limiting middleware
├── monitoring/
│   ├── __init__.py
│   ├── metrics.py         # KPI collection
│   └── alerting.py        # Alert rules and notifications
├── siem/
│   ├── __init__.py
│   └── engine.py          # SIEM/SOAR engine
├── retention/
│   ├── __init__.py
│   └── manager.py         # Data retention management
├── dashboard/
│   └── app.py             # SOC dashboard (Dash)
├── api/
│   ├── __init__.py
│   └── endpoints.py       # FastAPI endpoints
├── docs/
│   └── THREAT_MODEL.md    # Threat model document
├── tests/
│   └── test_security.py   # Test suite
├── logs/                  # Log files directory
├── requirements.txt
└── README.md
```

## 🔌 API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Login and get JWT token |
| `/auth/me` | GET | Get current user info |

### Monitoring
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/metrics` | GET | Prometheus format metrics |
| `/api/v1/kpis` | GET | Get all KPI values |
| `/api/v1/kpis/{name}/history` | GET | KPI history |
| `/api/v1/baseline/create` | POST | Create KPI baseline |
| `/api/v1/baseline/compare` | GET | Compare to baseline |

### Alerting
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/alerts` | GET | Get active alerts |
| `/api/v1/alerts/history` | GET | Alert history |
| `/api/v1/alerts/acknowledge` | POST | Acknowledge alert |
| `/api/v1/alerts/test` | POST | Simulate fault for testing |

### SIEM
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/siem/events` | GET | Search security events |
| `/api/v1/siem/cases` | GET | Get security cases |
| `/api/v1/siem/cases/{id}` | PUT | Update case |

## 📊 Threat Model

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) for the full threat model including:
- Top 5 risks with likelihood/impact matrix
- Mitigation strategies
- Incident response playbooks
- Security architecture diagram

### Top Risks Summary
1. **Event Lag / Stale UI** - Monitored with alerts
2. **Fake Event Injection** - Event signature verification
3. **Unauthorized Admin Access** - JWT + rate limiting + logging
4. **API Abuse / DDoS** - Rate limiting + WAF
5. **Sybil Attack** - Risk scorer + suspicious TX detection

## 🧪 Testing Alerts

To test the alerting pipeline, use the `/api/v1/alerts/test` endpoint:

```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8070/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Simulate high event lag
curl -X POST http://localhost:8070/api/v1/alerts/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fault_type":"event_lag","value":75}'
```

## 🔧 Configuration

Edit `config/settings.py` to configure:
- Database connection
- Redis connection (for rate limiting)
- Authentication settings
- Rate limit thresholds
- KPI alert thresholds
- Notification channels

### Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=doncoin

# Authentication
SECRET_KEY=your-secret-key-change-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# Alerting
ALERT_EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
ALERT_RECIPIENTS=security@doncoin.dao
```

## 📋 Pass/Fail Criteria

| Criterion | Status |
|-----------|--------|
| KPIs Visible on Dashboard | ✅ |
| Alert Triggers Under Fault | ✅ |
| Security Controls Operational | ✅ |
| Admin Access Protected | ✅ |
| Rate Limiting Enforced | ✅ |
| Logs Captured Centrally | ✅ |
| Code Version Controlled | ✅ |

## 📜 License

Part of the DonCoin DAO project.
