"""
Sprint 3: Monitoring & Metrics Module
Tracks KPIs, alerts, and operational health
"""

import json
from datetime import datetime, timezone
from collections import deque
from threading import Lock
from enum import Enum

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CollectorRegistry


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = 1
    WARNING = 2
    INFO = 3


class KPITracker:
    """Track key performance indicators"""
    
    def __init__(self, max_history=1440):  # 1 day at 1-min resolution
        self.max_history = max_history
        self.lock = Lock()
        
        # Event processing KPIs
        self.event_processing_lag = deque(maxlen=max_history)  # Seconds
        self.error_rate = deque(maxlen=max_history)  # Percentage
        self.api_response_latency = deque(maxlen=max_history)  # Milliseconds
        self.suspicious_transactions_flagged = deque(maxlen=max_history)  # Count
        
        # Conversion metrics
        self.conversion_rate = deque(maxlen=max_history)  # Percentage
        self.transaction_success_rate = deque(maxlen=max_history)  # Percentage
        
        # Timestamp
        self.last_update = datetime.now()
        
    def update_event_lag(self, lag_seconds):
        """Update event processing lag KPI"""
        with self.lock:
            try:
                self.event_processing_lag.append(float(lag_seconds))
            except Exception:
                self.event_processing_lag.append(0.0)
            self.last_update = datetime.now()
    
    def update_error_rate(self, error_count, total_count):
        """Update error rate KPI"""
        with self.lock:
            try:
                total = max(int(total_count), 1)
                rate = (int(error_count) / total) * 100.0
                self.error_rate.append(float(rate))
            except Exception:
                self.error_rate.append(0.0)
            self.last_update = datetime.now()
            # note: previous accidental duplicate append removed
    
    def update_latency(self, latency_ms):
        """Update API response latency"""
        with self.lock:
            try:
                self.api_response_latency.append(float(latency_ms))
            except Exception:
                self.api_response_latency.append(0.0)
            self.last_update = datetime.now()
    
    def update_suspicious_count(self, count):
        """Update count of flagged suspicious transactions"""
        with self.lock:
            try:
                self.suspicious_transactions_flagged.append(int(count))
            except Exception:
                self.suspicious_transactions_flagged.append(0)
            self.last_update = datetime.now()
    
    def update_conversion_rate(self, converted, total):
        """Update conversion rate KPI"""
        with self.lock:
            try:
                total = max(int(total), 1)
                rate = (int(converted) / total) * 100.0
                self.conversion_rate.append(float(rate))
            except Exception:
                self.conversion_rate.append(0.0)
            self.last_update = datetime.now()
            # note: previous accidental duplicate append removed
    
    def get_summary(self):
        """Get KPI summary statistics"""
        with self.lock:
            def _stats(dq):
                if not dq:
                    return {'current': None, 'min': None, 'max': None, 'avg': None}
                vals = list(dq)
                return {
                    'current': vals[-1],
                    'min': min(vals),
                    'max': max(vals),
                    'avg': sum(vals) / len(vals)
                }

            return {
                'event_processing_lag': _stats(self.event_processing_lag),
                'error_rate': _stats(self.error_rate),
                'api_response_latency': _stats(self.api_response_latency),
                'suspicious_transactions_flagged': _stats(self.suspicious_transactions_flagged),
                'conversion_rate': _stats(self.conversion_rate),
                'transaction_success_rate': _stats(self.transaction_success_rate),
                'last_update': self.last_update.isoformat()
            }


class AlertManager:
    """Manage alerts and thresholds"""
    
    def __init__(self):
        self.lock = Lock()
        self.alerts = deque(maxlen=10000)  # Keep recent alerts
        
        # Alert thresholds (configurable)
        self.thresholds = {
            'event_processing_lag_critical': 60,  # seconds
            'error_rate_critical': 2.0,  # percentage
            'api_latency_warning': 1000,  # milliseconds
            'suspicious_transactions_critical': 50,  # count in period
        }
    
    def check_and_alert(self, kpi_name, value, threshold):
        """Check if value exceeds threshold and create alert"""
        try:
            if value is None:
                return None
            if float(value) > float(threshold):
                alert = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'kpi': kpi_name,
                    'value': float(value),
                    'threshold': float(threshold),
                    'severity': AlertSeverity.CRITICAL.name,
                }
                with self.lock:
                    self.alerts.append(alert)
                return alert
        except Exception:
            return None
        return None
    
    def get_recent_alerts(self, limit=100):
        """Get recent alerts"""
        with self.lock:
            return list(self.alerts)[-limit:]


# Global instances
kpi_tracker = KPITracker()
alert_manager = AlertManager()


class MetricsCollector:
    """Collect metrics for Prometheus export"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Prometheus metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration_ms = Histogram(
            'http_request_duration_ms',
            'HTTP request duration in milliseconds',
            ['endpoint'],
            registry=self.registry
        )
        
        self.event_processing_lag_seconds = Gauge(
            'event_processing_lag_seconds',
            'Event processing lag in seconds',
            registry=self.registry
        )
        
        self.error_rate_percent = Gauge(
            'error_rate_percent',
            'Error rate percentage',
            registry=self.registry
        )
        
        self.suspicious_transactions_total = Counter(
            'suspicious_transactions_total',
            'Total suspicious transactions flagged',
            registry=self.registry
        )
        
        self.model_inference_duration_ms = Histogram(
            'model_inference_duration_ms',
            'Model inference duration in milliseconds',
            ['model_name'],
            registry=self.registry
        )
    
    def export_metrics(self):
        # Return Prometheus exposition format bytes
        return generate_latest(self.registry)


metrics_collector = MetricsCollector()


# Logging for model inputs/outputs (for model tracing)
class ModelInferenceLogger:
    """Log all model inferences for tracing and audit"""
    
    def __init__(self, max_entries=10000):
        self.max_entries = max_entries
        self.lock = Lock()
        self.logs = deque(maxlen=max_entries)
    
    def log_inference(self, model_name, features_dict, prediction, score, latency_ms):
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'model_name': model_name,
            'features': features_dict,
            'prediction': prediction,
            'score': float(score),
            'latency_ms': float(latency_ms)
        }
        with self.lock:
            self.logs.append(entry)
    
    def get_recent_inferences(self, model_name=None, limit=100):
        """Get recent inferences"""
        with self.lock:
            items = list(self.logs)
        if model_name:
            items = [i for i in items if i.get('model_name') == model_name]
        return items[-limit:]


inference_logger = ModelInferenceLogger()


if __name__ == '__main__':
    # Demo: Simulate KPI updates
    print("=== Monitoring Module Demo ===\n")
    
    # Simulate event processing lag
    kpi_tracker.update_event_lag(45)  # Normal
    kpi_tracker.update_event_lag(65)  # Exceeds threshold
    
    # Check thresholds
    alert = alert_manager.check_and_alert(
        'event_processing_lag',
        65,
        alert_manager.thresholds['event_processing_lag_critical']
    )
    if alert:
        print(f"🚨 ALERT: {alert}")
    
    # Get KPI summary
    print("\nKPI Summary:")
    summary = kpi_tracker.get_summary()
    print(json.dumps(summary, indent=2))
    
    # Log model inference
    inference_logger.log_inference(
        model_name='XGBoost_HighValueUserClassifier',
        features_dict={'total_amount': 100.5, 'tx_count': 15, 'confirmation_rate': 0.95},
        prediction=1,
        score=0.87,
        latency_ms=5.2
    )
    print("\n✅ Model inference logged")
