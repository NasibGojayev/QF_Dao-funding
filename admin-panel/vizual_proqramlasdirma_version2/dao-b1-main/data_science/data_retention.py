"""
Data Retention Policy Module
============================
Defines what is retained on-chain/off-chain, retention periods, and archival.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
import os


class StorageType(Enum):
    ON_CHAIN = "on_chain"
    OFF_CHAIN = "off_chain"
    HYBRID = "hybrid"


class RetentionPeriod(Enum):
    DAYS_7 = 7
    DAYS_30 = 30
    DAYS_90 = 90
    DAYS_365 = 365
    PERMANENT = -1  # Never delete


@dataclass
class DataRetentionRule:
    """Defines retention rules for a data type."""
    data_type: str
    storage_type: StorageType
    retention_days: int
    archive_after_days: int
    description: str
    gdpr_relevant: bool = False
    

# =============================================================================
# RETENTION POLICY DEFINITIONS
# =============================================================================

RETENTION_POLICIES = {
    # On-Chain Data (Permanent by nature)
    "transactions": DataRetentionRule(
        data_type="transactions",
        storage_type=StorageType.ON_CHAIN,
        retention_days=-1,  # Permanent (blockchain)
        archive_after_days=-1,
        description="Blockchain transactions - permanent by design",
        gdpr_relevant=False  # Pseudonymous wallet addresses
    ),
    "smart_contract_events": DataRetentionRule(
        data_type="smart_contract_events",
        storage_type=StorageType.ON_CHAIN,
        retention_days=-1,
        archive_after_days=-1,
        description="Emitted events from contracts - permanent"
    ),
    
    # Off-Chain Database (PostgreSQL)
    "user_profiles": DataRetentionRule(
        data_type="user_profiles",
        storage_type=StorageType.OFF_CHAIN,
        retention_days=365 * 5,  # 5 years
        archive_after_days=365 * 2,  # Archive after 2 years inactive
        description="User profile data (email, preferences)",
        gdpr_relevant=True  # Contains PII
    ),
    "session_logs": DataRetentionRule(
        data_type="session_logs",
        storage_type=StorageType.OFF_CHAIN,
        retention_days=90,
        archive_after_days=30,
        description="User session and authentication logs"
    ),
    "api_request_logs": DataRetentionRule(
        data_type="api_request_logs",
        storage_type=StorageType.OFF_CHAIN,
        retention_days=30,
        archive_after_days=7,
        description="API request/response logs for debugging"
    ),
    "model_inference_logs": DataRetentionRule(
        data_type="model_inference_logs",
        storage_type=StorageType.OFF_CHAIN,
        retention_days=365,
        archive_after_days=90,
        description="ML model predictions and inputs for auditing"
    ),
    "kpi_snapshots": DataRetentionRule(
        data_type="kpi_snapshots",
        storage_type=StorageType.OFF_CHAIN,
        retention_days=365 * 3,  # 3 years
        archive_after_days=365,
        description="Historical KPI values for trend analysis"
    ),
    
    # Hybrid (Indexed from chain, stored off-chain)
    "indexed_events": DataRetentionRule(
        data_type="indexed_events",
        storage_type=StorageType.HYBRID,
        retention_days=365 * 2,  # 2 years in fast DB
        archive_after_days=90,
        description="Events indexed from blockchain for fast queries"
    ),
    "materialized_views": DataRetentionRule(
        data_type="materialized_views",
        storage_type=StorageType.OFF_CHAIN,
        retention_days=30,
        archive_after_days=-1,  # Regenerate, don't archive
        description="Pre-computed aggregations for dashboards"
    ),
}


# =============================================================================
# ARCHIVAL MANAGER
# =============================================================================

class ArchivalManager:
    """Manages data archival and deletion based on retention policies."""
    
    def __init__(self, archive_dir: str = "archives"):
        self.archive_dir = archive_dir
        os.makedirs(archive_dir, exist_ok=True)
        self.policies = RETENTION_POLICIES
        
    def get_data_age_days(self, created_at: datetime) -> int:
        """Calculate age of data in days."""
        return (datetime.now() - created_at).days
    
    def should_archive(self, data_type: str, created_at: datetime) -> bool:
        """Check if data should be archived based on policy."""
        if data_type not in self.policies:
            return False
            
        policy = self.policies[data_type]
        age_days = self.get_data_age_days(created_at)
        
        if policy.archive_after_days < 0:
            return False
            
        return age_days >= policy.archive_after_days
    
    def should_delete(self, data_type: str, created_at: datetime) -> bool:
        """Check if data should be deleted based on policy."""
        if data_type not in self.policies:
            return False
            
        policy = self.policies[data_type]
        age_days = self.get_data_age_days(created_at)
        
        if policy.retention_days < 0:  # Permanent
            return False
            
        return age_days >= policy.retention_days
    
    def archive_data(self, data_type: str, data: Dict, data_id: str) -> str:
        """Archive data to cold storage."""
        archive_path = os.path.join(
            self.archive_dir,
            data_type,
            datetime.now().strftime("%Y-%m"),
            f"{data_id}.json"
        )
        
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        
        archive_record = {
            "data_type": data_type,
            "data_id": data_id,
            "archived_at": datetime.now().isoformat(),
            "data": data
        }
        
        with open(archive_path, 'w') as f:
            json.dump(archive_record, f, indent=2, default=str)
            
        return archive_path
    
    def run_retention_check(self) -> Dict[str, int]:
        """
        Run retention policy check across all data types.
        Returns counts of records marked for archival/deletion.
        
        In production, this would query each database table.
        """
        results = {
            "checked": 0,
            "to_archive": 0,
            "to_delete": 0,
            "permanent": 0
        }
        
        for data_type, policy in self.policies.items():
            results["checked"] += 1
            
            if policy.retention_days < 0:
                results["permanent"] += 1
            else:
                # In production: query count of records older than thresholds
                pass
                
        return results
    
    def get_policy_summary(self) -> List[Dict]:
        """Get human-readable summary of all retention policies."""
        summary = []
        
        for data_type, policy in self.policies.items():
            retention = "Permanent" if policy.retention_days < 0 else f"{policy.retention_days} days"
            archive = "N/A" if policy.archive_after_days < 0 else f"{policy.archive_after_days} days"
            
            summary.append({
                "Data Type": data_type,
                "Storage": policy.storage_type.value,
                "Retention": retention,
                "Archive After": archive,
                "GDPR": "Yes" if policy.gdpr_relevant else "No"
            })
            
        return summary


# =============================================================================
# GDPR COMPLIANCE HELPERS
# =============================================================================

class GDPRManager:
    """Handles GDPR-related data requests."""
    
    def __init__(self, archival_manager: ArchivalManager):
        self.archival = archival_manager
        
    def get_gdpr_relevant_data_types(self) -> List[str]:
        """Get list of data types that contain PII."""
        return [
            dt for dt, policy in self.archival.policies.items()
            if policy.gdpr_relevant
        ]
    
    def export_user_data(self, user_id: str) -> Dict:
        """
        Export all user data for GDPR data portability request.
        
        In production, this would query all tables containing user data.
        """
        return {
            "user_id": user_id,
            "exported_at": datetime.now().isoformat(),
            "data_types": self.get_gdpr_relevant_data_types(),
            "note": "Full data export would include all user records"
        }
    
    def delete_user_data(self, user_id: str) -> Dict:
        """
        Delete all user data for GDPR right-to-be-forgotten request.
        
        In production, this would delete from all tables.
        """
        return {
            "user_id": user_id,
            "deleted_at": datetime.now().isoformat(),
            "status": "scheduled",
            "note": "On-chain data cannot be deleted (pseudonymous)"
        }


if __name__ == "__main__":
    print("=" * 60)
    print("DATA RETENTION POLICY")
    print("=" * 60)
    
    manager = ArchivalManager()
    summary = manager.get_policy_summary()
    
    # Print as table
    print(f"\n{'Data Type':<25} {'Storage':<12} {'Retention':<15} {'Archive':<12} {'GDPR':<5}")
    print("-" * 70)
    
    for row in summary:
        print(f"{row['Data Type']:<25} {row['Storage']:<12} {row['Retention']:<15} {row['Archive After']:<12} {row['GDPR']:<5}")
    
    print("\n" + "=" * 60)
    print("GDPR-RELEVANT DATA TYPES")
    print("=" * 60)
    
    gdpr = GDPRManager(manager)
    for dt in gdpr.get_gdpr_relevant_data_types():
        print(f"  - {dt}")
