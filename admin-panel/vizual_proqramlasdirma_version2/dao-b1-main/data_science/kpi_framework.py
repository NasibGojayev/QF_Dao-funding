"""
KPI Framework for DAO Platform
==============================
Defines and computes all key performance indicators.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class KPIGranularity(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class KPIDefinition:
    """KPI metadata and computation details."""
    name: str
    category: str
    definition: str
    formula: str
    data_source: str
    granularity: KPIGranularity
    purpose: str
    
    
# =============================================================================
# KPI DEFINITIONS
# =============================================================================

KPI_REGISTRY = {
    # Conversion KPIs
    "active_user_rate": KPIDefinition(
        name="Active User Rate",
        category="Conversion",
        definition="Percentage of registered users who made at least 1 transaction in period",
        formula="(users_with_tx / total_users) * 100",
        data_source="transactions, users tables",
        granularity=KPIGranularity.DAILY,
        purpose="Measures user engagement and platform stickiness"
    ),
    "funnel_completion_rate": KPIDefinition(
        name="Funnel Completion Rate",
        category="Conversion",
        definition="Percentage of users who complete wallet->project->donate flow",
        formula="(completed_donations / wallet_connections) * 100",
        data_source="event_logs table",
        granularity=KPIGranularity.DAILY,
        purpose="Identifies conversion bottlenecks"
    ),
    
    # Behavior KPIs
    "avg_tx_per_user": KPIDefinition(
        name="Average Transactions per User",
        category="Behavior",
        definition="Mean number of transactions per active user",
        formula="total_transactions / active_users",
        data_source="transactions table",
        granularity=KPIGranularity.DAILY,
        purpose="Measures transaction frequency behavior"
    ),
    "avg_donation_amount": KPIDefinition(
        name="Average Donation Amount",
        category="Behavior",
        definition="Mean donation value in ETH",
        formula="SUM(amount) / COUNT(transactions)",
        data_source="transactions table",
        granularity=KPIGranularity.DAILY,
        purpose="Tracks donation size trends"
    ),
    
    # Engagement KPIs
    "return_rate": KPIDefinition(
        name="Return Rate",
        category="Engagement",
        definition="Percentage of users who return within 7 days",
        formula="(returning_users / total_users) * 100",
        data_source="transactions table",
        granularity=KPIGranularity.WEEKLY,
        purpose="Measures retention and platform value"
    ),
    "project_funding_velocity": KPIDefinition(
        name="Project Funding Velocity",
        category="Engagement",
        definition="Average time to reach 50% of funding goal",
        formula="AVG(days_to_50_percent)",
        data_source="transactions, projects tables",
        granularity=KPIGranularity.WEEKLY,
        purpose="Measures project attractiveness and platform efficiency"
    ),
    
    # Quality KPIs
    "anomaly_ratio": KPIDefinition(
        name="Anomaly Ratio",
        category="Quality",
        definition="Percentage of transactions flagged as suspicious",
        formula="(flagged_transactions / total_transactions) * 100",
        data_source="transactions, ml_predictions tables",
        granularity=KPIGranularity.DAILY,
        purpose="Monitors fraud detection effectiveness"
    ),
    "false_positive_rate": KPIDefinition(
        name="False Positive Rate",
        category="Quality",
        definition="Percentage of flagged transactions that were legitimate",
        formula="(false_positives / total_flagged) * 100",
        data_source="ml_predictions, manual_reviews tables",
        granularity=KPIGranularity.WEEKLY,
        purpose="Measures model precision and user friction"
    ),
    
    # Operational KPIs
    "model_latency_p95": KPIDefinition(
        name="Model Latency P95",
        category="Operational",
        definition="95th percentile inference time in milliseconds",
        formula="PERCENTILE(inference_time, 0.95)",
        data_source="inference_logs table",
        granularity=KPIGranularity.HOURLY,
        purpose="Monitors model performance in production"
    ),
    "inference_throughput": KPIDefinition(
        name="Inference Throughput",
        category="Operational",
        definition="Number of predictions per second",
        formula="total_predictions / time_period_seconds",
        data_source="inference_logs table",
        granularity=KPIGranularity.HOURLY,
        purpose="Capacity planning and scaling decisions"
    ),
}


# =============================================================================
# KPI COMPUTATION FUNCTIONS
# =============================================================================

class KPIComputer:
    """Computes KPIs from database/dataframes."""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        
    def compute_all(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Compute all KPIs for a date range."""
        return {
            "active_user_rate": self.active_user_rate(start_date, end_date),
            "avg_tx_per_user": self.avg_tx_per_user(start_date, end_date),
            "avg_donation_amount": self.avg_donation_amount(start_date, end_date),
            "return_rate": self.return_rate(start_date, end_date),
            "anomaly_ratio": self.anomaly_ratio(start_date, end_date),
        }
    
    def active_user_rate(self, start_date: datetime, end_date: datetime) -> float:
        """Compute active user rate."""
        # Would query: SELECT COUNT(DISTINCT user_id) FROM transactions WHERE ...
        # Simulated for demo
        total_users = 100
        active_users = 45
        return (active_users / total_users) * 100 if total_users > 0 else 0.0
    
    def avg_tx_per_user(self, start_date: datetime, end_date: datetime) -> float:
        """Compute average transactions per active user."""
        total_tx = 250
        active_users = 45
        return total_tx / active_users if active_users > 0 else 0.0
    
    def avg_donation_amount(self, start_date: datetime, end_date: datetime) -> float:
        """Compute average donation amount in ETH."""
        # Would query: SELECT AVG(amount) FROM transactions WHERE ...
        return 0.85  # ETH
    
    def return_rate(self, start_date: datetime, end_date: datetime) -> float:
        """Compute 7-day return rate."""
        total_users = 100
        returning_users = 35
        return (returning_users / total_users) * 100 if total_users > 0 else 0.0
    
    def anomaly_ratio(self, start_date: datetime, end_date: datetime) -> float:
        """Compute anomaly/suspicious transaction ratio."""
        total_tx = 250
        flagged_tx = 8
        return (flagged_tx / total_tx) * 100 if total_tx > 0 else 0.0
    
    def compute_time_series(self, kpi_name: str, days: int = 30) -> pd.DataFrame:
        """Compute KPI values over time for trend analysis."""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # Generate realistic time-series data
        np.random.seed(42)
        if kpi_name == "active_user_rate":
            base = 45
            values = base + np.cumsum(np.random.randn(days) * 2)
        elif kpi_name == "avg_donation_amount":
            base = 0.8
            values = base + np.cumsum(np.random.randn(days) * 0.05)
        elif kpi_name == "anomaly_ratio":
            base = 3.0
            values = np.abs(base + np.random.randn(days) * 0.5)
        else:
            values = np.random.rand(days) * 100
            
        return pd.DataFrame({
            'date': dates,
            'value': values,
            'kpi': kpi_name
        })


# =============================================================================
# KPI DASHBOARD DATA GENERATOR
# =============================================================================

def generate_kpi_dashboard_data() -> Dict:
    """Generate KPI data for dashboard visualization."""
    computer = KPIComputer()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Current KPI values
    current_kpis = computer.compute_all(start_date, end_date)
    
    # Time series for trends
    kpi_trends = {}
    for kpi_name in ["active_user_rate", "avg_donation_amount", "anomaly_ratio"]:
        kpi_trends[kpi_name] = computer.compute_time_series(kpi_name, days=30)
    
    # Comparison with previous period
    prev_start = start_date - timedelta(days=30)
    prev_kpis = {
        "active_user_rate": 42.0,
        "avg_tx_per_user": 5.2,
        "avg_donation_amount": 0.75,
        "return_rate": 32.0,
        "anomaly_ratio": 3.5,
    }
    
    # Calculate deltas
    deltas = {
        k: ((current_kpis[k] - prev_kpis[k]) / prev_kpis[k] * 100) if prev_kpis[k] != 0 else 0
        for k in current_kpis
    }
    
    return {
        "current": current_kpis,
        "previous": prev_kpis,
        "deltas": deltas,
        "trends": kpi_trends,
        "definitions": KPI_REGISTRY,
    }


if __name__ == "__main__":
    # Demo: Print KPI definitions
    print("=" * 60)
    print("KPI FRAMEWORK - DAO Platform")
    print("=" * 60)
    
    for kpi_id, kpi in KPI_REGISTRY.items():
        print(f"\n📊 {kpi.name} ({kpi.category})")
        print(f"   Definition: {kpi.definition}")
        print(f"   Formula: {kpi.formula}")
        print(f"   Source: {kpi.data_source}")
        print(f"   Granularity: {kpi.granularity.value}")
    
    # Compute current KPIs
    print("\n" + "=" * 60)
    print("CURRENT KPI VALUES")
    print("=" * 60)
    
    dashboard = generate_kpi_dashboard_data()
    for kpi_name, value in dashboard["current"].items():
        delta = dashboard["deltas"][kpi_name]
        arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
        print(f"{kpi_name}: {value:.2f} ({arrow} {abs(delta):.1f}%)")
