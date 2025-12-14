# Data Science Module for DAO Platform

"""
Sprint 3 - Data Science Layer Implementation

Components:
- kpi_framework: KPI definitions and computation
- feature_engineering: Sklearn-compatible transformers
- models: Classification, Clustering, Anomaly Detection, Time-Series
- experimentation: A/B Testing, Multi-Armed Bandit
- visualizations: Dashboard and metric charts
- inference_logging: Model versioning and inference tracking
- pipeline: Main ETL → Feature → Inference pipeline
"""

from .kpi_framework import KPIComputer, generate_kpi_dashboard_data, KPI_REGISTRY
from .feature_engineering import create_feature_pipeline, extract_features
from .models import ClassificationModels, ClusteringModels, AnomalyDetectionModels
from .experimentation import ABTest, MultiArmedBandit
from .inference_logging import InferenceLogger, ModelVersionManager, TrackedModel

__version__ = "1.0.0"
__all__ = [
    "KPIComputer",
    "generate_kpi_dashboard_data", 
    "KPI_REGISTRY",
    "create_feature_pipeline",
    "extract_features",
    "ClassificationModels",
    "ClusteringModels", 
    "AnomalyDetectionModels",
    "ABTest",
    "MultiArmedBandit",
    "InferenceLogger",
    "ModelVersionManager",
    "TrackedModel",
]
