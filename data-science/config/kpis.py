"""
KPI Definitions for DonCoin DAO
Defines business-critical and system monitoring KPIs with baseline tracking.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import os


@dataclass
class KPIDefinition:
    """Definition of a single KPI"""
    name: str
    description: str
    category: str  # 'business' or 'system'
    formula: str
    unit: str
    target: Optional[float] = None
    alert_threshold: Optional[float] = None
    higher_is_better: bool = True


# Primary Business KPIs
BUSINESS_KPIS = [
    KPIDefinition(
        name="funding_success_rate",
        description="Percentage of proposals that reach their funding goal",
        category="business",
        formula="(funded_proposals / total_proposals) * 100",
        unit="%",
        target=60.0,
        alert_threshold=40.0,
        higher_is_better=True
    ),
    KPIDefinition(
        name="conversion_rate",
        description="Percentage of unique visitors who make a donation",
        category="business",
        formula="(unique_donors / unique_visitors) * 100",
        unit="%",
        target=15.0,
        alert_threshold=5.0,
        higher_is_better=True
    ),
    KPIDefinition(
        name="time_to_finality_days",
        description="Average time from proposal creation to full funding",
        category="business",
        formula="AVG(funded_at - created_at) in days",
        unit="days",
        target=14.0,
        alert_threshold=30.0,
        higher_is_better=False
    ),
    KPIDefinition(
        name="average_donation_size",
        description="Mean donation amount in tokens",
        category="business",
        formula="SUM(donation_amount) / COUNT(donations)",
        unit="tokens",
        target=100.0,
        alert_threshold=10.0,
        higher_is_better=True
    ),
]

# System Monitoring KPIs
SYSTEM_KPIS = [
    KPIDefinition(
        name="event_processing_lag",
        description="Time between blockchain event emission and database persistence",
        category="system",
        formula="AVG(db_timestamp - blockchain_timestamp) in seconds",
        unit="seconds",
        target=2.0,
        alert_threshold=5.0,
        higher_is_better=False
    ),
    KPIDefinition(
        name="api_response_latency_p95",
        description="95th percentile API response time",
        category="system",
        formula="PERCENTILE_95(api_response_time) in ms",
        unit="ms",
        target=100.0,
        alert_threshold=200.0,
        higher_is_better=False
    ),
    KPIDefinition(
        name="error_rate",
        description="Percentage of failed API and blockchain requests",
        category="system",
        formula="(failed_requests / total_requests) * 100",
        unit="%",
        target=0.05,
        alert_threshold=0.1,
        higher_is_better=False
    ),
    KPIDefinition(
        name="suspicious_transaction_count",
        description="Number of transactions flagged by outlier detection",
        category="system",
        formula="COUNT(flagged_transactions) per day",
        unit="count/day",
        target=0,
        alert_threshold=10,
        higher_is_better=False
    ),
]

ALL_KPIS = BUSINESS_KPIS + SYSTEM_KPIS


@dataclass
class KPIBaseline:
    """Stores baseline values for KPIs before model deployment"""
    kpi_name: str
    baseline_value: float
    recorded_at: datetime
    sample_size: int
    notes: str = ""


class KPITracker:
    """Track and store KPI baselines and current values"""
    
    def __init__(self, storage_path: str = "config/kpi_baselines.json"):
        self.storage_path = storage_path
        self.baselines: Dict[str, KPIBaseline] = {}
        self._load_baselines()
    
    def _load_baselines(self):
        """Load baselines from storage"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for name, info in data.items():
                    self.baselines[name] = KPIBaseline(
                        kpi_name=name,
                        baseline_value=info['value'],
                        recorded_at=datetime.fromisoformat(info['recorded_at']),
                        sample_size=info['sample_size'],
                        notes=info.get('notes', '')
                    )
    
    def _save_baselines(self):
        """Save baselines to storage"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = {}
        for name, baseline in self.baselines.items():
            data[name] = {
                'value': baseline.baseline_value,
                'recorded_at': baseline.recorded_at.isoformat(),
                'sample_size': baseline.sample_size,
                'notes': baseline.notes
            }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_baseline(self, kpi_name: str, value: float, sample_size: int, notes: str = ""):
        """Record a new baseline for a KPI"""
        self.baselines[kpi_name] = KPIBaseline(
            kpi_name=kpi_name,
            baseline_value=value,
            recorded_at=datetime.now(),
            sample_size=sample_size,
            notes=notes
        )
        self._save_baselines()
    
    def get_baseline(self, kpi_name: str) -> Optional[KPIBaseline]:
        """Get baseline for a KPI"""
        return self.baselines.get(kpi_name)
    
    def compare_to_baseline(self, kpi_name: str, current_value: float) -> Dict[str, Any]:
        """Compare current value to baseline"""
        baseline = self.get_baseline(kpi_name)
        if not baseline:
            return {'error': 'No baseline recorded'}
        
        kpi_def = next((k for k in ALL_KPIS if k.name == kpi_name), None)
        
        change = current_value - baseline.baseline_value
        change_pct = (change / baseline.baseline_value * 100) if baseline.baseline_value != 0 else 0
        
        # Determine if change is improvement
        is_improvement = (change > 0) == (kpi_def.higher_is_better if kpi_def else True)
        
        return {
            'kpi_name': kpi_name,
            'baseline_value': baseline.baseline_value,
            'current_value': current_value,
            'change': change,
            'change_percent': change_pct,
            'is_improvement': is_improvement,
            'baseline_date': baseline.recorded_at.isoformat(),
            'sample_size': baseline.sample_size
        }
    
    def get_all_baselines(self) -> List[Dict[str, Any]]:
        """Get all recorded baselines"""
        return [
            {
                'kpi_name': b.kpi_name,
                'value': b.baseline_value,
                'recorded_at': b.recorded_at.isoformat(),
                'sample_size': b.sample_size,
                'notes': b.notes
            }
            for b in self.baselines.values()
        ]


def get_kpi_by_name(name: str) -> Optional[KPIDefinition]:
    """Get KPI definition by name"""
    return next((k for k in ALL_KPIS if k.name == name), None)


def get_business_kpis() -> List[KPIDefinition]:
    """Get all business KPIs"""
    return BUSINESS_KPIS


def get_system_kpis() -> List[KPIDefinition]:
    """Get all system monitoring KPIs"""
    return SYSTEM_KPIS
