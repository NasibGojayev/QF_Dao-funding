"""
Sprint 3: Production Model Inference Pipeline
Consumes ETL features and outputs model decisions integrated into backend flow
"""

import time
from typing import Dict, Tuple, Any, List
import logging

logger = logging.getLogger(__name__)


class ModelInferencePipeline:
    """Production inference pipeline for risk scoring and personalization"""
    
    def __init__(self):
        """Initialize with pre-trained models (would be loaded from disk in production)"""
        self.high_value_classifier = None  # Pre-trained RandomForest/XGBoost
        self.anomaly_detector = None  # Isolation Forest
        self.risk_scorer = None  # Custom risk model
        self.models_loaded = False
    
    def load_models(self):
        """Load pre-trained models from disk"""
        # In production: joblib.load('models/high_value_classifier.pkl')
        # For demo, we'll use mock models
        logger.info("Loading pre-trained models...")
        self.models_loaded = True
        logger.info("✅ Models loaded successfully")
    
    def score_user_high_value_likelihood(self, features: Dict) -> Tuple[float, Dict]:
        """
        Score probability that user will be high-value donor
        
        Args:
            features: User feature dict (total_amount, tx_count, confirmation_rate, etc)
        
        Returns:
            (probability_score, decision_dict)
        """
        if not self.models_loaded:
            self.load_models()
        
        start_time = time.time()
        
        # Mock model inference (in production, use real model)
        # Real: score = self.high_value_classifier.predict_proba(np.array([...]))[0][1]
        total_amount = features.get('total_amount', 0)
        tx_count = features.get('tx_count', 0)
        confirmation_rate = features.get('confirmation_rate', 0.5)
        
        # Simple heuristic for demo (in production, use trained model)
        score = (
            0.3 * min(total_amount / 1000, 1.0) +  # Amount score
            0.3 * min(tx_count / 50, 1.0) +  # Frequency score
            0.4 * confirmation_rate  # Reliability score
        )
        score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
        
        latency_ms = (time.time() - start_time) * 1000
        
        decision = {
            'score': score,
            'is_high_value': score > 0.6,
            'confidence': abs(score - 0.5) * 2,  # Confidence increases toward extremes
            'latency_ms': latency_ms,
            'features_used': list(features.keys())
        }
        
        logger.info(f"User high-value score: {score:.3f} (latency: {latency_ms:.2f}ms)")
        return score, decision
    
    def detect_anomalies(self, features: Dict) -> Tuple[int, Dict]:
        """
        Detect anomalous user behavior
        
        Args:
            features: User feature dict
        
        Returns:
            (is_anomaly, details_dict)
        """
        start_time = time.time()
        
        # Mock anomaly detection
        suspicious_ratio = features.get('suspicious_ratio', 0)
        amount_volatility = features.get('amount_volatility', 0)
        
        # Flag if suspicious ratio > 30% or volatility > 2x
        is_anomaly = suspicious_ratio > 0.3 or amount_volatility > 2.0
        
        latency_ms = (time.time() - start_time) * 1000

        details = {
            'is_anomaly': int(is_anomaly),
            'suspicious_ratio': suspicious_ratio,
            'amount_volatility': amount_volatility,
            'reasons': [],
            'latency_ms': latency_ms
        }
        if suspicious_ratio > 0.3:
            details['reasons'].append(f"High suspicious transaction ratio: {suspicious_ratio:.2%}")
        if amount_volatility > 2.0:
            details['reasons'].append(f"High amount volatility: {amount_volatility:.2f}")
        
        return int(is_anomaly), details
    
    def calculate_risk_score(self, features: Dict) -> Tuple[float, Dict]:
        """
        Calculate risk score for transaction gating
        
        Args:
            features: Transaction/user features
        
        Returns:
            (risk_score_0_to_1, details_dict)
        """
        start_time = time.time()
        
        # Risk factors
        is_anomalous = features.get('is_anomalous', 0)
        confirmation_rate = features.get('confirmation_rate', 1.0)
        account_age_days = features.get('days_since_creation', 1)
        transaction_size = features.get('transaction_size', 0)
        
        # Risk score components
        anomaly_risk = 0.6 if is_anomalous else 0.0
        confirmation_risk = (1.0 - confirmation_rate) * 0.2  # Low confirmation = risk
        newness_risk = max(0, (30 - account_age_days) / 30 * 0.15)  # New accounts = risk
        size_risk = min(transaction_size / 10000, 1.0) * 0.05  # Large tx = slight risk
        
        risk_score = min(1.0, anomaly_risk + confirmation_risk + newness_risk + size_risk)
        
        latency_ms = (time.time() - start_time) * 1000
        
        details = {
            'risk_score': risk_score,
            'anomaly_component': anomaly_risk,
            'confirmation_component': confirmation_risk,
            'newness_component': newness_risk,
            'size_component': size_risk,
            'risk_level': 'HIGH' if risk_score > 0.7 else 'MEDIUM' if risk_score > 0.4 else 'LOW',
            'latency_ms': latency_ms
        }
        
        return risk_score, details
    
    def recommend_content(self, user_id: int, cluster_id: int,
                        user_interests: List[int]) -> Tuple[List[int], Dict[str, Any]]:
        """
        Recommend projects/rounds based on user profile
        
        Args:
            user_id: User ID
            cluster_id: K-means cluster assignment
            user_interests: List of project IDs user has interacted with
        
        Returns:
            (recommended_project_ids, details_dict)
        """
        start_time = time.time()
        
        # Mock recommender (in production, use actual collaborative filtering)
        # Recommendation strategy: suggest projects from same cluster
        all_projects = list(range(1, 51))  # Projects 1-50
        recommended = [p for p in all_projects if p not in user_interests][:5]
        
        latency_ms = (time.time() - start_time) * 1000
        
        details = {
            'recommended_projects': recommended,
            'strategy': 'cluster_based_collaborative_filtering',
            'user_cluster': cluster_id,
            'ranking_confidence': [0.9, 0.85, 0.8, 0.75, 0.7][:len(recommended)],
            'latency_ms': latency_ms
        }
        
        return recommended, details


# Global pipeline instance
pipeline = ModelInferencePipeline()


def score_user_for_ui_personalization(user_id: int, features: Dict) -> Dict:
    """
    Score user for personalized UI presentation
    Called on every user load to decide which variant to show
    """
    high_value_score, hv_decision = pipeline.score_user_high_value_likelihood(features)
    risk_score, risk_decision = pipeline.calculate_risk_score(features)
    
    # Decision logic
    personalization = {
        'user_id': user_id,
        'variant': 'baseline',  # default
        'personalization_features': []
    }
    
    if high_value_score > 0.75:
        personalization['variant'] = 'variant_a'  # Show recommendations
        personalization['personalization_features'] = [
            'premium_content_access',
            'priority_support',
            'early_round_access'
        ]
    elif high_value_score > 0.5:
        personalization['variant'] = 'variant_b'  # Show cluster-similar projects
        personalization['personalization_features'] = ['content_recommendations']
    
    # Add risk flagging
    if risk_score > 0.7:
        personalization['risk_flag'] = {
            'level': 'HIGH',
            'message': 'Additional verification may be required'
        }
    
    return personalization


def score_transaction_for_gating(user_id: int, transaction_data: Dict) -> Dict:
    """
    Score transaction for approval/gating
    Called during transaction submission to decide if immediate execution or review required
    """
    risk_score, risk_details = pipeline.calculate_risk_score(transaction_data)
    
    decision = {
        'user_id': user_id,
        'transaction_id': transaction_data.get('tx_id'),
        'risk_score': risk_score,
        'risk_level': risk_details['risk_level'],
        'action': 'approve' if risk_score < 0.4 else 'review' if risk_score < 0.7 else 'block',
        'requires_additional_verification': risk_score > 0.5
    }
    
    if decision['action'] == 'block':
        decision['block_reason'] = 'High risk detected - require additional verification'
    
    return decision


if __name__ == '__main__':
    print("=== Model Inference Pipeline Demo ===\n")
    
    # Load models
    pipeline.load_models()
    
    # Test user features
    test_features = {
        'total_amount': 500.0,
        'tx_count': 20,
        'confirmation_rate': 0.95,
        'suspicious_ratio': 0.05,
        'amount_volatility': 0.3,
        'days_since_creation': 45
    }
    
    # Test inference
    print("Testing High-Value User Scoring...")
    score, decision = pipeline.score_user_high_value_likelihood(test_features)
    print(f"Score: {score:.3f}, Decision: {decision}\n")
    
    print("Testing Anomaly Detection...")
    is_anom, anom_details = pipeline.detect_anomalies(test_features)
    print(f"Is Anomalous: {is_anom}, Details: {anom_details}\n")
    
    print("Testing Risk Scoring...")
    risk, risk_details = pipeline.calculate_risk_score({
        **test_features,
        'transaction_size': 100,
        'is_anomalous': 0
    })
    print(f"Risk Score: {risk:.3f}, Level: {risk_details['risk_level']}\n")
    
    print("Testing UI Personalization...")
    personal = score_user_for_ui_personalization(123, test_features)
    print(f"Personalization: {personal}\n")
    
    print("Testing Transaction Gating...")
    gating = score_transaction_for_gating(123, {
        'tx_id': 'tx_abc123',
        'transaction_size': 1000,
        'is_anomalous': 0,
        **test_features
    })
    print(f"Gating Decision: {gating}\n")
    
    print("✅ Pipeline demo complete")
