"""
Data Retention Module for DonCoin DAO
Manages data lifecycle, archiving, and deletion policies.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import json
import os
import shutil
import gzip
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DATA_RETENTION_CONFIG, LOGS_DIR


class DataRetentionManager:
    """
    Manages data retention policies for different data types.
    """
    
    def __init__(self, archive_dir: Optional[Path] = None):
        self.archive_dir = archive_dir or LOGS_DIR / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.policies = DATA_RETENTION_CONFIG
        self.execution_log: List[Dict[str, Any]] = []
    
    def get_policy(self, data_type: str) -> Optional[Dict[str, Any]]:
        """Get retention policy for a data type"""
        return self.policies.get(data_type)
    
    def should_archive(self, data_type: str, record_date: datetime) -> bool:
        """Check if a record should be archived"""
        policy = self.get_policy(data_type)
        if not policy or not policy.get('archive_after_days'):
            return False
        
        archive_threshold = datetime.utcnow() - timedelta(days=policy['archive_after_days'])
        return record_date < archive_threshold
    
    def should_delete(self, data_type: str, record_date: datetime) -> bool:
        """Check if a record should be deleted"""
        policy = self.get_policy(data_type)
        if not policy or not policy.get('retention_days'):
            return False
        
        delete_threshold = datetime.utcnow() - timedelta(days=policy['retention_days'])
        return record_date < delete_threshold
    
    def archive_file(self, source_path: Path, data_type: str) -> Optional[Path]:
        """Archive a file by compressing and moving to archive directory"""
        if not source_path.exists():
            return None
        
        # Create archive subdirectory for this data type
        type_archive_dir = self.archive_dir / data_type / datetime.utcnow().strftime('%Y/%m')
        type_archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Compress file
        archive_name = f"{source_path.name}.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.gz"
        archive_path = type_archive_dir / archive_name
        
        with open(source_path, 'rb') as f_in:
            with gzip.open(archive_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Log archival
        self._log_execution('archive', data_type, str(source_path), str(archive_path))
        
        return archive_path
    
    def process_log_rotation(self, log_file: Path, data_type: str) -> Dict[str, Any]:
        """
        Process a log file for rotation based on retention policy.
        Archives old entries and keeps recent ones.
        """
        if not log_file.exists():
            return {'status': 'file_not_found'}
        
        policy = self.get_policy(data_type)
        if not policy:
            return {'status': 'no_policy'}
        
        archive_days = policy.get('archive_after_days', 30)
        retention_days = policy.get('retention_days', 90)
        
        archive_threshold = datetime.utcnow() - timedelta(days=archive_days)
        delete_threshold = datetime.utcnow() - timedelta(days=retention_days)
        
        keep_entries = []
        archive_entries = []
        delete_count = 0
        
        # Process JSONL file
        with open(log_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line)
                    timestamp_str = entry.get('timestamp')
                    if not timestamp_str:
                        keep_entries.append(line)
                        continue
                    
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    if timestamp < delete_threshold:
                        delete_count += 1
                    elif timestamp < archive_threshold:
                        archive_entries.append(line)
                    else:
                        keep_entries.append(line)
                
                except (json.JSONDecodeError, ValueError):
                    keep_entries.append(line)
        
        # Archive old entries
        if archive_entries:
            archive_file = self.archive_dir / data_type / f"{log_file.stem}_{datetime.utcnow().strftime('%Y%m%d')}.jsonl.gz"
            archive_file.parent.mkdir(parents=True, exist_ok=True)
            
            with gzip.open(archive_file, 'at') as f:
                for entry in archive_entries:
                    f.write(entry)
        
        # Rewrite log file with kept entries
        with open(log_file, 'w') as f:
            for entry in keep_entries:
                f.write(entry)
        
        result = {
            'status': 'success',
            'kept': len(keep_entries),
            'archived': len(archive_entries),
            'deleted': delete_count,
        }
        
        self._log_execution('rotation', data_type, str(log_file), result)
        
        return result
    
    def cleanup_archives(self, data_type: str) -> Dict[str, Any]:
        """Delete archives older than retention period"""
        policy = self.get_policy(data_type)
        if not policy or not policy.get('retention_days'):
            return {'status': 'no_policy'}
        
        retention_days = policy['retention_days']
        delete_threshold = datetime.utcnow() - timedelta(days=retention_days)
        
        type_archive_dir = self.archive_dir / data_type
        if not type_archive_dir.exists():
            return {'status': 'no_archives'}
        
        deleted_count = 0
        deleted_bytes = 0
        
        for archive_file in type_archive_dir.rglob('*.gz'):
            # Get file modification time
            mtime = datetime.fromtimestamp(archive_file.stat().st_mtime)
            
            if mtime < delete_threshold:
                deleted_bytes += archive_file.stat().st_size
                archive_file.unlink()
                deleted_count += 1
        
        result = {
            'status': 'success',
            'deleted_files': deleted_count,
            'deleted_bytes': deleted_bytes,
        }
        
        self._log_execution('cleanup', data_type, str(type_archive_dir), result)
        
        return result
    
    def run_all_policies(self) -> Dict[str, Any]:
        """Run retention policies for all data types"""
        results = {}
        
        # Map data types to their log files
        log_file_mapping = {
            'security_logs': [
                LOGS_DIR / 'auth_events.jsonl',
                LOGS_DIR / 'admin_access.jsonl',
                LOGS_DIR / 'rate_limit_events.jsonl',
                LOGS_DIR / 'alerts.jsonl',
                LOGS_DIR / 'siem_events.jsonl',
            ],
            'off_chain_operational': [
                LOGS_DIR / 'api_requests.jsonl',
            ],
            'model_artifacts': [
                # Data science logs are in data-science/logs
            ],
        }
        
        for data_type, log_files in log_file_mapping.items():
            results[data_type] = {
                'rotations': [],
                'cleanup': None
            }
            
            for log_file in log_files:
                if log_file.exists():
                    rotation_result = self.process_log_rotation(log_file, data_type)
                    results[data_type]['rotations'].append({
                        'file': str(log_file),
                        'result': rotation_result
                    })
            
            cleanup_result = self.cleanup_archives(data_type)
            results[data_type]['cleanup'] = cleanup_result
        
        return results
    
    def _log_execution(self, action: str, data_type: str, target: str, result: Any):
        """Log policy execution"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'data_type': data_type,
            'target': target,
            'result': result
        }
        
        self.execution_log.append(log_entry)
        
        # Also write to file
        log_file = LOGS_DIR / 'retention_execution.jsonl'
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_retention_summary(self) -> Dict[str, Any]:
        """Get summary of data retention status"""
        summary = {
            'policies': {},
            'archive_size_bytes': 0,
            'archive_file_count': 0,
        }
        
        for data_type, policy in self.policies.items():
            type_archive_dir = self.archive_dir / data_type
            
            if type_archive_dir.exists():
                files = list(type_archive_dir.rglob('*.gz'))
                size = sum(f.stat().st_size for f in files)
            else:
                files = []
                size = 0
            
            summary['policies'][data_type] = {
                'retention_days': policy.get('retention_days'),
                'archive_after_days': policy.get('archive_after_days'),
                'archive_file_count': len(files),
                'archive_size_bytes': size,
            }
            
            summary['archive_size_bytes'] += size
            summary['archive_file_count'] += len(files)
        
        return summary


# Global retention manager
retention_manager = DataRetentionManager()


# =============================================================================
# CLI COMMANDS
# =============================================================================

def run_retention_policies():
    """CLI command to run retention policies"""
    print("Running data retention policies...")
    results = retention_manager.run_all_policies()
    
    for data_type, type_results in results.items():
        print(f"\n{data_type}:")
        for rotation in type_results.get('rotations', []):
            r = rotation['result']
            print(f"  {rotation['file']}:")
            print(f"    Kept: {r.get('kept', 0)}, Archived: {r.get('archived', 0)}, Deleted: {r.get('deleted', 0)}")
        
        cleanup = type_results.get('cleanup', {})
        if cleanup.get('status') == 'success':
            print(f"  Cleanup: {cleanup.get('deleted_files', 0)} files, {cleanup.get('deleted_bytes', 0)} bytes")


if __name__ == "__main__":
    run_retention_policies()
