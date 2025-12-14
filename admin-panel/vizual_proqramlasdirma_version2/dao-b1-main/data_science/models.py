"""
ML Models for DAO Platform
==========================
Classification, Clustering, Anomaly Detection, Time-Series

Implements multiple model families with hyperparameter tuning.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.cluster import KMeans, DBSCAN
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    silhouette_score
)
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import pickle
import json
import time
import warnings
warnings.filterwarnings('ignore')

# Try importing optional dependencies
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


# =============================================================================
# MODEL CONFIGURATIONS WITH HYPERPARAMETERS
# =============================================================================

HYPERPARAMETERS = {
    # Classification Models
    "logistic_regression": {
        "C": [0.01, 0.1, 1.0, 10.0],
        "penalty": ["l1", "l2"],
        "solver": ["liblinear", "saga"],
        "max_iter": [1000],
    },
    "random_forest": {
        "n_estimators": [50, 100, 200],
        "max_depth": [5, 10, 20, None],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "class_weight": ["balanced", None],
    },
    "xgboost": {
        "n_estimators": [50, 100, 200],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.01, 0.1, 0.2],
        "subsample": [0.8, 1.0],
        "colsample_bytree": [0.8, 1.0],
    },
    
    # Clustering Models
    "kmeans": {
        "n_clusters": [3, 4, 5, 6, 7, 8],
        "init": ["k-means++", "random"],
        "n_init": [10, 20],
        "max_iter": [300],
    },
    "dbscan": {
        "eps": [0.3, 0.5, 0.7, 1.0],
        "min_samples": [3, 5, 10],
        "metric": ["euclidean", "manhattan"],
    },
    
    # Anomaly Detection
    "isolation_forest": {
        "n_estimators": [50, 100, 200],
        "contamination": [0.01, 0.05, 0.1],
        "max_features": [0.5, 0.8, 1.0],
        "bootstrap": [True, False],
    },
    "one_class_svm": {
        "kernel": ["rbf", "poly"],
        "gamma": ["scale", "auto", 0.1, 0.01],
        "nu": [0.01, 0.05, 0.1],
    },
}


@dataclass
class ModelResult:
    """Container for model training results."""
    model_name: str
    model: Any
    best_params: Dict
    metrics: Dict[str, float]
    training_time: float
    feature_importance: Optional[Dict[str, float]] = None


# =============================================================================
# CLASSIFICATION MODELS
# =============================================================================

class ClassificationModels:
    """Classification models for fraud detection, user segmentation, etc."""
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models: Dict[str, ModelResult] = {}
        self.scaler = StandardScaler()
        
    def train_logistic_regression(
        self, X: np.ndarray, y: np.ndarray, cv: int = 5
    ) -> ModelResult:
        """Train Logistic Regression with hyperparameter tuning."""
        start_time = time.time()
        
        model = LogisticRegression(random_state=self.random_state)
        grid = GridSearchCV(
            model, 
            HYPERPARAMETERS["logistic_regression"],
            cv=cv, 
            scoring='f1',
            n_jobs=-1
        )
        grid.fit(X, y)
        
        training_time = time.time() - start_time
        
        # Get predictions for metrics
        y_pred = grid.predict(X)
        y_proba = grid.predict_proba(X)[:, 1]
        
        metrics = {
            "accuracy": accuracy_score(y, y_pred),
            "precision": precision_score(y, y_pred, zero_division=0),
            "recall": recall_score(y, y_pred, zero_division=0),
            "f1": f1_score(y, y_pred, zero_division=0),
            "auc_roc": roc_auc_score(y, y_proba) if len(np.unique(y)) > 1 else 0,
        }
        
        # Feature importance (coefficients)
        feature_importance = dict(enumerate(np.abs(grid.best_estimator_.coef_[0])))
        
        result = ModelResult(
            model_name="logistic_regression",
            model=grid.best_estimator_,
            best_params=grid.best_params_,
            metrics=metrics,
            training_time=training_time,
            feature_importance=feature_importance
        )
        
        self.models["logistic_regression"] = result
        return result
    
    def train_random_forest(
        self, X: np.ndarray, y: np.ndarray, cv: int = 5
    ) -> ModelResult:
        """Train Random Forest with hyperparameter tuning."""
        start_time = time.time()
        
        model = RandomForestClassifier(random_state=self.random_state)
        
        # Use smaller grid for faster training
        param_grid = {
            "n_estimators": [50, 100],
            "max_depth": [5, 10, None],
            "min_samples_split": [2, 5],
        }
        
        grid = GridSearchCV(model, param_grid, cv=cv, scoring='f1', n_jobs=-1)
        grid.fit(X, y)
        
        training_time = time.time() - start_time
        
        y_pred = grid.predict(X)
        y_proba = grid.predict_proba(X)[:, 1]
        
        metrics = {
            "accuracy": accuracy_score(y, y_pred),
            "precision": precision_score(y, y_pred, zero_division=0),
            "recall": recall_score(y, y_pred, zero_division=0),
            "f1": f1_score(y, y_pred, zero_division=0),
            "auc_roc": roc_auc_score(y, y_proba) if len(np.unique(y)) > 1 else 0,
        }
        
        # Feature importance
        feature_importance = dict(enumerate(grid.best_estimator_.feature_importances_))
        
        result = ModelResult(
            model_name="random_forest",
            model=grid.best_estimator_,
            best_params=grid.best_params_,
            metrics=metrics,
            training_time=training_time,
            feature_importance=feature_importance
        )
        
        self.models["random_forest"] = result
        return result
    
    def train_xgboost(
        self, X: np.ndarray, y: np.ndarray, cv: int = 5
    ) -> ModelResult:
        """Train XGBoost with hyperparameter tuning."""
        if not HAS_XGBOOST:
            raise ImportError("XGBoost not installed. Run: pip install xgboost")
            
        start_time = time.time()
        
        model = XGBClassifier(
            random_state=self.random_state,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        
        param_grid = {
            "n_estimators": [50, 100],
            "max_depth": [3, 5],
            "learning_rate": [0.1, 0.2],
        }
        
        grid = GridSearchCV(model, param_grid, cv=cv, scoring='f1', n_jobs=-1)
        grid.fit(X, y)
        
        training_time = time.time() - start_time
        
        y_pred = grid.predict(X)
        y_proba = grid.predict_proba(X)[:, 1]
        
        metrics = {
            "accuracy": accuracy_score(y, y_pred),
            "precision": precision_score(y, y_pred, zero_division=0),
            "recall": recall_score(y, y_pred, zero_division=0),
            "f1": f1_score(y, y_pred, zero_division=0),
            "auc_roc": roc_auc_score(y, y_proba) if len(np.unique(y)) > 1 else 0,
        }
        
        feature_importance = dict(enumerate(grid.best_estimator_.feature_importances_))
        
        result = ModelResult(
            model_name="xgboost",
            model=grid.best_estimator_,
            best_params=grid.best_params_,
            metrics=metrics,
            training_time=training_time,
            feature_importance=feature_importance
        )
        
        self.models["xgboost"] = result
        return result
    
    def train_all(self, X: np.ndarray, y: np.ndarray) -> Dict[str, ModelResult]:
        """Train all classification models and return comparison."""
        results = {}
        
        # Logistic Regression (baseline)
        print("Training Logistic Regression...")
        results["logistic_regression"] = self.train_logistic_regression(X, y)
        
        # Random Forest
        print("Training Random Forest...")
        results["random_forest"] = self.train_random_forest(X, y)
        
        # XGBoost (if available)
        if HAS_XGBOOST:
            print("Training XGBoost...")
            results["xgboost"] = self.train_xgboost(X, y)
            
        return results
    
    def get_best_model(self) -> ModelResult:
        """Return best model based on F1 score."""
        if not self.models:
            raise ValueError("No models trained yet")
        return max(self.models.values(), key=lambda x: x.metrics["f1"])


# =============================================================================
# CLUSTERING MODELS
# =============================================================================

class ClusteringModels:
    """Clustering models for user segmentation."""
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models: Dict[str, Any] = {}
        self.scaler = StandardScaler()
        
    def train_kmeans(
        self, X: np.ndarray, n_clusters_range: List[int] = None
    ) -> Tuple[KMeans, Dict]:
        """Train K-Means with elbow method."""
        n_clusters_range = n_clusters_range or [2, 3, 4, 5, 6, 7, 8]
        
        X_scaled = self.scaler.fit_transform(X)
        
        results = []
        for k in n_clusters_range:
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            kmeans.fit(X_scaled)
            
            silhouette = silhouette_score(X_scaled, kmeans.labels_) if k > 1 else 0
            results.append({
                "n_clusters": k,
                "inertia": kmeans.inertia_,
                "silhouette": silhouette,
                "model": kmeans
            })
        
        # Select best by silhouette score
        best = max(results, key=lambda x: x["silhouette"])
        
        self.models["kmeans"] = {
            "model": best["model"],
            "n_clusters": best["n_clusters"],
            "silhouette": best["silhouette"],
            "elbow_data": [(r["n_clusters"], r["inertia"]) for r in results]
        }
        
        return best["model"], self.models["kmeans"]
    
    def train_dbscan(
        self, X: np.ndarray, eps_range: List[float] = None
    ) -> Tuple[DBSCAN, Dict]:
        """Train DBSCAN with parameter search."""
        eps_range = eps_range or [0.3, 0.5, 0.7, 1.0]
        
        X_scaled = self.scaler.fit_transform(X)
        
        best_silhouette = -1
        best_model = None
        best_params = {}
        
        for eps in eps_range:
            for min_samples in [3, 5, 10]:
                dbscan = DBSCAN(eps=eps, min_samples=min_samples)
                labels = dbscan.fit_predict(X_scaled)
                
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                
                if n_clusters > 1:
                    # Only calculate silhouette for non-noise points
                    mask = labels != -1
                    if mask.sum() > 1:
                        silhouette = silhouette_score(X_scaled[mask], labels[mask])
                        
                        if silhouette > best_silhouette:
                            best_silhouette = silhouette
                            best_model = dbscan
                            best_params = {
                                "eps": eps,
                                "min_samples": min_samples,
                                "n_clusters": n_clusters,
                                "noise_ratio": (~mask).mean()
                            }
        
        if best_model is None:
            # Fallback
            best_model = DBSCAN(eps=0.5, min_samples=5)
            best_model.fit(X_scaled)
            best_params = {"eps": 0.5, "min_samples": 5}
            
        self.models["dbscan"] = {
            "model": best_model,
            "params": best_params,
            "silhouette": best_silhouette
        }
        
        return best_model, self.models["dbscan"]


# =============================================================================
# ANOMALY DETECTION MODELS
# =============================================================================

class AnomalyDetectionModels:
    """Anomaly detection for fraud/suspicious activity."""
    
    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.models: Dict[str, Any] = {}
        self.scaler = StandardScaler()
        
    def train_isolation_forest(self, X: np.ndarray) -> Tuple[IsolationForest, Dict]:
        """Train Isolation Forest for anomaly detection."""
        start_time = time.time()
        
        X_scaled = self.scaler.fit_transform(X)
        
        # Grid search for best parameters
        best_score = float('inf')
        best_model = None
        best_params = {}
        
        for n_estimators in [50, 100, 200]:
            for max_features in [0.5, 0.8, 1.0]:
                model = IsolationForest(
                    n_estimators=n_estimators,
                    max_features=max_features,
                    contamination=self.contamination,
                    random_state=self.random_state,
                    n_jobs=-1
                )
                model.fit(X_scaled)
                
                # Score: lower is more anomalous
                scores = model.decision_function(X_scaled)
                anomalies = model.predict(X_scaled)
                anomaly_ratio = (anomalies == -1).mean()
                
                # We want anomaly ratio close to contamination
                score_diff = abs(anomaly_ratio - self.contamination)
                
                if score_diff < best_score:
                    best_score = score_diff
                    best_model = model
                    best_params = {
                        "n_estimators": n_estimators,
                        "max_features": max_features,
                        "contamination": self.contamination
                    }
        
        training_time = time.time() - start_time
        
        predictions = best_model.predict(X_scaled)
        
        self.models["isolation_forest"] = {
            "model": best_model,
            "params": best_params,
            "training_time": training_time,
            "anomaly_count": (predictions == -1).sum(),
            "anomaly_ratio": (predictions == -1).mean()
        }
        
        return best_model, self.models["isolation_forest"]
    
    def train_one_class_svm(self, X: np.ndarray) -> Tuple[OneClassSVM, Dict]:
        """Train One-Class SVM for anomaly detection."""
        start_time = time.time()
        
        X_scaled = self.scaler.fit_transform(X)
        
        # Subsample for faster training if dataset is large
        if len(X_scaled) > 5000:
            idx = np.random.choice(len(X_scaled), 5000, replace=False)
            X_train = X_scaled[idx]
        else:
            X_train = X_scaled
        
        model = OneClassSVM(
            kernel='rbf',
            gamma='scale',
            nu=self.contamination
        )
        model.fit(X_train)
        
        training_time = time.time() - start_time
        
        predictions = model.predict(X_scaled)
        
        self.models["one_class_svm"] = {
            "model": model,
            "params": {"kernel": "rbf", "gamma": "scale", "nu": self.contamination},
            "training_time": training_time,
            "anomaly_count": (predictions == -1).sum(),
            "anomaly_ratio": (predictions == -1).mean()
        }
        
        return model, self.models["one_class_svm"]
    
    def train_lof(self, X: np.ndarray, n_neighbors: int = 20) -> Tuple[LocalOutlierFactor, Dict]:
        """Train Local Outlier Factor."""
        start_time = time.time()
        
        X_scaled = self.scaler.fit_transform(X)
        
        model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=self.contamination,
            novelty=True
        )
        model.fit(X_scaled)
        
        training_time = time.time() - start_time
        
        predictions = model.predict(X_scaled)
        
        self.models["lof"] = {
            "model": model,
            "params": {"n_neighbors": n_neighbors, "contamination": self.contamination},
            "training_time": training_time,
            "anomaly_count": (predictions == -1).sum(),
            "anomaly_ratio": (predictions == -1).mean()
        }
        
        return model, self.models["lof"]
    
    def train_all(self, X: np.ndarray) -> Dict:
        """Train all anomaly detection models."""
        results = {}
        
        print("Training Isolation Forest...")
        _, results["isolation_forest"] = self.train_isolation_forest(X)
        
        print("Training One-Class SVM...")
        _, results["one_class_svm"] = self.train_one_class_svm(X)
        
        print("Training LOF...")
        _, results["lof"] = self.train_lof(X)
        
        return results


# =============================================================================
# TIME SERIES MODELS
# =============================================================================

class TimeSeriesModels:
    """Time series models for forecasting."""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        
    def train_arima(
        self, series: pd.Series, order: Tuple[int, int, int] = (1, 1, 1)
    ) -> Dict:
        """Train ARIMA model."""
        if not HAS_STATSMODELS:
            raise ImportError("statsmodels not installed")
            
        start_time = time.time()
        
        model = ARIMA(series, order=order)
        fitted = model.fit()
        
        training_time = time.time() - start_time
        
        # Forecast next 7 periods
        forecast = fitted.forecast(steps=7)
        
        self.models["arima"] = {
            "model": fitted,
            "order": order,
            "training_time": training_time,
            "aic": fitted.aic,
            "bic": fitted.bic,
            "forecast": forecast.tolist()
        }
        
        return self.models["arima"]
    
    def train_exponential_smoothing(
        self, series: pd.Series, seasonal_periods: int = 7
    ) -> Dict:
        """Train Exponential Smoothing model."""
        if not HAS_STATSMODELS:
            raise ImportError("statsmodels not installed")
            
        start_time = time.time()
        
        model = ExponentialSmoothing(
            series,
            seasonal_periods=seasonal_periods,
            trend='add',
            seasonal='add' if len(series) >= 2 * seasonal_periods else None
        )
        fitted = model.fit()
        
        training_time = time.time() - start_time
        
        forecast = fitted.forecast(steps=7)
        
        self.models["exp_smoothing"] = {
            "model": fitted,
            "seasonal_periods": seasonal_periods,
            "training_time": training_time,
            "aic": fitted.aic,
            "forecast": forecast.tolist()
        }
        
        return self.models["exp_smoothing"]


# =============================================================================
# MODEL COMPARISON
# =============================================================================

def compare_models(results: Dict[str, ModelResult]) -> pd.DataFrame:
    """Compare multiple model results."""
    comparison = []
    
    for name, result in results.items():
        row = {
            "model": name,
            "training_time": result.training_time,
            **result.metrics,
            "best_params": str(result.best_params)
        }
        comparison.append(row)
    
    return pd.DataFrame(comparison).sort_values("f1", ascending=False)


if __name__ == "__main__":
    print("=" * 60)
    print("ML MODELS - DAO Platform")
    print("=" * 60)
    
    # Generate synthetic data
    np.random.seed(42)
    n_samples = 500
    n_features = 10
    
    X = np.random.randn(n_samples, n_features)
    y = (X[:, 0] + X[:, 1] * 0.5 + np.random.randn(n_samples) * 0.3 > 0).astype(int)
    
    # Classification
    print("\n📊 Classification Models")
    print("-" * 40)
    clf = ClassificationModels()
    clf_results = clf.train_all(X, y)
    
    comparison = compare_models(clf_results)
    print(comparison[["model", "f1", "auc_roc", "training_time"]].to_string(index=False))
    
    # Clustering
    print("\n📊 Clustering Models")
    print("-" * 40)
    cluster = ClusteringModels()
    kmeans_model, kmeans_result = cluster.train_kmeans(X)
    print(f"K-Means: {kmeans_result['n_clusters']} clusters, silhouette={kmeans_result['silhouette']:.3f}")
    
    # Anomaly Detection
    print("\n📊 Anomaly Detection Models")
    print("-" * 40)
    anomaly = AnomalyDetectionModels(contamination=0.05)
    anomaly_results = anomaly.train_all(X)
    
    for name, result in anomaly_results.items():
        print(f"{name}: {result['anomaly_count']} anomalies ({result['anomaly_ratio']*100:.1f}%)")
