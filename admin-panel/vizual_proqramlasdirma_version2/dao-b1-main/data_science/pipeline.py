"""
Main Data Science Pipeline
==========================
ETL -> Feature Store -> Inference Pipeline
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import json
import os
import warnings
warnings.filterwarnings('ignore')

# Import our modules
from kpi_framework import KPIComputer, generate_kpi_dashboard_data
from feature_engineering import create_feature_pipeline, extract_features
from models import ClassificationModels, ClusteringModels, AnomalyDetectionModels
from experimentation import MultiArmedBandit, ABTest
from inference_logging import InferenceLogger, ModelVersionManager, TrackedModel
from visualizations import generate_all_visualizations


# =============================================================================
# PIPELINE CONFIGURATION
# =============================================================================

PIPELINE_CONFIG = {
    "model_name": "fraud_detector",
    "version": "1.0.0",
    "contamination_threshold": 0.05,
    "suspicious_score_threshold": 0.7,
    "log_dir": "logs/inference",
    "models_dir": "models",
    "visualizations_dir": "visualizations",
}


# =============================================================================
# DATA LOADING (ETL)
# =============================================================================

def load_transaction_data(source: str = "sample") -> pd.DataFrame:
    """
    Load transaction data from source.
    
    In production, this would connect to the PostgreSQL database.
    For now, generate sample data.
    """
    if source == "sample":
        np.random.seed(42)
        n_samples = 1000
        
        df = pd.DataFrame({
            'user_id': np.random.randint(1, 100, n_samples),
            'project_id': np.random.randint(1, 30, n_samples),
            'amount': np.random.exponential(0.5, n_samples),
            'created_at': pd.date_range(
                datetime.now() - timedelta(days=30),
                periods=n_samples,
                freq='30T'
            ),
            'tag': np.random.choice(
                ['environment', 'education', 'tech', 'health', 'community'],
                n_samples
            ),
            'success': np.random.choice([True, False], n_samples, p=[0.95, 0.05]),
        })
        
        # Add some anomalies (fraud patterns)
        anomaly_indices = np.random.choice(n_samples, 50, replace=False)
        df.loc[anomaly_indices, 'amount'] *= 10
        
        return df
    
    else:
        # In production: Query from database
        raise NotImplementedError("Database connection not implemented")


# =============================================================================
# FEATURE STORE
# =============================================================================

class FeatureStore:
    """Simple feature store for computed features."""
    
    def __init__(self, cache_dir: str = "feature_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.pipeline = create_feature_pipeline()
        
    def compute_and_cache(self, df: pd.DataFrame, cache_key: str) -> pd.DataFrame:
        """Compute features and cache them."""
        features = self.pipeline.fit_transform(df)
        
        # Skip caching for now to avoid dependency issues
        # In production, use pickle or database
        
        return features
    
    def load_cached(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Load cached features if available."""
        return None  # Caching disabled for simplicity


# =============================================================================
# INFERENCE PIPELINE
# =============================================================================

class InferencePipeline:
    """
    Production inference pipeline.
    
    Flow:
    1. Receive transaction data
    2. Extract features
    3. Make predictions
    4. Apply business rules
    5. Log everything
    6. Return decision
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or PIPELINE_CONFIG
        self.feature_store = FeatureStore()
        self.logger = InferenceLogger(log_dir=self.config["log_dir"])
        self.version_manager = ModelVersionManager(models_dir=self.config["models_dir"])
        
        # Initialize models
        self.anomaly_model = None
        self.classification_model = None
        self.training_columns = []
        
    def train_models(self, df: pd.DataFrame):
        """Train all models on provided data."""
        print("[INFO] Computing features...")
        features = self.feature_store.compute_and_cache(df, "training")
        
        # Get numeric features (exclude datetime/object columns)
        if isinstance(features, pd.DataFrame):
            # Exclude non-numeric columns
            numeric_cols = features.select_dtypes(include=[np.number]).columns.tolist()
            # Store training columns for prediction alignment
            self.training_columns = numeric_cols
            X = features[numeric_cols].fillna(0).values.astype(np.float64)
        else:
            X = np.nan_to_num(features).astype(np.float64)
        
        # Train anomaly detector
        print("[INFO] Training anomaly detector...")
        anomaly = AnomalyDetectionModels(
            contamination=self.config["contamination_threshold"]
        )
        self.anomaly_model, anomaly_info = anomaly.train_isolation_forest(X)
        
        # Register model
        self.version_manager.register_model(
            model=self.anomaly_model,
            model_name="anomaly_detector",
            metrics={"anomaly_ratio": anomaly_info["anomaly_ratio"]},
            hyperparameters=anomaly_info["params"],
            description="Isolation Forest for fraud detection"
        )
        
        # For classification, create labels from anomaly predictions
        y = (self.anomaly_model.predict(X) == -1).astype(int)
        
        print("[INFO] Training classification models...")
        clf = ClassificationModels()
        clf_result = clf.train_logistic_regression(X, y, cv=3)
        self.classification_model = clf_result.model
        
        self.version_manager.register_model(
            model=self.classification_model,
            model_name="fraud_classifier",
            metrics=clf_result.metrics,
            hyperparameters=clf_result.best_params,
            description="Logistic regression for fraud classification"
        )
        
        print("[OK] Models trained and registered!")
        
        return {"anomaly": anomaly_info, "classification": clf_result.metrics}
    
    def predict(self, transaction: Dict) -> Dict:
        """
        Make prediction for a single transaction.
        
        Returns:
            Decision dict with score, label, and recommended action
        """
        import time
        start_time = time.time()
        
        # Convert to DataFrame
        tx_df = pd.DataFrame([transaction])
        
        # Extract features using the same pipeline
        features = self.feature_store.pipeline.transform(tx_df)
        if isinstance(features, pd.DataFrame):
            # Align with training columns
            for col in self.training_columns:
                if col not in features.columns:
                    features[col] = 0
            X = features[self.training_columns].fillna(0).values.astype(np.float64)
        else:
            X = np.nan_to_num(features).astype(np.float64)
        
        # Get predictions
        anomaly_pred = self.anomaly_model.predict(X)[0]
        anomaly_score = -self.anomaly_model.decision_function(X)[0]  # Negative = more anomalous
        
        # Normalize score to 0-1
        fraud_score = min(max((anomaly_score + 0.5) / 1.0, 0), 1)
        
        # Determine action
        if fraud_score > self.config["suspicious_score_threshold"]:
            decision = "FLAG_REVIEW"
            label = 1
        elif anomaly_pred == -1:
            decision = "ADDITIONAL_VERIFICATION"
            label = 1
        else:
            decision = "ALLOW"
            label = 0
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Log inference
        self.logger.log_inference(
            model_name="fraud_detector",
            model_version=self.config["version"],
            input_features={
                "amount": transaction.get("amount"),
                "user_id": transaction.get("user_id"),
                "project_id": transaction.get("project_id"),
            },
            output_score=fraud_score,
            output_label=label,
            inference_latency_ms=latency_ms,
            decision_taken=decision,
            user_id=str(transaction.get("user_id"))
        )
        
        return {
            "fraud_score": fraud_score,
            "is_suspicious": label == 1,
            "decision": decision,
            "latency_ms": latency_ms
        }
    
    def batch_predict(self, transactions: pd.DataFrame) -> pd.DataFrame:
        """Make predictions for a batch of transactions."""
        results = []
        for _, tx in transactions.iterrows():
            result = self.predict(tx.to_dict())
            results.append(result)
        
        return pd.DataFrame(results)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_full_pipeline():
    """Run the complete data science pipeline."""
    print("=" * 60)
    print("DAO DATA SCIENCE PIPELINE")
    print("=" * 60)
    
    # 1. Load data
    print("\n[1] Loading transaction data...")
    df = load_transaction_data("sample")
    print(f"   Loaded {len(df)} transactions")
    
    # 2. Compute KPIs
    print("\n[2] Computing KPIs...")
    kpi_data = generate_kpi_dashboard_data()
    print("   KPI Dashboard Data:")
    for kpi, value in kpi_data["current"].items():
        delta = kpi_data["deltas"][kpi]
        arrow = "+" if delta > 0 else "-"
        print(f"   - {kpi}: {value:.2f} ({arrow} {abs(delta):.1f}%)")
    
    # 3. Train models
    print("\n[3] Training ML Models...")
    pipeline = InferencePipeline()
    train_results = pipeline.train_models(df)
    
    print(f"   Anomaly ratio: {train_results['anomaly']['anomaly_ratio']*100:.1f}%")
    print(f"   Classification F1: {train_results['classification']['f1']:.3f}")
    
    # 4. Run A/B test simulation
    print("\n[4] Running A/B Test Simulation...")
    ab_test = ABTest()
    np.random.seed(42)
    
    for _ in range(500):
        ab_test.record_impression("control")
        ab_test.record_impression("treatment")
        
        if np.random.random() < 0.10:
            ab_test.record_conversion("control")
        if np.random.random() < 0.12:
            ab_test.record_conversion("treatment")
    
    ab_summary = ab_test.get_summary()
    print(f"   Control rate: {ab_summary['control']['rate']}")
    print(f"   Treatment rate: {ab_summary['treatment']['rate']}")
    print(f"   Lift: {ab_summary['lift']}")
    print(f"   Significant: {ab_summary['is_significant']}")
    
    # 5. Run bandit simulation
    print("\n[5] Running Multi-Armed Bandit...")
    bandit = MultiArmedBandit(arms=["model_v1", "model_v2", "model_v3"], strategy="ucb1")
    true_rates = {"model_v1": 0.10, "model_v2": 0.15, "model_v3": 0.12}
    
    np.random.seed(42)
    for _ in range(300):
        arm = bandit.select_arm()
        reward = 1 if np.random.random() < true_rates[arm] else 0
        bandit.update(arm, reward)
    
    print(f"   Recommended model: {bandit.get_recommendation()}")
    
    # 6. Generate visualizations
    print("\n[6] Generating Visualizations...")
    viz_dir = "visualizations"  # Relative to data_science folder
    os.makedirs(viz_dir, exist_ok=True)
    files = generate_all_visualizations(output_dir=viz_dir)
    print(f"   Generated {len(files)} visualization files")
    
    # 7. Sample predictions
    print("\n[7] Sample Predictions...")
    sample_transactions = [
        {"user_id": 1, "project_id": 5, "amount": 0.5, "tag": "education"},
        {"user_id": 2, "project_id": 10, "amount": 5.0, "tag": "tech"},
        {"user_id": 3, "project_id": 15, "amount": 50.0, "tag": "health"},  # High amount
    ]
    
    for tx in sample_transactions:
        result = pipeline.predict(tx)
        print(f"   Amount: {tx['amount']:.2f} ETH -> Score: {result['fraud_score']:.3f}, Decision: {result['decision']}")
    
    # 8. Get inference stats
    print("\n[8] Inference Statistics:")
    stats = pipeline.logger.get_stats()
    print(f"   Total inferences: {stats['total_logs']}")
    print(f"   Avg latency: {stats['avg_latency_ms']:.2f} ms")
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    
    return {
        "kpis": kpi_data["current"],
        "train_results": train_results,
        "ab_test": ab_summary,
        "bandit_recommendation": bandit.get_recommendation(),
        "inference_stats": stats
    }


if __name__ == "__main__":
    results = run_full_pipeline()
