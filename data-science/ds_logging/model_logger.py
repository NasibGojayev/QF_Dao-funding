"""
Model Logging Infrastructure for DonCoin DAO
Logs all model inputs, outputs, and performance for traceability.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import threading
from queue import Queue
import time


@dataclass
class ModelPrediction:
    """Represents a single model prediction log entry"""
    request_id: str
    timestamp: str
    model_name: str
    model_version: str
    input_features: Dict[str, Any]
    output: Any
    latency_ms: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExperimentEvent:
    """Represents an experiment event (A/B test, MAB)"""
    event_id: str
    timestamp: str
    experiment_name: str
    experiment_type: str  # 'ab_test' or 'mab'
    user_id: str
    variant: str
    event_type: str  # 'impression', 'conversion'
    value: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ModelLogger:
    """
    Logger for model predictions and experiments.
    
    Features:
    - JSON Lines format for easy parsing
    - Async writing for minimal latency impact
    - Automatic file rotation
    - Structured logging for querying
    """
    
    def __init__(self,
                 log_dir: str = 'logs/',
                 model_log_file: str = 'model_predictions.jsonl',
                 experiment_log_file: str = 'experiments.jsonl',
                 max_file_size_mb: int = 100,
                 async_write: bool = True):
        
        self.log_dir = log_dir
        self.model_log_path = os.path.join(log_dir, model_log_file)
        self.experiment_log_path = os.path.join(log_dir, experiment_log_file)
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.async_write = async_write
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Async write queue
        if async_write:
            self.write_queue: Queue = Queue()
            self.writer_thread = threading.Thread(target=self._async_writer, daemon=True)
            self.writer_thread.start()
    
    def _async_writer(self):
        """Background thread for async log writing"""
        while True:
            try:
                log_entry, log_path = self.write_queue.get(timeout=1)
                self._write_log(log_entry, log_path)
            except:
                pass
    
    def _write_log(self, log_entry: Dict[str, Any], log_path: str):
        """Write a single log entry to file"""
        # Check for rotation
        if os.path.exists(log_path):
            if os.path.getsize(log_path) > self.max_file_size:
                self._rotate_log(log_path)
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _rotate_log(self, log_path: str):
        """Rotate log file when it exceeds max size"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base, ext = os.path.splitext(log_path)
        rotated_path = f"{base}_{timestamp}{ext}"
        os.rename(log_path, rotated_path)
    
    def log_prediction(self,
                       model_name: str,
                       input_features: Dict[str, Any],
                       output: Any,
                       latency_ms: float,
                       model_version: str = '1.0',
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a model prediction.
        
        Args:
            model_name: Name of the model
            input_features: Input features used for prediction
            output: Model output (score, class, etc.)
            latency_ms: Inference latency in milliseconds
            model_version: Version of the model
            metadata: Additional metadata
        
        Returns:
            Request ID for tracing
        """
        request_id = str(uuid.uuid4())
        
        prediction = ModelPrediction(
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            model_name=model_name,
            model_version=model_version,
            input_features=input_features,
            output=output if isinstance(output, (int, float, str, bool, list, dict)) else str(output),
            latency_ms=latency_ms,
            metadata=metadata
        )
        
        log_entry = asdict(prediction)
        
        if self.async_write:
            self.write_queue.put((log_entry, self.model_log_path))
        else:
            self._write_log(log_entry, self.model_log_path)
        
        return request_id
    
    def log_experiment_impression(self,
                                   experiment_name: str,
                                   experiment_type: str,
                                   user_id: str,
                                   variant: str,
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log when a user is exposed to an experiment variant"""
        event_id = str(uuid.uuid4())
        
        event = ExperimentEvent(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            experiment_name=experiment_name,
            experiment_type=experiment_type,
            user_id=user_id,
            variant=variant,
            event_type='impression',
            metadata=metadata
        )
        
        log_entry = asdict(event)
        
        if self.async_write:
            self.write_queue.put((log_entry, self.experiment_log_path))
        else:
            self._write_log(log_entry, self.experiment_log_path)
        
        return event_id
    
    def log_experiment_conversion(self,
                                   experiment_name: str,
                                   experiment_type: str,
                                   user_id: str,
                                   variant: str,
                                   value: float = 1.0,
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log when a user converts in an experiment"""
        event_id = str(uuid.uuid4())
        
        event = ExperimentEvent(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            experiment_name=experiment_name,
            experiment_type=experiment_type,
            user_id=user_id,
            variant=variant,
            event_type='conversion',
            value=value,
            metadata=metadata
        )
        
        log_entry = asdict(event)
        
        if self.async_write:
            self.write_queue.put((log_entry, self.experiment_log_path))
        else:
            self._write_log(log_entry, self.experiment_log_path)
        
        return event_id
    
    def read_prediction_logs(self,
                              model_name: Optional[str] = None,
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None,
                              limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Read prediction logs with optional filtering.
        
        Returns:
            List of log entries
        """
        logs = []
        
        if not os.path.exists(self.model_log_path):
            return logs
        
        with open(self.model_log_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # Apply filters
                if model_name and entry.get('model_name') != model_name:
                    continue
                
                entry_time = datetime.fromisoformat(entry['timestamp'])
                
                if start_time and entry_time < start_time:
                    continue
                
                if end_time and entry_time > end_time:
                    continue
                
                logs.append(entry)
                
                if len(logs) >= limit:
                    break
        
        return logs
    
    def read_experiment_logs(self,
                              experiment_name: Optional[str] = None,
                              event_type: Optional[str] = None,
                              limit: int = 1000) -> List[Dict[str, Any]]:
        """Read experiment logs with optional filtering"""
        logs = []
        
        if not os.path.exists(self.experiment_log_path):
            return logs
        
        with open(self.experiment_log_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                if experiment_name and entry.get('experiment_name') != experiment_name:
                    continue
                
                if event_type and entry.get('event_type') != event_type:
                    continue
                
                logs.append(entry)
                
                if len(logs) >= limit:
                    break
        
        return logs
    
    def get_model_stats(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregate statistics for model predictions"""
        logs = self.read_prediction_logs(model_name=model_name, limit=10000)
        
        if not logs:
            return {'error': 'No logs found'}
        
        latencies = [log['latency_ms'] for log in logs]
        
        # Group by model
        models = {}
        for log in logs:
            name = log['model_name']
            if name not in models:
                models[name] = {'count': 0, 'latencies': []}
            models[name]['count'] += 1
            models[name]['latencies'].append(log['latency_ms'])
        
        stats = {
            'total_predictions': len(logs),
            'avg_latency_ms': sum(latencies) / len(latencies),
            'p50_latency_ms': sorted(latencies)[len(latencies) // 2],
            'p95_latency_ms': sorted(latencies)[int(len(latencies) * 0.95)],
            'max_latency_ms': max(latencies),
            'min_latency_ms': min(latencies),
            'models': {
                name: {
                    'count': data['count'],
                    'avg_latency': sum(data['latencies']) / len(data['latencies'])
                }
                for name, data in models.items()
            }
        }
        
        return stats
    
    def get_experiment_stats(self, experiment_name: str) -> Dict[str, Any]:
        """Get aggregate statistics for an experiment"""
        logs = self.read_experiment_logs(experiment_name=experiment_name, limit=10000)
        
        if not logs:
            return {'error': 'No logs found'}
        
        # Aggregate by variant
        variants = {}
        for log in logs:
            variant = log['variant']
            if variant not in variants:
                variants[variant] = {'impressions': 0, 'conversions': 0, 'value': 0}
            
            if log['event_type'] == 'impression':
                variants[variant]['impressions'] += 1
            elif log['event_type'] == 'conversion':
                variants[variant]['conversions'] += 1
                variants[variant]['value'] += log.get('value', 1.0)
        
        # Calculate conversion rates
        for variant, data in variants.items():
            if data['impressions'] > 0:
                data['conversion_rate'] = data['conversions'] / data['impressions']
            else:
                data['conversion_rate'] = 0
        
        return {
            'experiment_name': experiment_name,
            'total_events': len(logs),
            'variants': variants
        }


# Singleton instance for global use
_logger_instance: Optional[ModelLogger] = None


def get_logger() -> ModelLogger:
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ModelLogger()
    return _logger_instance


if __name__ == "__main__":
    # Demo logging
    print("Model Logger Demo")
    print("=" * 60)
    
    logger = ModelLogger(log_dir='logs/', async_write=False)
    
    # Log some predictions
    print("\n1. Logging model predictions...")
    for i in range(5):
        request_id = logger.log_prediction(
            model_name='risk_scorer',
            model_version='1.0',
            input_features={
                'tx_count': 10 + i,
                'avg_amount': 100 * (i + 1),
                'sybil_score': 0.1 * i
            },
            output=0.2 + 0.1 * i,
            latency_ms=10 + i * 2,
            metadata={'wallet': f'0x{i:040x}'}
        )
        print(f"  Logged prediction: {request_id[:8]}...")
    
    # Log some experiment events
    print("\n2. Logging experiment events...")
    for i in range(10):
        variant = 'control' if i % 2 == 0 else 'treatment'
        
        # Log impression
        logger.log_experiment_impression(
            experiment_name='recommender_v2',
            experiment_type='ab_test',
            user_id=f'user_{i}',
            variant=variant
        )
        
        # Log conversion (50% conversion rate for treatment, 30% for control)
        conv_rate = 0.5 if variant == 'treatment' else 0.3
        if i / 10 < conv_rate:
            logger.log_experiment_conversion(
                experiment_name='recommender_v2',
                experiment_type='ab_test',
                user_id=f'user_{i}',
                variant=variant,
                value=10.0 + i
            )
    
    print("  Logged 10 impressions and conversions")
    
    # Read stats
    print("\n3. Model Statistics:")
    model_stats = logger.get_model_stats()
    print(f"  Total Predictions: {model_stats['total_predictions']}")
    print(f"  Avg Latency: {model_stats['avg_latency_ms']:.2f}ms")
    print(f"  P95 Latency: {model_stats['p95_latency_ms']:.2f}ms")
    
    print("\n4. Experiment Statistics:")
    exp_stats = logger.get_experiment_stats('recommender_v2')
    print(f"  Total Events: {exp_stats['total_events']}")
    for variant, data in exp_stats['variants'].items():
        print(f"  {variant}:")
        print(f"    Impressions: {data['impressions']}")
        print(f"    Conversions: {data['conversions']}")
        print(f"    Conv. Rate: {data['conversion_rate']:.2%}")
    
    print(f"\nLogs written to: {logger.log_dir}")
