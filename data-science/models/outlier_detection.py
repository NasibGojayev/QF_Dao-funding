"""
Outlier Detection Model - Isolation Forest for Suspicious Transaction Detection
Real-time detection of anomalous transactions.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, Optional, List, Tuple
import pickle
import os
from datetime import datetime


class OutlierDetector:
    """
    Outlier Detection for suspicious transaction identification.
    
    Uses Isolation Forest for efficient anomaly detection.
    Designed for real-time transaction monitoring.
    """
    
    def __init__(self, 
                 contamination: float = 0.05,
                 method: str = 'isolation_forest',
                 random_state: int = 42):
        self.contamination = contamination
        self.method = method
        self.random_state = random_state
        
        self.model = None
        self.scaler = StandardScaler()
        
        self.feature_names = [
            'amount',
            'amount_zscore',
            'time_since_last_tx_hours',
            'hour_of_day',
            'day_of_week',
            'is_weekend',
            'is_night',  # 10pm-6am
            'tx_count_last_24h',
            'tx_count_last_7d',
            'amount_vs_avg_ratio',
            'unique_recipients_24h'
        ]
        
        self.is_fitted = False
        self.training_metrics = {}
        
        # Store historical stats for feature computation
        self.historical_stats = {
            'mean_amount': 0,
            'std_amount': 1,
            'median_amount': 0
        }
    
    def _create_model(self):
        """Create the anomaly detection model"""
        if self.method == 'isolation_forest':
            return IsolationForest(
                contamination=self.contamination,
                random_state=self.random_state,
                n_estimators=100,
                max_samples='auto',
                n_jobs=-1
            )
        elif self.method == 'one_class_svm':
            return OneClassSVM(nu=self.contamination, kernel='rbf', gamma='auto')
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def prepare_features(self, 
                         transactions: pd.DataFrame,
                         historical_transactions: Optional[pd.DataFrame] = None) -> np.ndarray:
        """
        Prepare features for each transaction.
        
        Expected columns in transactions:
        - amount: float
        - timestamp: datetime
        - sender_wallet: str (optional)
        - recipient_wallet/proposal_id: str (optional)
        """
        transactions = transactions.copy()
        transactions['timestamp'] = pd.to_datetime(transactions['timestamp'])
        transactions = transactions.sort_values('timestamp')
        
        features = []
        
        for idx, row in transactions.iterrows():
            amount = row['amount']
            timestamp = row['timestamp']
            
            # Amount features
            amount_zscore = (
                (amount - self.historical_stats['mean_amount']) / 
                (self.historical_stats['std_amount'] + 1e-6)
            )
            
            amount_vs_avg = amount / (self.historical_stats['mean_amount'] + 1e-6)
            
            # Time features
            hour_of_day = timestamp.hour
            day_of_week = timestamp.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            is_night = 1 if (hour_of_day >= 22 or hour_of_day <= 6) else 0
            
            # Transaction velocity (using historical if available)
            if historical_transactions is not None and len(historical_transactions) > 0:
                sender = row.get('sender_wallet', '')
                hist = historical_transactions[
                    (historical_transactions.get('sender_wallet', '') == sender) &
                    (historical_transactions['timestamp'] < timestamp)
                ]
                
                # Time since last transaction
                if len(hist) > 0:
                    last_tx_time = hist['timestamp'].max()
                    time_since_last = (timestamp - last_tx_time).total_seconds() / 3600
                else:
                    time_since_last = 168  # 1 week default
                
                # Transaction counts
                last_24h = hist[hist['timestamp'] >= timestamp - pd.Timedelta(hours=24)]
                last_7d = hist[hist['timestamp'] >= timestamp - pd.Timedelta(days=7)]
                
                tx_count_24h = len(last_24h)
                tx_count_7d = len(last_7d)
                
                # Unique recipients in last 24h
                recipient_col = 'proposal_id' if 'proposal_id' in last_24h.columns else 'recipient_wallet'
                if recipient_col in last_24h.columns:
                    unique_recipients_24h = last_24h[recipient_col].nunique()
                else:
                    unique_recipients_24h = 0
            else:
                time_since_last = 24  # Default
                tx_count_24h = 0
                tx_count_7d = 0
                unique_recipients_24h = 0
            
            feature_vector = [
                amount,
                amount_zscore,
                time_since_last,
                hour_of_day,
                day_of_week,
                is_weekend,
                is_night,
                tx_count_24h,
                tx_count_7d,
                amount_vs_avg,
                unique_recipients_24h
            ]
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def fit(self, transactions: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the outlier detection model on historical transactions.
        
        Args:
            transactions: DataFrame with transaction data
        
        Returns:
            Dictionary of training metrics
        """
        # Calculate historical statistics
        self.historical_stats = {
            'mean_amount': transactions['amount'].mean(),
            'std_amount': transactions['amount'].std(),
            'median_amount': transactions['amount'].median()
        }
        
        # Prepare features
        X = self.prepare_features(transactions, transactions)
        X_scaled = self.scaler.fit_transform(X)
        
        # Create and fit model
        self.model = self._create_model()
        predictions = self.model.fit_predict(X_scaled)
        
        # Predictions: 1 = normal, -1 = outlier
        n_outliers = np.sum(predictions == -1)
        outlier_rate = n_outliers / len(predictions)
        
        # Get anomaly scores
        if self.method == 'isolation_forest':
            scores = self.model.score_samples(X_scaled)
            # Lower scores = more anomalous
            threshold = np.percentile(scores, self.contamination * 100)
        else:
            scores = self.model.decision_function(X_scaled)
            threshold = 0
        
        self.training_metrics = {
            'n_transactions': len(transactions),
            'n_outliers_detected': int(n_outliers),
            'outlier_rate': float(outlier_rate),
            'contamination_setting': self.contamination,
            'score_threshold': float(threshold),
            'method': self.method,
            'trained_at': datetime.now().isoformat()
        }
        
        self.is_fitted = True
        return self.training_metrics
    
    def predict(self, 
                transactions: pd.DataFrame,
                historical_transactions: Optional[pd.DataFrame] = None) -> np.ndarray:
        """
        Detect outliers in new transactions.
        
        Returns:
            Array of predictions (1 = normal, -1 = outlier)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = self.prepare_features(transactions, historical_transactions)
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict(X_scaled)
    
    def get_anomaly_scores(self,
                           transactions: pd.DataFrame,
                           historical_transactions: Optional[pd.DataFrame] = None) -> np.ndarray:
        """
        Get anomaly scores for transactions.
        Lower scores = more anomalous.
        
        Returns:
            Array of anomaly scores
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        X = self.prepare_features(transactions, historical_transactions)
        X_scaled = self.scaler.transform(X)
        
        if self.method == 'isolation_forest':
            return self.model.score_samples(X_scaled)
        else:
            return self.model.decision_function(X_scaled)
    
    def detect_anomalies(self,
                         transactions: pd.DataFrame,
                         historical_transactions: Optional[pd.DataFrame] = None,
                         return_scores: bool = True) -> List[Dict[str, Any]]:
        """
        Detect anomalies and return detailed results.
        
        Returns:
            List of dicts with transaction info and anomaly flags
        """
        predictions = self.predict(transactions, historical_transactions)
        scores = self.get_anomaly_scores(transactions, historical_transactions)
        
        results = []
        for i, (_, row) in enumerate(transactions.iterrows()):
            is_anomaly = predictions[i] == -1
            
            result = {
                'index': i,
                'is_anomaly': bool(is_anomaly),
                'anomaly_score': float(scores[i]),
                'amount': float(row['amount']),
                'timestamp': str(row['timestamp'])
            }
            
            if 'sender_wallet' in row:
                result['sender_wallet'] = row['sender_wallet']
            
            results.append(result)
        
        return results
    
    def get_feature_importance(self, transactions: pd.DataFrame) -> Dict[str, float]:
        """
        Approximate feature importance using permutation.
        Only available for isolation forest.
        """
        if not self.is_fitted or self.method != 'isolation_forest':
            return {}
        
        X = self.prepare_features(transactions, transactions)
        X_scaled = self.scaler.transform(X)
        
        base_scores = self.model.score_samples(X_scaled)
        base_outlier_rate = np.mean(base_scores < np.percentile(base_scores, self.contamination * 100))
        
        importances = {}
        for i, name in enumerate(self.feature_names):
            # Permute feature
            X_permuted = X_scaled.copy()
            np.random.shuffle(X_permuted[:, i])
            
            permuted_scores = self.model.score_samples(X_permuted)
            permuted_outlier_rate = np.mean(
                permuted_scores < np.percentile(permuted_scores, self.contamination * 100)
            )
            
            # Importance = change in outlier rate
            importances[name] = abs(permuted_outlier_rate - base_outlier_rate)
        
        # Normalize
        total = sum(importances.values())
        if total > 0:
            importances = {k: v / total for k, v in importances.items()}
        
        return importances
    
    def save(self, path: str):
        """Save model to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'contamination': self.contamination,
                'method': self.method,
                'feature_names': self.feature_names,
                'historical_stats': self.historical_stats,
                'training_metrics': self.training_metrics
            }, f)
    
    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.contamination = data['contamination']
            self.method = data['method']
            self.feature_names = data['feature_names']
            self.historical_stats = data['historical_stats']
            self.training_metrics = data['training_metrics']
            self.is_fitted = True


def generate_synthetic_transactions(n_normal: int = 1000, n_anomalous: int = 50) -> pd.DataFrame:
    """Generate synthetic transaction data with known anomalies"""
    np.random.seed(42)
    
    transactions = []
    base_time = datetime.now()
    
    # Normal transactions
    for i in range(n_normal):
        amount = np.random.lognormal(5, 1)  # Log-normal distribution
        hour = np.random.choice(range(8, 22))  # Business hours mostly
        day_offset = np.random.randint(0, 90)
        
        transactions.append({
            'amount': amount,
            'timestamp': base_time - pd.Timedelta(days=day_offset, hours=24-hour),
            'sender_wallet': f'0x{np.random.randint(0, 100):040x}',
            'proposal_id': f'proposal_{np.random.randint(1, 20)}',
            'is_anomaly': False
        })
    
    # Anomalous transactions
    for i in range(n_anomalous):
        anomaly_type = np.random.choice(['high_amount', 'rapid_fire', 'odd_timing'])
        
        if anomaly_type == 'high_amount':
            amount = np.random.lognormal(8, 0.5)  # Much higher
            hour = np.random.randint(0, 24)
        elif anomaly_type == 'rapid_fire':
            amount = np.random.lognormal(3, 0.5)  # Small but many
            hour = np.random.randint(0, 24)
        else:  # odd_timing
            amount = np.random.lognormal(5, 1)
            hour = np.random.choice([2, 3, 4, 5])  # Late night
        
        day_offset = np.random.randint(0, 90)
        
        transactions.append({
            'amount': amount,
            'timestamp': base_time - pd.Timedelta(days=day_offset, hours=24-hour),
            'sender_wallet': f'0x{np.random.randint(0, 10):040x}',  # Fewer unique wallets
            'proposal_id': f'proposal_{np.random.randint(1, 5)}',
            'is_anomaly': True
        })
    
    return pd.DataFrame(transactions)


if __name__ == "__main__":
    print("Generating synthetic transaction data...")
    transactions = generate_synthetic_transactions(1000, 50)
    
    # Remove labels for training (unsupervised)
    labels = transactions['is_anomaly'].values
    train_data = transactions.drop('is_anomaly', axis=1)
    
    print(f"Generated {len(transactions)} transactions ({sum(labels)} actual anomalies)")
    
    print("\nTraining Outlier Detector...")
    detector = OutlierDetector(contamination=0.05)
    metrics = detector.fit(train_data)
    
    print(f"\nTraining Results:")
    print(f"  Method: {metrics['method']}")
    print(f"  Outliers Detected: {metrics['n_outliers_detected']}")
    print(f"  Detection Rate: {metrics['outlier_rate']:.2%}")
    
    # Evaluate detection accuracy
    predictions = detector.predict(train_data, train_data)
    detected_outliers = predictions == -1
    
    # True positives: actual anomalies that were detected
    tp = np.sum(detected_outliers & labels)
    # False positives: normal transactions flagged as anomalies
    fp = np.sum(detected_outliers & ~labels)
    # False negatives: actual anomalies that were missed
    fn = np.sum(~detected_outliers & labels)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    print(f"\nDetection Performance (on synthetic data with known labels):")
    print(f"  Precision: {precision:.2%}")
    print(f"  Recall: {recall:.2%}")
    print(f"  True Positives: {tp}")
    print(f"  False Positives: {fp}")
    print(f"  False Negatives: {fn}")
    
    # Save model
    detector.save('models/saved/outlier_detector.pkl')
    print("\nModel saved to models/saved/outlier_detector.pkl")
