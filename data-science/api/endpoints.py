"""
FastAPI Endpoints for Data Science Models
Exposes model predictions and experimentation APIs.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ds_logging.model_logger import ModelLogger

# ============================================================
# PYDANTIC MODELS
# ============================================================

class WalletRiskRequest(BaseModel):
    wallet_address: str
    transactions: Optional[List[Dict[str, Any]]] = None
    sybil_score: Optional[float] = 0.5


class WalletRiskResponse(BaseModel):
    wallet_address: str
    risk_score: float
    is_risky: bool
    threshold: float
    request_id: str


class RecommendationRequest(BaseModel):
    donor_id: str
    n_recommendations: int = 5
    exclude_funded: bool = True


class RecommendationResponse(BaseModel):
    donor_id: str
    recommendations: List[Dict[str, Any]]
    method: str
    request_id: str


class DonorSegmentRequest(BaseModel):
    donor_id: str
    donations: Optional[List[Dict[str, Any]]] = None


class DonorSegmentResponse(BaseModel):
    donor_id: str
    cluster_id: int
    segment_name: str
    request_id: str


class VariantRequest(BaseModel):
    experiment_name: str
    user_id: str


class VariantResponse(BaseModel):
    experiment_name: str
    user_id: str
    variant: str
    request_id: str


class ConversionRequest(BaseModel):
    experiment_name: str
    user_id: str
    variant: str
    value: float = 1.0


class KPIResponse(BaseModel):
    kpis: Dict[str, Dict[str, Any]]
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    models: Dict[str, str]


# ============================================================
# FASTAPI APP
# ============================================================

def create_api_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="DonCoin DAO Data Science API",
        description="API for ML model predictions, experimentation, and KPIs",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize logger
    logger = ModelLogger(log_dir='logs/')
    
    # Models (lazy loading)
    models = {
        'risk_scorer': None,
        'recommender': None,
        'clustering': None,
        'outlier_detector': None
    }
    
    def get_model(name: str):
        """Lazy load model"""
        if models[name] is None:
            # In production, load from saved models
            # For demo, return None (predictions will be simulated)
            pass
        return models[name]
    
    # ============================================================
    # HEALTH CHECK
    # ============================================================
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Check API and model health"""
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            models={
                'risk_scorer': 'ready' if models['risk_scorer'] else 'not_loaded',
                'recommender': 'ready' if models['recommender'] else 'not_loaded',
                'clustering': 'ready' if models['clustering'] else 'not_loaded',
                'outlier_detector': 'ready' if models['outlier_detector'] else 'not_loaded'
            }
        )
    
    # ============================================================
    # RISK SCORING
    # ============================================================
    
    @app.post("/api/v1/risk/score", response_model=WalletRiskResponse)
    async def get_risk_score(request: WalletRiskRequest):
        """
        Get risk score for a wallet.
        
        Returns a score from 0.0 (low risk) to 1.0 (high risk).
        """
        start_time = time.time()
        
        # Simulate prediction (replace with actual model)
        import numpy as np
        np.random.seed(hash(request.wallet_address) % 2**32)
        
        # Risk score based on features
        base_risk = request.sybil_score * 0.5
        if request.transactions:
            tx_count = len(request.transactions)
            if tx_count > 50:
                base_risk += 0.2
            total_amount = sum(tx.get('amount', 0) for tx in request.transactions)
            if total_amount < 10:
                base_risk += 0.1
        
        risk_score = min(1.0, max(0.0, base_risk + np.random.uniform(-0.1, 0.1)))
        threshold = 0.7
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Log prediction
        request_id = logger.log_prediction(
            model_name='risk_scorer',
            model_version='1.0',
            input_features={'wallet_address': request.wallet_address, 'sybil_score': request.sybil_score},
            output=risk_score,
            latency_ms=latency_ms
        )
        
        return WalletRiskResponse(
            wallet_address=request.wallet_address,
            risk_score=round(risk_score, 4),
            is_risky=risk_score >= threshold,
            threshold=threshold,
            request_id=request_id
        )
    
    # ============================================================
    # RECOMMENDATIONS
    # ============================================================
    
    @app.post("/api/v1/recommend", response_model=RecommendationResponse)
    async def get_recommendations(request: RecommendationRequest):
        """
        Get proposal recommendations for a donor.
        
        Returns top N proposals the donor might be interested in.
        """
        start_time = time.time()
        
        # Simulate recommendations (replace with actual model)
        import numpy as np
        np.random.seed(hash(request.donor_id) % 2**32)
        
        recommendations = [
            {
                'proposal_id': f'proposal_{i}',
                'score': float(np.random.uniform(0.3, 0.9)),
                'reason': 'Similar to past donations'
            }
            for i in np.random.choice(range(1, 50), size=min(request.n_recommendations, 5), replace=False)
        ]
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Log prediction
        request_id = logger.log_prediction(
            model_name='recommender',
            model_version='1.0',
            input_features={'donor_id': request.donor_id, 'n': request.n_recommendations},
            output=len(recommendations),
            latency_ms=latency_ms
        )
        
        return RecommendationResponse(
            donor_id=request.donor_id,
            recommendations=recommendations,
            method='hybrid',
            request_id=request_id
        )
    
    # ============================================================
    # DONOR SEGMENTATION
    # ============================================================
    
    @app.post("/api/v1/segment", response_model=DonorSegmentResponse)
    async def get_donor_segment(request: DonorSegmentRequest):
        """
        Get the cluster/segment for a donor.
        
        Returns segment name and characteristics.
        """
        start_time = time.time()
        
        # Simulate clustering (replace with actual model)
        import numpy as np
        np.random.seed(hash(request.donor_id) % 2**32)
        
        segments = [
            (0, 'High-Value Champions'),
            (1, 'Regular Supporters'),
            (2, 'One-Time Donors'),
            (3, 'At-Risk / Churned')
        ]
        
        # Determine segment based on donation patterns
        if request.donations:
            total = sum(d.get('amount', 0) for d in request.donations)
            count = len(request.donations)
            
            if total > 1000 and count > 5:
                cluster_id, segment_name = segments[0]
            elif count > 3:
                cluster_id, segment_name = segments[1]
            elif count == 1:
                cluster_id, segment_name = segments[2]
            else:
                cluster_id, segment_name = segments[3]
        else:
            cluster_id, segment_name = segments[np.random.randint(0, 4)]
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Log prediction
        request_id = logger.log_prediction(
            model_name='clustering',
            model_version='1.0',
            input_features={'donor_id': request.donor_id},
            output=cluster_id,
            latency_ms=latency_ms
        )
        
        return DonorSegmentResponse(
            donor_id=request.donor_id,
            cluster_id=cluster_id,
            segment_name=segment_name,
            request_id=request_id
        )
    
    # ============================================================
    # EXPERIMENTATION
    # ============================================================
    
    @app.post("/api/v1/experiment/variant", response_model=VariantResponse)
    async def get_experiment_variant(request: VariantRequest):
        """
        Get the variant assignment for a user in an experiment.
        
        Uses deterministic hashing for consistent assignment.
        """
        import hashlib
        
        # Deterministic assignment
        hash_input = f"{request.user_id}:{request.experiment_name}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        variant = 'treatment' if (hash_value % 100) < 50 else 'control'
        
        # Log impression
        request_id = logger.log_experiment_impression(
            experiment_name=request.experiment_name,
            experiment_type='ab_test',
            user_id=request.user_id,
            variant=variant
        )
        
        return VariantResponse(
            experiment_name=request.experiment_name,
            user_id=request.user_id,
            variant=variant,
            request_id=request_id
        )
    
    @app.post("/api/v1/experiment/convert")
    async def record_conversion(request: ConversionRequest):
        """Record a conversion event for an experiment"""
        request_id = logger.log_experiment_conversion(
            experiment_name=request.experiment_name,
            experiment_type='ab_test',
            user_id=request.user_id,
            variant=request.variant,
            value=request.value
        )
        
        return {"status": "recorded", "request_id": request_id}
    
    # ============================================================
    # KPIs
    # ============================================================
    
    @app.get("/api/v1/kpis", response_model=KPIResponse)
    async def get_kpis():
        """Get current KPI values"""
        # Simulated KPI data (replace with actual database queries)
        kpis = {
            'funding_success_rate': {'value': 62.5, 'unit': '%', 'target': 60},
            'conversion_rate': {'value': 12.8, 'unit': '%', 'target': 15},
            'time_to_finality_days': {'value': 18.3, 'unit': 'days', 'target': 14},
            'average_donation_size': {'value': 156.42, 'unit': '$', 'target': 100},
            'event_processing_lag': {'value': 2.3, 'unit': 'seconds', 'target': 5},
            'api_response_latency_p95': {'value': 145, 'unit': 'ms', 'target': 200},
            'error_rate': {'value': 0.05, 'unit': '%', 'target': 0.1},
            'suspicious_transaction_count': {'value': 3, 'unit': 'count', 'target': 10},
        }
        
        return KPIResponse(
            kpis=kpis,
            timestamp=datetime.now().isoformat()
        )
    
    @app.get("/api/v1/kpis/{kpi_name}")
    async def get_kpi_detail(kpi_name: str, days: int = Query(30, ge=1, le=365)):
        """Get detailed KPI data with history"""
        import numpy as np
        
        # Simulated time series (replace with actual database query)
        dates = [(datetime.now() - timedelta(days=i)).isoformat()[:10] for i in range(days)]
        values = np.random.uniform(50, 70, days).tolist()
        
        return {
            'kpi_name': kpi_name,
            'current_value': values[0],
            'history': [
                {'date': d, 'value': v}
                for d, v in zip(dates, values)
            ],
            'trend': 'up' if values[0] > values[-1] else 'down'
        }
    
    # ============================================================
    # MODEL STATS
    # ============================================================
    
    @app.get("/api/v1/models/stats")
    async def get_model_stats():
        """Get model performance statistics"""
        return logger.get_model_stats()
    
    return app


# Create app instance
app = create_api_app()


if __name__ == "__main__":
    import uvicorn
    print("Starting DonCoin DAO Data Science API...")
    print("Open http://localhost:8051/docs for Swagger UI")
    uvicorn.run(app, host="0.0.0.0", port=8051)
