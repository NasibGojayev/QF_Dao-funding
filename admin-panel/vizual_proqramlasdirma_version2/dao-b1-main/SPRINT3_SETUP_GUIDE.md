# Sprint 3 Setup & Installation Guide
## Data Science, Monitoring & Security

This guide covers installation, configuration, and deployment of Sprint 3 components.

---

## Prerequisites

- Python 3.9+
- pip or conda
- Node.js 16+ (for dashboard dependencies)
- Backend services running (Django, FastAPI)

---

## Installation Steps

### 1. Install Python Dependencies

```bash
cd backend

# Install Sprint 3 specific packages
pip install dash dash-bootstrap-components plotly
pip install scikit-learn xgboost
pip install imbalanced-learn mlxtend
pip install prometheus-client
pip install pandas numpy scipy

# Or install from requirements (if generated)
# pip install -r requirements-sprint3.txt
```

**Key Packages:**
- `scikit-learn`: Classical ML models (7 implemented)
- `xgboost`: Gradient boosting
- `imbalanced-learn`: SMOTE, ADASYN, BORDERLINE-SMOTE
- `mlxtend`: Association rules (Apriori)
- `prometheus-client`: Metrics export
- `dash` + `plotly`: Monitoring dashboard

### 2. Start Monitoring Dashboard

```bash
cd backend
python dashboard.py
```

**Expected Output:**
```
Running on http://0.0.0.0:8002
WARNING in app.run_server: This is a development server. Do not use it in production.
```

**Access Dashboard:**
- Open: `http://localhost:8002` in browser
- You should see 6 KPI cards and multiple timeline charts

### 3. Run Data Science Notebook

```bash
jupyter notebook sprint3_data_science.ipynb
```

The notebook will:
1. Generate synthetic materialized view data
2. Perform EDA and feature engineering
3. Train 7 ML models
4. Execute A/B test and MAB simulation
5. Evaluate statistical significance
6. Generate all visualizations

**Estimated Runtime:** 5-10 minutes

### 4. Test Integration

```bash
cd backend
pytest test_sprint3.py -v
```

**Expected Output:**
```
tests/test_sprint3.py::TestMonitoring::test_kpi_tracker_update PASSED
tests/test_sprint3.py::TestMonitoring::test_alert_creation PASSED
tests/test_sprint3.py::TestModelInference::test_high_value_scoring PASSED
...
======================== 15 passed in 2.34s ========================
```

### 5. Verify SIEM/SOAR Integration

```bash
cd backend
python siem_soar.py
```

**Expected Output:**
```
=== Threat Model Registry ===
# Threat Model
## T001: PERFORMANCE_DEGRADATION
...
=== Event Correlation Demo ===
Event Summary:
{'total_events': 2, 'critical_events': 0, ...}

✅ SIEM/SOAR integration ready
```

### 6. Test Model Inference Pipeline

```bash
cd backend
python inference.py
```

**Expected Output:**
```
=== Model Inference Pipeline Demo ===
Loading pre-trained models...
✅ Models loaded successfully

Testing High-Value User Scoring...
Score: 0.689, Decision: {'score': ..., 'is_high_value': True, ...}
...
✅ Pipeline demo complete
```

---

## Configuration

### Alert Thresholds (in `monitoring.py`)

```python
alert_manager.thresholds = {
    'event_processing_lag_critical': 60,  # seconds
    'error_rate_critical': 2.0,  # percentage
    'api_latency_warning': 1000,  # milliseconds
    'suspicious_transactions_critical': 50,  # count
}
```

**To Modify:**
1. Edit `backend/monitoring.py`
2. Update thresholds dict
3. Restart dashboard: `python dashboard.py`

### Model Inference Config (in `inference.py`)

```python
# High-value threshold
high_value_threshold = 0.6  # Probability > 60% considered high-value

# Risk thresholds
risk_approve = 0.4  # Risk < 40% → approve transaction
risk_review = 0.7   # Risk 40-70% → require review
risk_block = 0.7    # Risk > 70% → block transaction
```

### Dashboard Port

Default: `8002`

**To Change:**
```python
# In dashboard.py, last line:
if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8003)  # Change 8002 to 8003
```

---

## Monitoring Dashboard Quick Start

### Main Views

**1. KPI Cards (Top Row)**
- Event Processing Lag (current value in seconds)
- Error Rate (current percentage)
- API Latency P95 (milliseconds)

**2. Alerts Section**
- Shows active CRITICAL and WARNING alerts
- Dismissable with X button
- Auto-updates every 5 seconds

**3. KPI Timelines (Charts)**
- Event lag timeline with 60s threshold line
- Error rate timeline with 2% threshold
- API latency timeline
- Suspicious transaction count (bar chart)
- Conversion rate timeline

**4. Model Inference Log**
- Recent model predictions
- Model name, score, latency
- Scrollable table

**5. Alert Configuration**
- Adjust alert thresholds
- Save button persists changes
- Refresh dashboard to apply

**6. A/B Test Status**
- Bar chart comparing conversion rates
- Variant performance ranking

### Simulating Alerts

The dashboard uses simulated data. To trigger an alert:

```python
# In monitoring.py, test_alert() function:
kpi_tracker.update_event_lag(65)  # Exceeds 60s threshold
# Dashboard will show 🚨 CRITICAL alert
```

---

## Integration with Backend

### Connecting Model Inference to API

```python
# In fastapi_service/main.py (or api/views.py)

from inference import score_user_for_ui_personalization, score_transaction_for_gating

@app.post("/api/score-transaction")
async def score_transaction(user_id: int, transaction: dict):
    """Score transaction for gating"""
    decision = score_transaction_for_gating(user_id, transaction)
    
    if decision['action'] == 'block':
        return {"error": decision['block_reason']}, 403
    
    return decision

@app.get("/api/user-personalization/{user_id}")
async def get_user_personalization(user_id: int):
    """Get personalization variant for user"""
    features = fetch_user_features(user_id)  # Your feature store
    personalization = score_user_for_ui_personalization(user_id, features)
    return personalization
```

### Connecting Monitoring to Django

```python
# In api/views.py

from monitoring import kpi_tracker, alert_manager, inference_logger

class ProjectViewSet(viewsets.ModelViewSet):
    def list(self, request):
        start = time.time()
        response = super().list(request)
        latency_ms = (time.time() - start) * 1000
        
        # Log latency
        kpi_tracker.update_latency(latency_ms)
        
        # Check alert
        if latency_ms > 1000:
            alert_manager.check_and_alert('api_latency', latency_ms, 1000)
        
        return response
```

---

## Troubleshooting

### Dashboard Won't Start

```bash
# Check if port 8002 is in use
lsof -i :8002

# Kill process on port 8002
kill -9 <PID>

# Try alternate port
python dashboard.py  # Edit port in code if needed
```

### Model Inference Errors

```bash
# Check models are loaded
python -c "from inference import pipeline; pipeline.load_models()"

# Verify feature format
python -c "from inference import pipeline; pipeline.score_user_high_value_likelihood({'total_amount': 100})"
```

### Test Failures

```bash
# Run with verbose output
pytest test_sprint3.py -v -s

# Run specific test
pytest test_sprint3.py::TestModelInference::test_high_value_scoring -v
```

### SIEM Event Correlation Issues

```python
# Test event correlation
from siem_soar import EventCorrelator
correlator = EventCorrelator()
# Check correlator.get_event_summary()
```

---

## Performance Tuning

### Reduce Model Inference Latency

```python
# In inference.py
# Use simpler models for real-time (e.g., logistic regression instead of XGBoost)
# Cache model predictions for same features
# Batch inference for bulk scoring
```

### Dashboard Refresh Rate

```python
# In dashboard.py
dcc.Interval(id="refresh-interval", interval=5000, n_intervals=0)
# Change 5000ms (5 sec) to higher for less frequent updates
```

### Memory Optimization

```python
# Reduce history size in KPI tracker
kpi_tracker = KPITracker(max_history=360)  # 6 hours instead of 1 day
```

---

## Security Hardening

### Protect Dashboard Access

```python
# Add authentication middleware (Flask/Dash)
@app.server.before_request
def check_auth():
    token = request.headers.get('Authorization')
    if not validate_token(token):
        return {"error": "Unauthorized"}, 401
```

### Secure Alert Configuration

```python
# Make threshold changes require admin token
@app.callback(
    Output("alerts-config", "data"),
    Input("save-config-btn", "n_clicks"),
    prevent_initial_call=True
)
def save_config(n_clicks):
    # Verify admin token before saving
    if not is_admin(request.headers.get('Authorization')):
        raise PreventUpdate
    # ... save config
```

### Log Sensitive Data

```python
# Redact user IDs/wallets in logs
def safe_log(message, user_id=None, wallet=None):
    safe_msg = message.replace(user_id or "", "***")
    safe_msg = safe_msg.replace(wallet or "", "0x****")
    logger.info(safe_msg)
```

---

## Deployment Checklist

- [ ] Models loaded successfully (test_sprint3.py passes)
- [ ] Dashboard accessible at configured port
- [ ] Alerts triggering correctly (test with artificial spike)
- [ ] SIEM event correlation working
- [ ] Rate-limiting enforced on all endpoints
- [ ] Admin endpoints protected with auth
- [ ] Monitoring logs written to file or central store
- [ ] Documentation reviewed and approved
- [ ] Threat model reviewed by security team
- [ ] Baseline KPIs recorded for comparison

---

## Support & Escalation

For issues:

1. **Data Science Questions:** See Sprint 3 Notebook
2. **Dashboard Issues:** Check `backend/dashboard.py` logs
3. **Model Inference:** Test `backend/inference.py` directly
4. **Security Concerns:** Reference `SPRINT3_THREAT_MODEL.md`
5. **Integration Help:** Check `test_sprint3.py` examples

---

**Last Updated:** December 8, 2025  
**Version:** 1.0  
**Status:** ✅ Ready for Deployment
