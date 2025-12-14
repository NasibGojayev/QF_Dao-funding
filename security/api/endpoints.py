"""
Security API Endpoints
FastAPI application for security monitoring and administration.
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth.authentication import (
    Token, LoginRequest, User, login, get_current_user, 
    get_current_admin, get_client_ip, log_admin_access
)
from middleware.rate_limiter import RateLimitMiddleware, brute_force_detector, rate_limit_stats
from monitoring.metrics import (
    metrics_collector, create_baseline_snapshot, 
    compare_to_baseline, record_event_lag
)
from monitoring.alerting import alert_manager, simulate_alert_test
from siem.engine import siem_engine, EventCategory
from retention.manager import retention_manager
from config.settings import MONITORING_KPIS


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class AlertAcknowledge(BaseModel):
    alert_id: str


class CaseUpdate(BaseModel):
    case_id: str
    status: Optional[str] = None
    assignee: Optional[str] = None
    resolution: Optional[str] = None


class SimulateFaultRequest(BaseModel):
    fault_type: str  # 'event_lag', 'error_rate'
    value: float


# =============================================================================
# CREATE APP
# =============================================================================

app = FastAPI(
    title="DonCoin DAO Security API",
    description="Security Monitoring, Authentication, and SIEM API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post("/auth/login", response_model=Token)
async def auth_login(request: Request, login_data: LoginRequest):
    """
    Authenticate and get access token.
    Rate limited to 5 attempts per minute.
    """
    ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    
    token = login(
        login_data.username,
        login_data.password,
        ip,
        user_agent
    )
    
    if not token:
        # Record failed attempt for brute force detection
        is_blocked = await brute_force_detector.record_failure(ip, login_data.username)
        
        if is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Too many failed attempts. IP blocked for 15 minutes."
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Reset brute force counter on success
    brute_force_detector.reset(ip, login_data.username)
    
    return token


@app.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


# =============================================================================
# MONITORING ENDPOINTS
# =============================================================================

@app.get("/metrics")
async def get_prometheus_metrics():
    """Export metrics in Prometheus format"""
    return metrics_collector.export_prometheus()


@app.get("/api/v1/kpis")
async def get_all_kpis(current_user: User = Depends(get_current_user)):
    """Get all KPI values and status"""
    return metrics_collector.get_all_kpis()


@app.get("/api/v1/kpis/{kpi_name}/history")
async def get_kpi_history(
    kpi_name: str,
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """Get historical KPI data"""
    since = datetime.utcnow() - timedelta(hours=hours)
    return {
        "kpi": kpi_name,
        "history": metrics_collector.get_metric_history(kpi_name, since=since)
    }


@app.post("/api/v1/baseline/create")
async def create_kpi_baseline(current_user: User = Depends(get_current_admin)):
    """Create a baseline snapshot of current KPI values"""
    log_admin_access(
        current_user.username,
        "create_baseline",
        "/api/v1/baseline/create",
        "system",
        True
    )
    return create_baseline_snapshot()


@app.get("/api/v1/baseline/compare")
async def compare_kpi_baseline(current_user: User = Depends(get_current_user)):
    """Compare current KPIs to baseline"""
    return compare_to_baseline()


# =============================================================================
# ALERTING ENDPOINTS
# =============================================================================

@app.get("/api/v1/alerts")
async def get_active_alerts(current_user: User = Depends(get_current_user)):
    """Get all active alerts"""
    return {
        "active": alert_manager.get_active_alerts(),
        "summary": alert_manager.get_alert_summary()
    }


@app.get("/api/v1/alerts/history")
async def get_alert_history(
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get alert history"""
    return alert_manager.get_alert_history(limit)


@app.post("/api/v1/alerts/acknowledge")
async def acknowledge_alert(
    request: Request,
    data: AlertAcknowledge,
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an active alert"""
    success = alert_manager.acknowledge_alert(data.alert_id, current_user.username)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    log_admin_access(
        current_user.username,
        "acknowledge_alert",
        f"/api/v1/alerts/{data.alert_id}",
        get_client_ip(request),
        True,
        {"alert_id": data.alert_id}
    )
    
    return {"status": "acknowledged", "alert_id": data.alert_id}


@app.post("/api/v1/alerts/test")
async def trigger_test_alert(
    data: SimulateFaultRequest,
    current_user: User = Depends(get_current_admin)
):
    """
    Simulate a fault to test alerting.
    Admin only - for testing alert pipelines.
    """
    if data.fault_type == 'event_lag':
        record_event_lag(data.value)
    elif data.fault_type == 'error_rate':
        metrics_collector.record_gauge("error_rate", data.value)
    else:
        raise HTTPException(status_code=400, detail="Unknown fault type")
    
    # Trigger alert check
    await alert_manager.check_rules()
    
    return {
        "status": "fault_simulated",
        "type": data.fault_type,
        "value": data.value,
        "alerts": alert_manager.get_active_alerts()
    }


# =============================================================================
# SIEM ENDPOINTS
# =============================================================================

@app.get("/api/v1/siem/events")
async def search_events(
    category: Optional[str] = None,
    source_ip: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Search security events"""
    cat = EventCategory(category) if category else None
    return siem_engine.search_events(
        category=cat,
        source_ip=source_ip,
        outcome=outcome,
        limit=limit
    )


@app.get("/api/v1/siem/cases")
async def get_security_cases(current_user: User = Depends(get_current_user)):
    """Get open security cases"""
    return {
        "cases": siem_engine.get_open_cases(),
        "summary": siem_engine.get_case_summary()
    }


@app.put("/api/v1/siem/cases/{case_id}")
async def update_security_case(
    case_id: str,
    update: CaseUpdate,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Update a security case"""
    from siem.engine import CaseStatus
    
    status_val = CaseStatus(update.status) if update.status else None
    
    case = siem_engine.update_case(
        case_id,
        status=status_val,
        assignee=update.assignee,
        resolution=update.resolution
    )
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    log_admin_access(
        current_user.username,
        "update_case",
        f"/api/v1/siem/cases/{case_id}",
        get_client_ip(request),
        True,
        {"case_id": case_id, "updates": update.dict(exclude_none=True)}
    )
    
    return case.to_dict()


# =============================================================================
# RATE LIMIT ENDPOINTS
# =============================================================================

@app.get("/api/v1/rate-limits/stats")
async def get_rate_limit_stats(current_user: User = Depends(get_current_admin)):
    """Get rate limiting statistics"""
    return rate_limit_stats.get_stats()


# =============================================================================
# RETENTION ENDPOINTS
# =============================================================================

@app.get("/api/v1/retention/summary")
async def get_retention_summary(current_user: User = Depends(get_current_admin)):
    """Get data retention summary"""
    return retention_manager.get_retention_summary()


@app.post("/api/v1/retention/run")
async def run_retention_policies(
    request: Request,
    current_user: User = Depends(get_current_admin)
):
    """Run data retention policies"""
    log_admin_access(
        current_user.username,
        "run_retention",
        "/api/v1/retention/run",
        get_client_ip(request),
        True
    )
    
    results = retention_manager.run_all_policies()
    return {"status": "completed", "results": results}


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "auth": "ok",
            "monitoring": "ok",
            "siem": "ok",
            "rate_limiter": "ok"
        }
    }


# =============================================================================
# REQUIRED IMPORTS
# =============================================================================

from datetime import timedelta


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    print("Starting DonCoin DAO Security API...")
    print("Open http://localhost:8070/docs for Swagger UI")
    uvicorn.run(app, host="0.0.0.0", port=8070)
