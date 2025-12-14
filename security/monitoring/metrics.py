"""
Monitoring System for DonCoin DAO
Tracks system KPIs, stores metrics, and provides data for dashboard.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, asdict
import json
import time
import statistics
import threading
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import MONITORING_KPIS, LOGS_DIR


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = None
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "labels": self.labels or {}
        }


class MetricsCollector:
    """
    Collects and stores metrics for monitoring.
    Provides Prometheus-style metrics exposition.
    """
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
        
        # Initialize KPI metrics
        for kpi_id in MONITORING_KPIS:
            self.gauges[kpi_id] = 0.0
    
    def _cleanup_old_metrics(self, metric_name: str):
        """Remove metrics older than retention period"""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
        self.metrics[metric_name] = [
            m for m in self.metrics[metric_name]
            if m.timestamp > cutoff
        ]
    
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a gauge metric (current value)"""
        with self.lock:
            self.gauges[name] = value
            self.metrics[name].append(MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                labels=labels
            ))
            self._cleanup_old_metrics(name)
    
    def record_counter(self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None):
        """Record a counter metric (cumulative)"""
        with self.lock:
            self.counters[name] += value
            self.metrics[name].append(MetricPoint(
                timestamp=datetime.utcnow(),
                value=self.counters[name],
                labels=labels
            ))
            self._cleanup_old_metrics(name)
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram metric (distribution)"""
        with self.lock:
            self.histograms[name].append(value)
            # Keep only last 1000 values for histogram
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
            
            self.metrics[name].append(MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                labels=labels
            ))
            self._cleanup_old_metrics(name)
    
    def get_gauge(self, name: str) -> float:
        """Get current gauge value"""
        return self.gauges.get(name, 0.0)
    
    def get_counter(self, name: str) -> float:
        """Get current counter value"""
        return self.counters.get(name, 0.0)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics"""
        values = self.histograms.get(name, [])
        if not values:
            return {"count": 0, "mean": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_vals = sorted(values)
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "p50": sorted_vals[len(sorted_vals) // 2],
            "p95": sorted_vals[int(len(sorted_vals) * 0.95)],
            "p99": sorted_vals[int(len(sorted_vals) * 0.99)]
        }
    
    def get_metric_history(
        self,
        name: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical metric data"""
        with self.lock:
            metrics = self.metrics.get(name, [])
            
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
            if until:
                metrics = [m for m in metrics if m.timestamp <= until]
            
            # Return most recent
            metrics = sorted(metrics, key=lambda x: x.timestamp, reverse=True)[:limit]
            return [m.to_dict() for m in reversed(metrics)]
    
    def get_all_kpis(self) -> Dict[str, Dict[str, Any]]:
        """Get all KPI values with their configuration"""
        result = {}
        for kpi_id, config in MONITORING_KPIS.items():
            current_value = self.get_gauge(kpi_id)
            
            # Determine status
            if current_value >= config['critical_threshold']:
                status = 'critical'
            elif current_value >= config['warning_threshold']:
                status = 'warning'
            else:
                status = 'ok'
            
            result[kpi_id] = {
                **config,
                'current_value': current_value,
                'status': status,
            }
        
        return result
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Gauges
        for name, value in self.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        # Counters
        for name, value in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        # Histograms
        for name, values in self.histograms.items():
            if values:
                stats = self.get_histogram_stats(name)
                lines.append(f"# TYPE {name} histogram")
                lines.append(f'{name}_count {stats["count"]}')
                lines.append(f'{name}_sum {sum(values)}')
        
        return "\n".join(lines)


# Global metrics collector
metrics_collector = MetricsCollector()


# =============================================================================
# KPI TRACKING FUNCTIONS
# =============================================================================

def record_event_lag(lag_seconds: float):
    """Record blockchain event processing lag"""
    metrics_collector.record_gauge("event_processing_lag", lag_seconds)
    metrics_collector.record_histogram("event_lag_distribution", lag_seconds)


def record_api_latency(latency_ms: float, endpoint: str = ""):
    """Record API response latency"""
    metrics_collector.record_histogram("api_response_latency", latency_ms, {"endpoint": endpoint})
    
    # Update P95 gauge
    stats = metrics_collector.get_histogram_stats("api_response_latency")
    metrics_collector.record_gauge("api_response_latency", stats['p95'])


def record_error(endpoint: str = "", error_type: str = ""):
    """Record an API error"""
    metrics_collector.record_counter("error_count", 1, {"endpoint": endpoint, "type": error_type})
    metrics_collector.record_counter("request_count", 1)
    
    # Calculate error rate (simple moving window)
    error_count = metrics_collector.get_counter("error_count")
    request_count = metrics_collector.get_counter("request_count")
    if request_count > 0:
        error_rate = (error_count / request_count) * 100
        metrics_collector.record_gauge("error_rate", error_rate)


def record_request():
    """Record a successful API request"""
    metrics_collector.record_counter("request_count", 1)


def record_suspicious_transaction(tx_hash: str = "", reason: str = ""):
    """Record a suspicious transaction flag"""
    metrics_collector.record_counter("suspicious_tx_total", 1)
    
    # Track hourly count
    hour_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
    metrics_collector.record_counter(f"suspicious_tx_{hour_key}", 1)
    
    # Update gauge with hourly count
    hourly_count = metrics_collector.get_counter(f"suspicious_tx_{hour_key}")
    metrics_collector.record_gauge("suspicious_tx_count", hourly_count)


# =============================================================================
# BASELINE SNAPSHOT
# =============================================================================

def create_baseline_snapshot() -> Dict[str, Any]:
    """Create a baseline snapshot of current KPI values"""
    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "kpis": {}
    }
    
    for kpi_id, config in MONITORING_KPIS.items():
        snapshot["kpis"][kpi_id] = {
            "value": metrics_collector.get_gauge(kpi_id),
            "target": config['target'],
            "unit": config['unit'],
        }
    
    # Save to file
    snapshot_file = LOGS_DIR / "kpi_baseline.json"
    with open(snapshot_file, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    return snapshot


def load_baseline_snapshot() -> Optional[Dict[str, Any]]:
    """Load the baseline snapshot"""
    snapshot_file = LOGS_DIR / "kpi_baseline.json"
    if snapshot_file.exists():
        with open(snapshot_file, 'r') as f:
            return json.load(f)
    return None


def compare_to_baseline() -> Dict[str, Any]:
    """Compare current KPIs to baseline"""
    baseline = load_baseline_snapshot()
    if not baseline:
        return {"error": "No baseline snapshot found"}
    
    comparison = {
        "baseline_timestamp": baseline["timestamp"],
        "current_timestamp": datetime.utcnow().isoformat(),
        "kpis": {}
    }
    
    for kpi_id, baseline_data in baseline["kpis"].items():
        current_value = metrics_collector.get_gauge(kpi_id)
        baseline_value = baseline_data["value"]
        
        if baseline_value != 0:
            change_pct = ((current_value - baseline_value) / baseline_value) * 100
        else:
            change_pct = 0 if current_value == 0 else 100
        
        comparison["kpis"][kpi_id] = {
            "baseline_value": baseline_value,
            "current_value": current_value,
            "change_percent": round(change_pct, 2),
            "improved": change_pct < 0 if kpi_id in ['error_rate', 'event_processing_lag', 
                                                       'api_response_latency', 'suspicious_tx_count'] else change_pct > 0
        }
    
    return comparison
