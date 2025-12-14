"""
Inference Logging and Model Versioning
=======================================
Tracks every model prediction for reproducibility and auditing.
"""
import json
import time
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
import numpy as np
import pickle
import os


# =============================================================================
# INFERENCE LOG ENTRY
# =============================================================================

@dataclass
class InferenceLog:
    """Single inference log entry."""
    log_id: str
    timestamp: str
    model_name: str
    model_version: str
    input_features: Dict[str, Any]
    output_score: float
    output_label: Optional[Any]
    inference_latency_ms: float
    decision_taken: Optional[str]
    user_id: Optional[str]
    request_metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


# =============================================================================
# INFERENCE LOGGER
# =============================================================================

class InferenceLogger:
    """
    Logs all model inferences for:
    - Reproducibility
    - Auditing
    - Performance monitoring
    - Debugging
    """
    
    def __init__(self, log_dir: str = "logs/inference"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logs: List[InferenceLog] = []
        self.current_file = self._get_log_filename()
        
    def _get_log_filename(self) -> Path:
        """Get log file for current date."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"inference_{date_str}.jsonl"
    
    def _generate_log_id(self) -> str:
        """Generate unique log ID."""
        return str(uuid.uuid4())[:8]
    
    def log_inference(
        self,
        model_name: str,
        model_version: str,
        input_features: Dict[str, Any],
        output_score: float,
        output_label: Any = None,
        inference_latency_ms: float = 0.0,
        decision_taken: str = None,
        user_id: str = None,
        metadata: Dict = None
    ) -> InferenceLog:
        """
        Log a single inference.
        
        Args:
            model_name: Name of the model
            model_version: Version string
            input_features: Input feature dictionary
            output_score: Model output score/probability
            output_label: Predicted class label
            inference_latency_ms: Inference time in milliseconds
            decision_taken: Downstream action taken based on prediction
            user_id: User identifier (if applicable)
            metadata: Additional metadata
            
        Returns:
            InferenceLog entry
        """
        log_entry = InferenceLog(
            log_id=self._generate_log_id(),
            timestamp=datetime.now().isoformat(),
            model_name=model_name,
            model_version=model_version,
            input_features=self._serialize_features(input_features),
            output_score=float(output_score),
            output_label=output_label,
            inference_latency_ms=float(inference_latency_ms),
            decision_taken=decision_taken,
            user_id=user_id,
            request_metadata=metadata or {}
        )
        
        self.logs.append(log_entry)
        self._write_log(log_entry)
        
        return log_entry
    
    def _serialize_features(self, features: Dict) -> Dict:
        """Convert numpy arrays to lists for JSON serialization."""
        serialized = {}
        for k, v in features.items():
            if isinstance(v, np.ndarray):
                serialized[k] = v.tolist()
            elif isinstance(v, (np.integer, np.floating)):
                serialized[k] = float(v)
            else:
                serialized[k] = v
        return serialized
    
    def _write_log(self, log_entry: InferenceLog):
        """Append log entry to file."""
        with open(self.current_file, 'a') as f:
            f.write(log_entry.to_json() + '\n')
    
    def get_logs(self, n: int = None) -> List[Dict]:
        """Get recent logs."""
        logs = [log.to_dict() for log in self.logs]
        if n:
            return logs[-n:]
        return logs
    
    def get_stats(self) -> Dict:
        """Get logging statistics."""
        if not self.logs:
            return {"total_logs": 0}
            
        latencies = [log.inference_latency_ms for log in self.logs]
        
        return {
            "total_logs": len(self.logs),
            "avg_latency_ms": np.mean(latencies),
            "p50_latency_ms": np.percentile(latencies, 50),
            "p95_latency_ms": np.percentile(latencies, 95),
            "p99_latency_ms": np.percentile(latencies, 99),
            "models_used": list(set(log.model_name for log in self.logs)),
            "first_log": self.logs[0].timestamp,
            "last_log": self.logs[-1].timestamp
        }


# =============================================================================
# MODEL VERSION MANAGER
# =============================================================================

@dataclass
class ModelVersion:
    """Metadata for a model version."""
    model_name: str
    version: str
    created_at: str
    model_hash: str
    metrics: Dict[str, float]
    hyperparameters: Dict
    training_data_hash: str
    description: str = ""


class ModelVersionManager:
    """
    Manages model versioning for:
    - Reproducibility
    - Rollback capability
    - A/B testing different versions
    """
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.models_dir / "registry.json"
        self.registry: Dict[str, List[ModelVersion]] = self._load_registry()
        
    def _load_registry(self) -> Dict:
        """Load model registry from disk."""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                data = json.load(f)
                return {k: [ModelVersion(**v) for v in versions] for k, versions in data.items()}
        return {}
    
    def _save_registry(self):
        """Save registry to disk."""
        data = {k: [asdict(v) for v in versions] for k, versions in self.registry.items()}
        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _compute_hash(self, model) -> str:
        """Compute hash of model object."""
        model_bytes = pickle.dumps(model)
        return hashlib.md5(model_bytes).hexdigest()[:8]
    
    def _generate_version(self, model_name: str) -> str:
        """Generate next version number."""
        if model_name not in self.registry:
            return "1.0.0"
        
        latest = self.registry[model_name][-1].version
        parts = latest.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        return '.'.join(parts)
    
    def register_model(
        self,
        model,
        model_name: str,
        metrics: Dict[str, float],
        hyperparameters: Dict,
        training_data_hash: str = "",
        description: str = ""
    ) -> ModelVersion:
        """
        Register a new model version.
        
        Args:
            model: Trained model object
            model_name: Name of the model
            metrics: Performance metrics
            hyperparameters: Training hyperparameters
            training_data_hash: Hash of training data
            description: Description of this version
            
        Returns:
            ModelVersion metadata
        """
        version = self._generate_version(model_name)
        model_hash = self._compute_hash(model)
        
        # Save model file
        model_file = self.models_dir / f"{model_name}_{version}.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        
        # Create version entry
        version_entry = ModelVersion(
            model_name=model_name,
            version=version,
            created_at=datetime.now().isoformat(),
            model_hash=model_hash,
            metrics=metrics,
            hyperparameters=hyperparameters,
            training_data_hash=training_data_hash,
            description=description
        )
        
        if model_name not in self.registry:
            self.registry[model_name] = []
        self.registry[model_name].append(version_entry)
        
        self._save_registry()
        
        return version_entry
    
    def load_model(self, model_name: str, version: str = None):
        """
        Load a model by name and version.
        
        Args:
            model_name: Name of the model
            version: Version string (None = latest)
            
        Returns:
            Loaded model object
        """
        if model_name not in self.registry:
            raise ValueError(f"Model '{model_name}' not found in registry")
        
        if version is None:
            version = self.registry[model_name][-1].version
        
        model_file = self.models_dir / f"{model_name}_{version}.pkl"
        
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")
        
        with open(model_file, 'rb') as f:
            return pickle.load(f)
    
    def get_versions(self, model_name: str) -> List[Dict]:
        """Get all versions of a model."""
        if model_name not in self.registry:
            return []
        return [asdict(v) for v in self.registry[model_name]]
    
    def get_latest_version(self, model_name: str) -> str:
        """Get latest version string for a model."""
        if model_name not in self.registry or not self.registry[model_name]:
            return None
        return self.registry[model_name][-1].version


# =============================================================================
# WRAPPED INFERENCE FUNCTION
# =============================================================================

class TrackedModel:
    """
    Wrapper that automatically logs all predictions.
    
    Usage:
        model = TrackedModel(sklearn_model, "fraud_detector", "1.0.0")
        prediction = model.predict(X)  # Automatically logged
    """
    
    def __init__(
        self, 
        model, 
        model_name: str, 
        model_version: str,
        logger: InferenceLogger = None
    ):
        self.model = model
        self.model_name = model_name
        self.model_version = model_version
        self.logger = logger or InferenceLogger()
    
    def predict(self, X, user_id: str = None) -> np.ndarray:
        """Make prediction with automatic logging."""
        start_time = time.time()
        
        # Make prediction
        predictions = self.model.predict(X)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Log each prediction
        for i, pred in enumerate(predictions):
            features = {f"feature_{j}": float(X[i, j]) for j in range(X.shape[1])} if hasattr(X, 'shape') else {"input": X[i]}
            
            self.logger.log_inference(
                model_name=self.model_name,
                model_version=self.model_version,
                input_features=features,
                output_score=float(pred),
                output_label=int(pred) if hasattr(pred, '__int__') else pred,
                inference_latency_ms=latency_ms / len(predictions),
                user_id=user_id
            )
        
        return predictions
    
    def predict_proba(self, X, user_id: str = None) -> np.ndarray:
        """Make probability prediction with logging."""
        start_time = time.time()
        
        probas = self.model.predict_proba(X)
        
        latency_ms = (time.time() - start_time) * 1000
        
        for i, proba in enumerate(probas):
            features = {f"feature_{j}": float(X[i, j]) for j in range(X.shape[1])} if hasattr(X, 'shape') else {"input": X[i]}
            
            self.logger.log_inference(
                model_name=self.model_name,
                model_version=self.model_version,
                input_features=features,
                output_score=float(proba[1]) if len(proba) > 1 else float(proba[0]),
                inference_latency_ms=latency_ms / len(probas),
                user_id=user_id
            )
        
        return probas


if __name__ == "__main__":
    print("=" * 60)
    print("INFERENCE LOGGING DEMO")
    print("=" * 60)
    
    # Demo logger
    logger = InferenceLogger(log_dir="data_science/logs/inference")
    
    # Simulate some inferences
    np.random.seed(42)
    for i in range(10):
        features = {
            "amount": np.random.uniform(0.1, 5.0),
            "user_tx_count": np.random.randint(1, 100),
            "amount_zscore": np.random.randn()
        }
        
        logger.log_inference(
            model_name="fraud_detector",
            model_version="1.2.0",
            input_features=features,
            output_score=np.random.random(),
            output_label=np.random.choice([0, 1]),
            inference_latency_ms=np.random.uniform(1, 10),
            decision_taken="allow" if np.random.random() > 0.1 else "flag_review",
            user_id=f"user_{np.random.randint(1, 100)}"
        )
    
    # Print stats
    stats = logger.get_stats()
    print("\nInference Statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # Demo version manager
    print("\n" + "=" * 60)
    print("MODEL VERSION MANAGER DEMO")
    print("=" * 60)
    
    from sklearn.linear_model import LogisticRegression
    
    manager = ModelVersionManager(models_dir="data_science/models")
    
    # Create and register a simple model
    model = LogisticRegression()
    X = np.random.randn(100, 5)
    y = (X[:, 0] > 0).astype(int)
    model.fit(X, y)
    
    version = manager.register_model(
        model=model,
        model_name="demo_classifier",
        metrics={"accuracy": 0.85, "f1": 0.83},
        hyperparameters={"C": 1.0, "solver": "lbfgs"},
        description="Demo model for testing"
    )
    
    print(f"\nRegistered: {version.model_name} v{version.version}")
    print(f"Hash: {version.model_hash}")
    print(f"Metrics: {version.metrics}")
