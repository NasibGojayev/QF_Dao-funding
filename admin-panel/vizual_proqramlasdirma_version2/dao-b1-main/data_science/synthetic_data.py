"""
Synthetic Data Generator
========================
Creates sample datasets for testing and demo purposes.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os


def generate_users(n_users: int = 100) -> pd.DataFrame:
    """Generate synthetic user data."""
    np.random.seed(42)
    
    wallets = [f"0x{''.join(np.random.choice(list('0123456789abcdef'), 40))}" for _ in range(n_users)]
    
    df = pd.DataFrame({
        'user_id': range(1, n_users + 1),
        'wallet': wallets,
        'email': [f"user{i}@example.com" for i in range(1, n_users + 1)],
        'created_at': pd.date_range(
            end=datetime.now(),
            periods=n_users,
            freq='D'
        ) - pd.Timedelta(days=90),
        'is_admin': [i <= 3 for i in range(1, n_users + 1)],
    })
    
    return df


def generate_projects(n_projects: int = 30, n_users: int = 100) -> pd.DataFrame:
    """Generate synthetic project data."""
    np.random.seed(42)
    
    titles = [
        "Community Garden", "Education Platform", "Clean Water Initiative",
        "Tech Hub", "Art Installation", "Healthcare Access", "Solar Energy",
        "Youth Mentorship", "Food Bank", "Housing Support", "Digital Literacy",
        "Wildlife Conservation", "Ocean Cleanup", "Renewable Energy", "Mental Health",
        "Senior Care", "Child Education", "Climate Action", "Refugee Support",
        "Disability Services", "Homeless Shelter", "Veteran Support", "STEM Education",
        "Women Empowerment", "Rural Development", "Urban Farming", "Recycling Program",
        "Public Library", "Sports Center", "Music Academy"
    ][:n_projects]
    
    df = pd.DataFrame({
        'project_id': range(1, n_projects + 1),
        'owner_id': np.random.randint(1, n_users + 1, n_projects),
        'title': titles,
        'description': [f"Description for {t}" for t in titles],
        'created_at': pd.date_range(
            end=datetime.now(),
            periods=n_projects,
            freq='2D'
        ) - pd.Timedelta(days=60),
        'is_active': np.random.choice([True, False], n_projects, p=[0.85, 0.15]),
    })
    
    return df


def generate_tags(n_tags: int = 10) -> pd.DataFrame:
    """Generate synthetic tag data."""
    tag_names = [
        'environment', 'education', 'technology', 'healthcare', 'community',
        'arts', 'infrastructure', 'social', 'science', 'sports'
    ][:n_tags]
    
    df = pd.DataFrame({
        'tag_id': range(1, n_tags + 1),
        'name': tag_names,
    })
    
    return df


def generate_transactions(
    n_transactions: int = 1000,
    n_users: int = 100,
    n_projects: int = 30,
    n_tags: int = 10,
    anomaly_ratio: float = 0.05
) -> pd.DataFrame:
    """Generate synthetic transaction data with some anomalies."""
    np.random.seed(42)
    
    # Generate base transactions
    df = pd.DataFrame({
        'tx_id': range(1, n_transactions + 1),
        'tx_hash': [f"0x{''.join(np.random.choice(list('0123456789abcdef'), 64))}" for _ in range(n_transactions)],
        'block_number': np.cumsum(np.random.randint(1, 10, n_transactions)) + 1000000,
        'user_id': np.random.randint(1, n_users + 1, n_transactions),
        'project_id': np.random.randint(1, n_projects + 1, n_transactions),
        'tag_id': np.random.choice(range(1, n_tags + 1), n_transactions),
        'amount': np.random.exponential(0.5, n_transactions),
        'created_at': pd.date_range(
            end=datetime.now(),
            periods=n_transactions,
            freq='30T'
        ),
        'success': np.random.choice([True, False], n_transactions, p=[0.95, 0.05]),
        'event_type': np.random.choice(
            ['TransactionCreated', 'DonationReceived', 'ContributionMade'],
            n_transactions,
            p=[0.6, 0.3, 0.1]
        ),
    })
    
    # Add anomalies (suspicious high-value transactions)
    n_anomalies = int(n_transactions * anomaly_ratio)
    anomaly_indices = np.random.choice(n_transactions, n_anomalies, replace=False)
    df.loc[anomaly_indices, 'amount'] *= 10  # Anomalously high amounts
    
    # Add derived features
    df['is_anomaly'] = False
    df.loc[anomaly_indices, 'is_anomaly'] = True
    
    return df


def generate_kpi_history(days: int = 30) -> pd.DataFrame:
    """Generate KPI time series data."""
    np.random.seed(42)
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    df = pd.DataFrame({
        'date': dates,
        'active_user_rate': 40 + np.cumsum(np.random.randn(days) * 0.5),
        'avg_tx_per_user': 5 + np.cumsum(np.random.randn(days) * 0.1),
        'avg_donation_amount': 0.7 + np.cumsum(np.random.randn(days) * 0.02),
        'return_rate': 30 + np.cumsum(np.random.randn(days) * 0.3),
        'anomaly_ratio': np.abs(3 + np.random.randn(days) * 0.3),
        'model_latency_p95': 5 + np.abs(np.random.randn(days) * 0.5),
        'daily_tx_count': np.random.randint(50, 150, days),
        'daily_volume': np.random.exponential(10, days),
    })
    
    return df


def generate_model_predictions(n_samples: int = 500) -> pd.DataFrame:
    """Generate synthetic model prediction data."""
    np.random.seed(42)
    
    df = pd.DataFrame({
        'prediction_id': range(1, n_samples + 1),
        'timestamp': pd.date_range(end=datetime.now(), periods=n_samples, freq='5T'),
        'model_name': np.random.choice(['fraud_detector_v1', 'fraud_detector_v2'], n_samples),
        'input_amount': np.random.exponential(0.5, n_samples),
        'input_user_tx_count': np.random.randint(1, 100, n_samples),
        'output_score': np.random.beta(2, 5, n_samples),
        'output_label': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
        'decision': np.random.choice(['ALLOW', 'FLAG_REVIEW', 'BLOCK'], n_samples, p=[0.90, 0.08, 0.02]),
        'latency_ms': np.random.exponential(3, n_samples),
    })
    
    return df


def generate_ab_test_data(n_samples: int = 2000) -> pd.DataFrame:
    """Generate A/B test results data."""
    np.random.seed(42)
    
    # Control: 10% conversion, Treatment: 12% conversion
    control_conversions = np.random.random(n_samples // 2) < 0.10
    treatment_conversions = np.random.random(n_samples // 2) < 0.12
    
    df = pd.DataFrame({
        'user_id': range(1, n_samples + 1),
        'variant': ['control'] * (n_samples // 2) + ['treatment'] * (n_samples // 2),
        'converted': list(control_conversions) + list(treatment_conversions),
        'timestamp': pd.date_range(end=datetime.now(), periods=n_samples, freq='2T'),
    })
    
    return df


def generate_cluster_data(n_samples: int = 300) -> pd.DataFrame:
    """Generate data for clustering visualization."""
    np.random.seed(42)
    
    # Generate 3 clusters
    cluster_0 = np.random.randn(100, 2) + [0, 0]
    cluster_1 = np.random.randn(100, 2) + [4, 4]
    cluster_2 = np.random.randn(100, 2) + [0, 4]
    
    X = np.vstack([cluster_0, cluster_1, cluster_2])
    
    df = pd.DataFrame({
        'sample_id': range(1, n_samples + 1),
        'feature_1': X[:, 0],
        'feature_2': X[:, 1],
        'true_cluster': [0] * 100 + [1] * 100 + [2] * 100,
    })
    
    return df


def save_all_data(output_dir: str = "data"):
    """Generate and save all synthetic datasets."""
    os.makedirs(output_dir, exist_ok=True)
    
    datasets = {
        'users.csv': generate_users(100),
        'projects.csv': generate_projects(30, 100),
        'tags.csv': generate_tags(10),
        'transactions.csv': generate_transactions(1000, 100, 30, 10),
        'kpi_history.csv': generate_kpi_history(30),
        'model_predictions.csv': generate_model_predictions(500),
        'ab_test_results.csv': generate_ab_test_data(2000),
        'cluster_data.csv': generate_cluster_data(300),
    }
    
    for filename, df in datasets.items():
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"[OK] Saved {filepath} ({len(df)} rows)")
    
    return datasets


if __name__ == "__main__":
    print("=" * 50)
    print("Generating Synthetic Data")
    print("=" * 50)
    
    datasets = save_all_data("data_science/data")
    
    print("\n" + "=" * 50)
    print("Data Generation Complete!")
    print("=" * 50)
