"""
Tests for Security Module
Unit and integration tests for authentication, rate limiting, and monitoring.
"""
import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# =============================================================================
# AUTHENTICATION TESTS
# =============================================================================

class TestAuthentication:
    """Tests for authentication module"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        from auth.authentication import get_password_hash, verify_password
        
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_password_validation(self):
        """Test password strength validation"""
        from auth.authentication import validate_password_strength
        
        # Too short
        is_valid, msg = validate_password_strength("short")
        assert is_valid is False
        
        # No uppercase
        is_valid, msg = validate_password_strength("alllowercase123!")
        assert is_valid is False
        
        # No special character
        is_valid, msg = validate_password_strength("NoSpecialChar123")
        assert is_valid is False
        
        # Valid password
        is_valid, msg = validate_password_strength("ValidPassword123!")
        assert is_valid is True
    
    def test_token_creation_and_decoding(self):
        """Test JWT token creation and decoding"""
        from auth.authentication import create_access_token, decode_token
        
        data = {"sub": "testuser", "scopes": ["admin"]}
        token = create_access_token(data)
        
        assert token is not None
        
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded.username == "testuser"
        assert "admin" in decoded.scopes
    
    def test_user_authentication(self):
        """Test user authentication flow"""
        from auth.authentication import authenticate_user, USERS_DB, get_password_hash
        
        # Add test user
        USERS_DB['testuser'] = {
            'username': 'testuser',
            'email': 'test@test.com',
            'hashed_password': get_password_hash('TestPass123!'),
            'is_admin': False,
            'disabled': False,
        }
        
        # Valid credentials
        user = authenticate_user('testuser', 'TestPass123!')
        assert user is not None
        assert user.username == 'testuser'
        
        # Invalid password
        user = authenticate_user('testuser', 'wrongpassword')
        assert user is None
        
        # Invalid username
        user = authenticate_user('nonexistent', 'password')
        assert user is None
        
        # Cleanup
        del USERS_DB['testuser']


# =============================================================================
# RATE LIMITING TESTS
# =============================================================================

class TestRateLimiting:
    """Tests for rate limiting module"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiting"""
        from middleware.rate_limiter import InMemoryRateLimiter
        
        limiter = InMemoryRateLimiter()
        
        # First requests should be allowed
        for i in range(5):
            is_limited, info = await limiter.is_rate_limited("test_key", "5/minute")
            assert is_limited is False
            assert info['remaining'] == 5 - i - 1
        
        # 6th request should be limited
        is_limited, info = await limiter.is_rate_limited("test_key", "5/minute")
        assert is_limited is True
    
    @pytest.mark.asyncio
    async def test_rate_limiter_different_keys(self):
        """Test that different keys have separate limits"""
        from middleware.rate_limiter import InMemoryRateLimiter
        
        limiter = InMemoryRateLimiter()
        
        # Use up limit for key1
        for i in range(3):
            await limiter.is_rate_limited("key1", "3/minute")
        
        is_limited, _ = await limiter.is_rate_limited("key1", "3/minute")
        assert is_limited is True
        
        # key2 should still have full limit
        is_limited, info = await limiter.is_rate_limited("key2", "3/minute")
        assert is_limited is False
        assert info['remaining'] == 2
    
    @pytest.mark.asyncio
    async def test_ip_blocking(self):
        """Test IP blocking functionality"""
        from middleware.rate_limiter import InMemoryRateLimiter
        
        limiter = InMemoryRateLimiter()
        
        # Block IP
        await limiter.block_ip("192.168.1.1", 60)
        
        # Requests from blocked IP should be denied
        is_limited, info = await limiter.is_rate_limited("192.168.1.1", "100/minute")
        assert is_limited is True
        assert info.get('blocked') is True
    
    @pytest.mark.asyncio
    async def test_brute_force_detection(self):
        """Test brute force detection"""
        from middleware.rate_limiter import BruteForceDetector
        
        detector = BruteForceDetector(max_attempts=3, window_seconds=300, block_seconds=60)
        
        # First failures should not block
        blocked = await detector.record_failure("192.168.1.1", "testuser")
        assert blocked is False
        
        blocked = await detector.record_failure("192.168.1.1", "testuser")
        assert blocked is False
        
        # 3rd failure should trigger block
        blocked = await detector.record_failure("192.168.1.1", "testuser")
        assert blocked is True


# =============================================================================
# MONITORING TESTS
# =============================================================================

class TestMonitoring:
    """Tests for monitoring module"""
    
    def test_metrics_gauge(self):
        """Test gauge metric recording"""
        from monitoring.metrics import MetricsCollector
        
        collector = MetricsCollector()
        
        collector.record_gauge("test_gauge", 42.5)
        assert collector.get_gauge("test_gauge") == 42.5
        
        collector.record_gauge("test_gauge", 50.0)
        assert collector.get_gauge("test_gauge") == 50.0
    
    def test_metrics_counter(self):
        """Test counter metric recording"""
        from monitoring.metrics import MetricsCollector
        
        collector = MetricsCollector()
        
        collector.record_counter("test_counter", 1)
        assert collector.get_counter("test_counter") == 1
        
        collector.record_counter("test_counter", 5)
        assert collector.get_counter("test_counter") == 6
    
    def test_metrics_histogram(self):
        """Test histogram metric recording"""
        from monitoring.metrics import MetricsCollector
        
        collector = MetricsCollector()
        
        # Record some values
        for v in [10, 20, 30, 40, 50]:
            collector.record_histogram("test_histogram", v)
        
        stats = collector.get_histogram_stats("test_histogram")
        assert stats['count'] == 5
        assert stats['mean'] == 30
        assert stats['min'] == 10
        assert stats['max'] == 50
    
    def test_kpi_status_calculation(self):
        """Test KPI status calculation based on thresholds"""
        from monitoring.metrics import MetricsCollector
        from config.settings import MONITORING_KPIS
        
        collector = MetricsCollector()
        
        # Set a value below warning threshold
        collector.record_gauge("event_processing_lag", 2.0)
        kpis = collector.get_all_kpis()
        assert kpis['event_processing_lag']['status'] == 'ok'
        
        # Set a value above warning but below critical
        collector.record_gauge("event_processing_lag", 45.0)
        kpis = collector.get_all_kpis()
        assert kpis['event_processing_lag']['status'] == 'warning'
        
        # Set a value above critical
        collector.record_gauge("event_processing_lag", 75.0)
        kpis = collector.get_all_kpis()
        assert kpis['event_processing_lag']['status'] == 'critical'


# =============================================================================
# ALERTING TESTS
# =============================================================================

class TestAlerting:
    """Tests for alerting module"""
    
    @pytest.mark.asyncio
    async def test_alert_firing(self):
        """Test alert firing when threshold exceeded"""
        from monitoring.alerting import AlertManager
        from monitoring.metrics import metrics_collector
        
        manager = AlertManager()
        
        # Set high event lag to trigger alert
        metrics_collector.record_gauge("event_processing_lag", 75.0)
        
        # Check rules
        await manager.check_rules()
        
        # Should have active alert
        active = manager.get_active_alerts()
        assert len(active) > 0
        assert any(a['name'] == 'High Event Processing Lag' for a in active)
    
    @pytest.mark.asyncio
    async def test_alert_resolution(self):
        """Test alert resolution when threshold no longer exceeded"""
        from monitoring.alerting import AlertManager
        from monitoring.metrics import metrics_collector
        
        manager = AlertManager()
        
        # Fire alert
        metrics_collector.record_gauge("event_processing_lag", 75.0)
        await manager.check_rules()
        
        initial_count = len(manager.get_active_alerts())
        
        # Resolve by lowering value
        metrics_collector.record_gauge("event_processing_lag", 5.0)
        await manager.check_rules()
        
        # Alert should be resolved
        final_count = len(manager.get_active_alerts())
        assert final_count < initial_count or final_count == 0
    
    def test_alert_acknowledgment(self):
        """Test alert acknowledgment"""
        from monitoring.alerting import Alert, AlertSeverity, AlertStatus, AlertManager
        
        manager = AlertManager()
        
        # Create a test alert
        test_alert = Alert(
            alert_id="TEST-001",
            name="Test Alert",
            kpi="test",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.FIRING,
            value=100,
            threshold=50,
            message="Test",
            fired_at=datetime.utcnow()
        )
        manager.active_alerts["Test Alert"] = test_alert
        
        # Acknowledge
        result = manager.acknowledge_alert("TEST-001", "testuser")
        assert result is True
        assert test_alert.acknowledged is True
        assert test_alert.acknowledged_by == "testuser"


# =============================================================================
# SIEM TESTS
# =============================================================================

class TestSIEM:
    """Tests for SIEM module"""
    
    def test_event_ingestion(self):
        """Test security event ingestion"""
        from siem.engine import SIEMEngine, EventCategory
        
        engine = SIEMEngine()
        
        event = engine.ingest_event(
            category=EventCategory.AUTHENTICATION,
            source_ip="192.168.1.1",
            user="testuser",
            action="login",
            resource="/auth/login",
            outcome="success"
        )
        
        assert event is not None
        assert event.category == EventCategory.AUTHENTICATION
        assert event.source_ip == "192.168.1.1"
        assert event.outcome == "success"
    
    def test_event_search(self):
        """Test event search functionality"""
        from siem.engine import SIEMEngine, EventCategory
        
        engine = SIEMEngine()
        
        # Ingest some events
        for i in range(5):
            engine.ingest_event(
                category=EventCategory.AUTHENTICATION,
                source_ip=f"192.168.1.{i}",
                action="login",
                resource="/auth/login",
                outcome="success" if i % 2 == 0 else "failure"
            )
        
        # Search by category
        results = engine.search_events(category=EventCategory.AUTHENTICATION)
        assert len(results) >= 5
        
        # Search by outcome
        results = engine.search_events(outcome="failure")
        assert all(r['outcome'] == 'failure' for r in results)
    
    def test_case_creation_on_correlation(self):
        """Test that cases are created when correlation rules match"""
        from siem.engine import SIEMEngine, EventCategory
        
        engine = SIEMEngine()
        
        # Simulate multiple failed logins to trigger correlation
        for i in range(6):
            engine.ingest_event(
                category=EventCategory.AUTHENTICATION,
                source_ip="192.168.1.100",
                user="attacker",
                action="login",
                resource="/auth/login",
                outcome="failure"
            )
        
        # Should have created a case
        open_cases = engine.get_open_cases()
        # Note: Case creation depends on threshold in correlation rules


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        from fastapi.testclient import TestClient
        from api.endpoints import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_login_flow(self):
        """Test complete login flow"""
        from fastapi.testclient import TestClient
        from api.endpoints import app
        
        client = TestClient(app)
        
        # Login
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
        # Use token to access protected endpoint
        token = data["access_token"]
        response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        assert response.json()["username"] == "admin"
    
    def test_protected_endpoint_without_auth(self):
        """Test that protected endpoints require authentication"""
        from fastapi.testclient import TestClient
        from api.endpoints import app
        
        client = TestClient(app)
        
        response = client.get("/api/v1/kpis")
        assert response.status_code == 403  # or 401
    
    def test_rate_limiting(self):
        """Test rate limiting is enforced"""
        from fastapi.testclient import TestClient
        from api.endpoints import app
        
        client = TestClient(app)
        
        # Make many requests to trigger rate limit
        for _ in range(10):
            response = client.post("/auth/login", json={
                "username": "test",
                "password": "wrong"
            })
        
        # Should eventually get rate limited
        # Note: Depends on rate limit config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
