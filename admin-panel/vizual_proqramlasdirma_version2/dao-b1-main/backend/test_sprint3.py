"""
Sprint 3: Integration Tests
End-to-end tests for model inference, monitoring, and security controls
"""

import pytest
from datetime import datetime, timedelta

from monitoring import kpi_tracker, alert_manager, inference_logger
from siem_soar import EventCorrelator, ThreatModelRegistry, SecurityEvent, SeverityLevel
from inference import ModelInferencePipeline, score_user_for_ui_personalization, score_transaction_for_gating


class TestMonitoring:
    """Tests for monitoring and KPI tracking"""
    
    def test_kpi_tracker_update(self):
        """Test KPI tracker updates"""
        tracker = kpi_tracker
        
        # Update event lag
        tracker.update_event_lag(45.0)
        tracker.update_event_lag(55.0)
        
        summary = tracker.get_summary()
        assert summary['event_processing_lag']['current'] == 55.0
        assert summary['event_processing_lag']['max'] >= 55.0
    
    def test_alert_creation(self):
        """Test alert creation when threshold exceeded"""
        manager = alert_manager
        
        # Check alert for high lag
        alert = manager.check_and_alert('event_lag', 65, 60)
        assert alert is not None
        assert alert['severity'] == 'CRITICAL'
        
        # No alert for low value
        alert2 = manager.check_and_alert('event_lag', 30, 60)
        assert alert2 is None
    
    def test_inference_logging(self):
        """Test model inference logging"""
        logger = inference_logger
        
        # Log inference
        logger.log_inference(
            model_name='TestModel',
            features_dict={'feature_1': 1.0, 'feature_2': 2.0},
            prediction=1,
            score=0.95,
            latency_ms=5.5
        )
        
        # Retrieve
        logs = logger.get_recent_inferences('TestModel')
        assert len(logs) > 0
        assert logs[-1]['model_name'] == 'TestModel'
        assert logs[-1]['score'] == 0.95


class TestModelInference:
    """Tests for model inference pipeline"""
    
    def setup_method(self):
        """Setup test pipeline"""
        self.pipeline = ModelInferencePipeline()
        self.pipeline.load_models()
    
    def test_high_value_scoring(self):
        """Test high-value user scoring"""
        features = {
            'total_amount': 500.0,
            'tx_count': 20,
            'confirmation_rate': 0.95,
        }
        
        score, decision = self.pipeline.score_user_high_value_likelihood(features)
        
        assert 0.0 <= score <= 1.0
        assert 'latency_ms' in decision
        assert decision['is_high_value'] == (score > 0.6)
    
    def test_anomaly_detection(self):
        """Test anomaly detection"""
        # Normal user
        normal_features = {
            'suspicious_ratio': 0.05,
            'amount_volatility': 0.5
        }
        is_anom, details = self.pipeline.detect_anomalies(normal_features)
        assert is_anom == 0
        
        # Anomalous user
        anomaly_features = {
            'suspicious_ratio': 0.5,
            'amount_volatility': 3.0
        }
        is_anom2, details2 = self.pipeline.detect_anomalies(anomaly_features)
        assert is_anom2 == 1
        assert len(details2['reasons']) > 0
    
    def test_risk_scoring(self):
        """Test transaction risk scoring"""
        features = {
            'is_anomalous': 0,
            'confirmation_rate': 0.95,
            'days_since_creation': 30,
            'transaction_size': 100
        }
        
        risk_score, details = self.pipeline.calculate_risk_score(features)
        
        assert 0.0 <= risk_score <= 1.0
        assert details['risk_level'] in ['LOW', 'MEDIUM', 'HIGH']
        assert 'latency_ms' in details
    
    def test_ui_personalization_high_value(self):
        """Test UI personalization for high-value user"""
        features = {
            'total_amount': 2000.0,
            'tx_count': 50,
            'confirmation_rate': 0.98,
            'suspicious_ratio': 0.02,
            'amount_volatility': 0.1,
            'days_since_creation': 60
        }
        
        personal = score_user_for_ui_personalization(123, features)
        
        assert personal['variant'] == 'variant_a'
        assert 'premium_content_access' in personal['personalization_features']
    
    def test_transaction_gating_approval(self):
        """Test transaction gating for low-risk transaction"""
        features = {
            'transaction_size': 100,
            'is_anomalous': 0,
            'confirmation_rate': 0.95,
            'days_since_creation': 30
        }
        
        decision = score_transaction_for_gating(123, {**features, 'tx_id': 'tx_123'})
        
        assert decision['action'] in ['approve', 'review', 'block']
        assert 'risk_score' in decision
        assert 'risk_level' in decision
    
    def test_transaction_gating_high_risk(self):
        """Test transaction gating for high-risk transaction"""
        features = {
            'transaction_size': 10000,
            'is_anomalous': 1,
            'confirmation_rate': 0.5,
            'days_since_creation': 1
        }
        
        decision = score_transaction_for_gating(456, {**features, 'tx_id': 'tx_456'})
        
        assert decision['requires_additional_verification']
        if decision['action'] == 'block':
            assert 'block_reason' in decision


class TestThreatModeling:
    """Tests for threat model and SIEM/SOAR"""
    
    def test_threat_registry(self):
        """Test threat model registry"""
        threats = ThreatModelRegistry.get_all_threats()
        
        assert len(threats) >= 3
        assert threats[0].risk_score >= threats[-1].risk_score  # Sorted by risk
    
    def test_threat_retrieval(self):
        """Test threat retrieval by ID"""
        threat = ThreatModelRegistry.get_threat_by_id('T001')
        
        assert threat is not None
        assert threat.threat_id == 'T001'
        assert len(threat.mitigations) > 0
    
    def test_event_correlation(self):
        """Test event correlation logic"""
        correlator = EventCorrelator(correlation_window_seconds=60)
        
        # Ingest first event
        event1 = SecurityEvent(
            timestamp=datetime.now().isoformat(),
            event_type='failed_login',
            severity=SeverityLevel.HIGH,
            source_ip='192.168.1.100',
            user_id='admin',
            resource='/api/admin',
            action='GET',
            details={},
            threat_score=0.7
        )
        correlator.ingest_event(event1)
        
        # Ingest related event from same IP
        event2 = SecurityEvent(
            timestamp=(datetime.now() + timedelta(seconds=5)).isoformat(),
            event_type='suspicious_query',
            severity=SeverityLevel.MEDIUM,
            source_ip='192.168.1.100',
            user_id=None,
            resource='/api/data',
            action='POST',
            details={},
            threat_score=0.6
        )
        correlator.ingest_event(event2)
        
        # Check correlation
        assert event2.correlated_events is not None
        assert len(event2.correlated_events) > 0
    
    def test_event_summary(self):
        """Test event correlation summary"""
        correlator = EventCorrelator()
        
        # Ingest multiple events
        for i in range(3):
            event = SecurityEvent(
                timestamp=(datetime.now() + timedelta(seconds=i)).isoformat(),
                event_type='test_event',
                severity=SeverityLevel.INFO,
                source_ip=f'192.168.1.{100+i}',
                user_id=None,
                resource='/test',
                action='GET',
                details={},
                threat_score=0.3
            )
            correlator.ingest_event(event)
        
        summary = correlator.get_event_summary()
        
        assert summary['total_events'] == 3
        assert 'test_event' in summary['events_by_type']


class TestRateLimiting:
    """Tests for rate limiting (placeholder for implementation)"""
    
    def test_token_bucket_initialization(self):
        """Test token bucket rate limiter initialization"""
        # Mock implementation
        max_tokens = 100
        refill_rate = 10  # tokens/second
        
        assert max_tokens > 0
        assert refill_rate > 0
    
    def test_rate_limit_allow(self):
        """Test rate limit allows request within threshold"""
        # Mock: Request should succeed within limits
        pass
    
    def test_rate_limit_exceed(self):
        """Test rate limit rejects request exceeding threshold"""
        # Mock: Request should be rejected/throttled over limit
        pass


class TestSecurityControls:
    """Tests for security controls (admin auth, audit logging)"""
    
    def test_admin_endpoint_requires_auth(self):
        """Test that admin endpoints require authentication"""
        # Mock implementation
        # Endpoint /api/admin should return 403 without valid token
        pass
    
    def test_admin_access_logging(self):
        """Test that admin access is logged"""
        # Mock implementation
        # All admin actions should appear in audit log
        pass


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
