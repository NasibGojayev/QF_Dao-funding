"""
Feature Engineering Pipeline for DAO Platform
==============================================
Scikit-learn compatible feature extraction and transformation.
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from typing import List, Optional, Dict
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# CUSTOM TRANSFORMERS
# =============================================================================

class TimeWindowAggregator(BaseEstimator, TransformerMixin):
    """
    Creates time-windowed aggregate features.
    Windows: 5min, 1h, 24h, 7d
    """
    
    def __init__(self, windows: List[str] = None, agg_funcs: List[str] = None):
        self.windows = windows or ['5T', '1H', '24H', '7D']
        self.agg_funcs = agg_funcs or ['count', 'sum', 'mean', 'std']
        
    def fit(self, X, y=None):
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform with time-windowed aggregates."""
        if not isinstance(X, pd.DataFrame):
            return X
            
        features = X.copy()
        
        if 'created_at' in features.columns and 'user_id' in features.columns:
            features = features.sort_values('created_at')
            
            for window in self.windows:
                # Rolling aggregates per user
                window_name = window.replace('T', 'min').replace('H', 'h').replace('D', 'd')
                
                if 'amount' in features.columns:
                    features[f'amount_sum_{window_name}'] = (
                        features.groupby('user_id')['amount']
                        .transform(lambda x: x.rolling(window, on=features.loc[x.index, 'created_at']).sum())
                    )
                    features[f'tx_count_{window_name}'] = (
                        features.groupby('user_id')['amount']
                        .transform(lambda x: x.rolling(window, on=features.loc[x.index, 'created_at']).count())
                    )
        
        return features


class LagFeatureCreator(BaseEstimator, TransformerMixin):
    """Creates lag features for time-series analysis."""
    
    def __init__(self, columns: List[str] = None, lags: List[int] = None):
        self.columns = columns or ['amount']
        self.lags = lags or [1, 2, 3, 7]
        
    def fit(self, X, y=None):
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        features = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        
        for col in self.columns:
            if col in features.columns:
                for lag in self.lags:
                    features[f'{col}_lag_{lag}'] = features[col].shift(lag)
                    
        # Fill NaN with 0 for lag features
        lag_cols = [c for c in features.columns if '_lag_' in c]
        features[lag_cols] = features[lag_cols].fillna(0)
        
        return features


class FrequencyEncoder(BaseEstimator, TransformerMixin):
    """Encodes categorical variables by their frequency."""
    
    def __init__(self, columns: List[str] = None):
        self.columns = columns
        self.freq_maps: Dict[str, Dict] = {}
        
    def fit(self, X, y=None):
        df = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        cols = self.columns or df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        for col in cols:
            if col in df.columns:
                self.freq_maps[col] = df[col].value_counts(normalize=True).to_dict()
        return self
    
    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        
        for col, freq_map in self.freq_maps.items():
            if col in df.columns:
                df[f'{col}_freq'] = df[col].map(freq_map).fillna(0)
                
        return df


class UserBehaviorFeatures(BaseEstimator, TransformerMixin):
    """Extracts user behavior features from transaction history."""
    
    def __init__(self):
        self.user_stats: Dict = {}
        
    def fit(self, X, y=None):
        df = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        
        if 'user_id' in df.columns:
            self.user_stats = df.groupby('user_id').agg({
                'amount': ['count', 'sum', 'mean', 'std'],
                'created_at': ['min', 'max']
            }).to_dict()
        return self
    
    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        
        if 'user_id' in df.columns and 'amount' in df.columns:
            # Transaction count per user
            user_tx_count = df.groupby('user_id')['amount'].transform('count')
            df['user_tx_count'] = user_tx_count
            
            # User total donated
            user_total = df.groupby('user_id')['amount'].transform('sum')
            df['user_total_donated'] = user_total
            
            # User average donation
            user_avg = df.groupby('user_id')['amount'].transform('mean')
            df['user_avg_donation'] = user_avg
            
            # Days since first transaction
            if 'created_at' in df.columns:
                user_first = df.groupby('user_id')['created_at'].transform('min')
                df['user_account_age_days'] = (df['created_at'] - user_first).dt.days
                
        return df


class ProjectFeatures(BaseEstimator, TransformerMixin):
    """Extracts project-level features."""
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        
        if 'project_id' in df.columns and 'amount' in df.columns:
            # Project total raised
            project_total = df.groupby('project_id')['amount'].transform('sum')
            df['project_total_raised'] = project_total
            
            # Project donor count
            if 'user_id' in df.columns:
                donor_count = df.groupby('project_id')['user_id'].transform('nunique')
                df['project_donor_count'] = donor_count
                
            # Average donation to project
            project_avg = df.groupby('project_id')['amount'].transform('mean')
            df['project_avg_donation'] = project_avg
            
        return df


class AnomalyFeatures(BaseEstimator, TransformerMixin):
    """Creates features useful for anomaly detection."""
    
    def __init__(self):
        self.global_stats: Dict = {}
        
    def fit(self, X, y=None):
        df = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        
        if 'amount' in df.columns:
            self.global_stats = {
                'amount_mean': df['amount'].mean(),
                'amount_std': df['amount'].std(),
                'amount_p99': df['amount'].quantile(0.99),
            }
        return self
    
    def transform(self, X):
        df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        
        if 'amount' in df.columns and self.global_stats:
            # Z-score of amount
            mean = self.global_stats['amount_mean']
            std = self.global_stats['amount_std']
            df['amount_zscore'] = (df['amount'] - mean) / std if std > 0 else 0
            
            # Is amount above 99th percentile
            df['amount_is_extreme'] = (df['amount'] > self.global_stats['amount_p99']).astype(int)
            
            # Log-scaled amount
            df['amount_log'] = np.log1p(df['amount'])
            
        return df


# =============================================================================
# MAIN FEATURE PIPELINE
# =============================================================================

def create_feature_pipeline(
    include_time_windows: bool = True,
    include_lags: bool = True,
    include_user_features: bool = True,
    include_project_features: bool = True,
    include_anomaly_features: bool = True,
    scale_numeric: bool = True
) -> Pipeline:
    """
    Creates the full feature engineering pipeline.
    
    Returns sklearn Pipeline that can be fit and transformed.
    """
    transformers = []
    
    if include_user_features:
        transformers.append(('user_features', UserBehaviorFeatures()))
    
    if include_project_features:
        transformers.append(('project_features', ProjectFeatures()))
        
    if include_anomaly_features:
        transformers.append(('anomaly_features', AnomalyFeatures()))
        
    if include_lags:
        transformers.append(('lag_features', LagFeatureCreator(columns=['amount'], lags=[1, 2, 3])))
    
    # Build pipeline
    steps = []
    
    for name, transformer in transformers:
        steps.append((name, transformer))
    
    # Add numeric column selector to drop datetime/object columns
    steps.append(('numeric_selector', NumericColumnSelector()))
    
    return Pipeline(steps)


class NumericColumnSelector(BaseEstimator, TransformerMixin):
    """Selects only numeric columns and drops datetime/object columns."""
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            # Keep only numeric columns
            numeric_df = X.select_dtypes(include=[np.number])
            return numeric_df.fillna(0)
        return X


def extract_features(df: pd.DataFrame, pipeline: Pipeline = None) -> pd.DataFrame:
    """
    Extract all features from raw transaction data.
    
    Args:
        df: Raw transaction dataframe
        pipeline: Optional pre-fitted pipeline
        
    Returns:
        DataFrame with all engineered features
    """
    if pipeline is None:
        pipeline = create_feature_pipeline()
        pipeline.fit(df)
    
    return pipeline.transform(df)


# =============================================================================
# FEATURE LIST FOR REFERENCE
# =============================================================================

FEATURE_DEFINITIONS = {
    # User behavior features
    'user_tx_count': 'Total number of transactions by user',
    'user_total_donated': 'Total amount donated by user (ETH)',
    'user_avg_donation': 'Average donation amount by user',
    'user_account_age_days': 'Days since user first transaction',
    
    # Project features
    'project_total_raised': 'Total raised by project (ETH)',
    'project_donor_count': 'Number of unique donors to project',
    'project_avg_donation': 'Average donation to project',
    
    # Anomaly detection features
    'amount_zscore': 'Z-score of transaction amount',
    'amount_is_extreme': 'Binary: amount > 99th percentile',
    'amount_log': 'Log-transformed amount',
    
    # Lag features
    'amount_lag_1': 'Previous transaction amount',
    'amount_lag_2': 'Amount 2 transactions ago',
    'amount_lag_3': 'Amount 3 transactions ago',
    
    # Time window features
    'tx_count_5min': 'Transactions in last 5 minutes',
    'tx_count_1h': 'Transactions in last 1 hour',
    'amount_sum_24h': 'Total donated in last 24 hours',
}


if __name__ == "__main__":
    # Demo with synthetic data
    print("Feature Engineering Pipeline Demo")
    print("=" * 50)
    
    # Create sample data
    np.random.seed(42)
    n_samples = 100
    
    df = pd.DataFrame({
        'user_id': np.random.randint(1, 20, n_samples),
        'project_id': np.random.randint(1, 10, n_samples),
        'amount': np.random.exponential(0.5, n_samples),
        'created_at': pd.date_range('2024-01-01', periods=n_samples, freq='H'),
        'tag': np.random.choice(['environment', 'education', 'tech'], n_samples),
    })
    
    print(f"Input shape: {df.shape}")
    print(f"Input columns: {df.columns.tolist()}")
    
    # Create and apply pipeline
    pipeline = create_feature_pipeline()
    features = pipeline.fit_transform(df)
    
    if isinstance(features, pd.DataFrame):
        print(f"\nOutput shape: {features.shape}")
        print(f"Output columns: {features.columns.tolist()}")
        print(f"\nNew features added: {len(features.columns) - len(df.columns)}")
    else:
        print(f"\nOutput shape: {features.shape}")
