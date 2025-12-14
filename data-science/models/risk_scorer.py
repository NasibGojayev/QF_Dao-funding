"""
Risk Scorer Model - Classical ML for Fraud/Sybil Detection
Uses Random Forest to score wallets and transactions for risk.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve
from typing import Dict, Any, Optional, List, Tuple
import pickle
import os
from datetime import datetime
import json


class RiskScorer:
    """
    Risk Scoring Model for detecting suspicious wallets/transactions.
    
    Features used:
    - Transaction frequency
    - Average transaction amount
    - Time since first transaction
    - Number of unique proposals donated to
    - Existing sybil score (if available)
    - Wallet balance volatility
    - Transaction timing patterns
    """
    
    def __init__(self, model_type: str = 'random_forest', threshold: float = 0.7):
        self.model_type = model_type
        self.threshold = threshold
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'tx_count',
            'avg_tx_amount',
            'days_since_first_tx',
            'unique_proposals',
            'sybil_score',
            'balance_volatility',
            'tx_frequency_per_day',
            'avg_time_between_tx_hours',
            'max_tx_amount',
            'min_tx_amount',
            'tx_amount_std',
            'weekend_tx_ratio',
            'night_tx_ratio'
        ]
        self.is_fitted = False
        self.training_metrics = {}
    
    def _create_model(self):
        """Create the underlying ML model"""
        if self.model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            return GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def prepare_features(self, wallet_data: pd.DataFrame) -> np.ndarray:
        """
        Prepare features from raw wallet data.
        
        Expected columns in wallet_data:
        - wallet_address: str
        - transactions: list of transaction dicts
        - sybil_score: float (optional)
        - balance_history: list of balance snapshots
        """
        features = []
        
        for _, row in wallet_data.iterrows():
            transactions = row.get('transactions', [])
            
            if not transactions:
                # No transactions - assign neutral features
                features.append([0] * len(self.feature_names))
                continue
            
            tx_df = pd.DataFrame(transactions)
            if 'timestamp' in tx_df.columns:
                tx_df['timestamp'] = pd.to_datetime(tx_df['timestamp'])
                tx_df = tx_df.sort_values('timestamp')
            
            # Calculate features
            tx_count = len(transactions)
            amounts = tx_df['amount'].values if 'amount' in tx_df.columns else [0]
            avg_tx_amount = np.mean(amounts)
            max_tx_amount = np.max(amounts)
            min_tx_amount = np.min(amounts)
            tx_amount_std = np.std(amounts) if len(amounts) > 1 else 0
            
            # Time-based features
            if 'timestamp' in tx_df.columns and len(tx_df) > 0:
                first_tx = tx_df['timestamp'].min()
                last_tx = tx_df['timestamp'].max()
                days_active = (last_tx - first_tx).days + 1
                days_since_first_tx = (datetime.now() - first_tx.to_pydatetime().replace(tzinfo=None)).days
                tx_frequency_per_day = tx_count / max(days_active, 1)
                
                # Time between transactions
                if len(tx_df) > 1:
                    time_diffs = tx_df['timestamp'].diff().dropna()
                    avg_time_between_tx_hours = time_diffs.mean().total_seconds() / 3600
                else:
                    avg_time_between_tx_hours = 0
                
                # Weekend/night patterns
                tx_df['hour'] = tx_df['timestamp'].dt.hour
                tx_df['dayofweek'] = tx_df['timestamp'].dt.dayofweek
                weekend_tx_ratio = (tx_df['dayofweek'] >= 5).mean()
                night_tx_ratio = ((tx_df['hour'] >= 22) | (tx_df['hour'] <= 6)).mean()
            else:
                days_since_first_tx = 0
                tx_frequency_per_day = 0
                avg_time_between_tx_hours = 0
                weekend_tx_ratio = 0.3
                night_tx_ratio = 0.2
            
            # Unique proposals
            unique_proposals = tx_df['proposal_id'].nunique() if 'proposal_id' in tx_df.columns else 0
            
            # Sybil score
            sybil_score = row.get('sybil_score', 0.5)
            
            # Balance volatility
            balance_history = row.get('balance_history', [])
            if len(balance_history) > 1:
                balance_volatility = np.std(balance_history) / (np.mean(balance_history) + 1e-6)
            else:
                balance_volatility = 0
            
            feature_vector = [
                tx_count,
                avg_tx_amount,
                days_since_first_tx,
                unique_proposals,
                sybil_score,
                balance_volatility,
                tx_frequency_per_day,
                avg_time_between_tx_hours,
                max_tx_amount,
                min_tx_amount,
                tx_amount_std,
                weekend_tx_ratio,
                night_tx_ratio
            ]
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def fit(self, wallet_data: pd.DataFrame, labels: np.ndarray) -> Dict[str, Any]:
        """
        Train the risk scoring model.
        
        Args:
            wallet_data: DataFrame with wallet/transaction data
            labels: Binary labels (1 = risky/fraudulent, 0 = legitimate)
        
        Returns:
            Dictionary of training metrics
        """
        X = self.prepare_features(wallet_data)
        X_scaled = self.scaler.fit_transform(X)
        
        # Split for validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Create and train model
        self.model = self._create_model()
        self.model.fit(X_train, y_train)
        
        # Calculate metrics
        y_pred = self.model.predict(X_val)
        y_proba = self.model.predict_proba(X_val)[:, 1]
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_scaled, labels, cv=5, scoring='roc_auc')
        
        self.training_metrics = {
            'roc_auc': roc_auc_score(y_val, y_proba),
            'cv_roc_auc_mean': cv_scores.mean(),
            'cv_roc_auc_std': cv_scores.std(),
            'classification_report': classification_report(y_val, y_pred, output_dict=True),
            'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_)),
            'training_samples': len(labels),
            'positive_rate': labels.mean(),
            'trained_at': datetime.now().isoformat()
        }
        
        self.is_fitted = True
        return self.training_metrics
    
    def predict_risk_score(self, wallet_data: pd.DataFrame) -> np.ndarray:
        """
        Predict risk scores for wallets.
        
        Args:
            wallet_data: DataFrame with wallet/transaction data
        
        Returns:
            Array of risk scores (0.0 to 1.0)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = self.prepare_features(wallet_data)
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict_proba(X_scaled)[:, 1]
    
    def is_risky(self, wallet_data: pd.DataFrame) -> np.ndarray:
        """
        Determine if wallets are risky based on threshold.
        
        Returns:
            Boolean array
        """
        scores = self.predict_risk_score(wallet_data)
        return scores >= self.threshold
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance rankings"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        return dict(zip(self.feature_names, self.model.feature_importances_))
    
    def save(self, path: str):
        """Save model to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'threshold': self.threshold,
                'feature_names': self.feature_names,
                'training_metrics': self.training_metrics,
                'model_type': self.model_type
            }, f)
    
    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.threshold = data['threshold']
            self.feature_names = data['feature_names']
            self.training_metrics = data['training_metrics']
            self.model_type = data['model_type']
            self.is_fitted = True


def generate_synthetic_training_data(n_samples: int = 1000) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Generate synthetic training data for demonstration.
    In production, this would come from labeled historical data.
    """
    np.random.seed(42)
    
    # Generate wallet data
    data = []
    labels = []
    
    for i in range(n_samples):
        # 10% are risky wallets
        is_risky = np.random.random() < 0.1
        
        if is_risky:
            # Risky wallet patterns
            tx_count = np.random.randint(50, 500)
            avg_amount = np.random.uniform(0.1, 10)  # Small amounts
            sybil_score = np.random.uniform(0.6, 1.0)  # High sybil score
            unique_proposals = np.random.randint(1, 3)  # Few proposals
        else:
            # Normal wallet patterns
            tx_count = np.random.randint(1, 50)
            avg_amount = np.random.uniform(10, 1000)
            sybil_score = np.random.uniform(0.0, 0.4)
            unique_proposals = np.random.randint(1, 20)
        
        # Generate transactions
        transactions = []
        base_time = datetime.now()
        for j in range(tx_count):
            transactions.append({
                'amount': avg_amount * np.random.uniform(0.5, 1.5),
                'timestamp': base_time - pd.Timedelta(hours=j * np.random.uniform(0.5, 24)),
                'proposal_id': np.random.randint(1, unique_proposals + 1)
            })
        
        data.append({
            'wallet_address': f'0x{i:040x}',
            'transactions': transactions,
            'sybil_score': sybil_score,
            'balance_history': [np.random.uniform(100, 10000) for _ in range(10)]
        })
        labels.append(1 if is_risky else 0)
    
    return pd.DataFrame(data), np.array(labels)


if __name__ == "__main__":
    # Demo training
    print("Generating synthetic training data...")
    wallet_data, labels = generate_synthetic_training_data(1000)
    
    print("Training Risk Scorer...")
    scorer = RiskScorer(threshold=0.7)
    metrics = scorer.fit(wallet_data, labels)
    
    print(f"\nTraining Results:")
    print(f"  ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"  CV ROC-AUC: {metrics['cv_roc_auc_mean']:.4f} (+/- {metrics['cv_roc_auc_std']:.4f})")
    print(f"\nTop Feature Importances:")
    importance = sorted(metrics['feature_importance'].items(), key=lambda x: x[1], reverse=True)
    for name, imp in importance[:5]:
        print(f"  {name}: {imp:.4f}")
    
    # Save model
    scorer.save('models/saved/risk_scorer.pkl')
    print("\nModel saved to models/saved/risk_scorer.pkl")
