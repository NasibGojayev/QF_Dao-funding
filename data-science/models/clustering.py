"""
Donor Clustering Model - K-Means/DBSCAN for Donor Segmentation
Segments donors for targeted engagement strategies.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from typing import Dict, Any, Optional, List, Tuple
import pickle
import os
from datetime import datetime


class DonorClustering:
    """
    Donor Segmentation using clustering.
    
    Segments donors into groups for targeted engagement:
    - High-Value Champions: High total donations, frequent
    - Regular Supporters: Medium donations, consistent
    - One-Time Donors: Single donation, varying amounts
    - At-Risk / Churned: Previously active, now inactive
    """
    
    SEGMENT_NAMES = {
        0: 'High-Value Champions',
        1: 'Regular Supporters', 
        2: 'One-Time Donors',
        3: 'At-Risk / Churned'
    }
    
    def __init__(self, n_clusters: int = 4, method: str = 'kmeans', random_state: int = 42):
        self.n_clusters = n_clusters
        self.method = method
        self.random_state = random_state
        
        self.model = None
        self.scaler = StandardScaler()
        
        self.feature_names = [
            'total_donated',
            'donation_count',
            'avg_donation',
            'days_since_last_donation',
            'days_since_first_donation',
            'unique_proposals',
            'donation_frequency',
            'max_donation',
            'donation_std',
            'recency_score'
        ]
        
        self.cluster_profiles = {}
        self.is_fitted = False
        self.training_metrics = {}
    
    def _create_model(self):
        """Create clustering model"""
        if self.method == 'kmeans':
            return KMeans(
                n_clusters=self.n_clusters,
                random_state=self.random_state,
                n_init=10,
                max_iter=300
            )
        elif self.method == 'dbscan':
            return DBSCAN(eps=0.5, min_samples=5)
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def prepare_features(self, donor_data: pd.DataFrame) -> np.ndarray:
        """
        Prepare features from donor aggregated data.
        
        Expected columns:
        - donor_id: str
        - donations: list of donation dicts with amount, timestamp, proposal_id
        """
        features = []
        
        current_time = datetime.now()
        
        for _, row in donor_data.iterrows():
            donations = row.get('donations', [])
            
            if not donations:
                features.append([0] * len(self.feature_names))
                continue
            
            # Convert to DataFrame for easier processing
            don_df = pd.DataFrame(donations)
            if 'timestamp' in don_df.columns:
                don_df['timestamp'] = pd.to_datetime(don_df['timestamp'])
            
            amounts = don_df['amount'].values
            
            # Calculate features
            total_donated = np.sum(amounts)
            donation_count = len(donations)
            avg_donation = np.mean(amounts)
            max_donation = np.max(amounts)
            donation_std = np.std(amounts) if len(amounts) > 1 else 0
            unique_proposals = don_df['proposal_id'].nunique() if 'proposal_id' in don_df.columns else 1
            
            # Time-based features
            if 'timestamp' in don_df.columns and len(don_df) > 0:
                last_donation = don_df['timestamp'].max()
                first_donation = don_df['timestamp'].min()
                
                days_since_last = (current_time - last_donation.to_pydatetime().replace(tzinfo=None)).days
                days_since_first = (current_time - first_donation.to_pydatetime().replace(tzinfo=None)).days
                
                # Donation frequency (donations per month)
                months_active = max((days_since_first / 30), 1)
                donation_frequency = donation_count / months_active
                
                # Recency score (0-1, higher = more recent)
                recency_score = max(0, 1 - (days_since_last / 365))
            else:
                days_since_last = 30
                days_since_first = 30
                donation_frequency = 1
                recency_score = 0.5
            
            feature_vector = [
                total_donated,
                donation_count,
                avg_donation,
                days_since_last,
                days_since_first,
                unique_proposals,
                donation_frequency,
                max_donation,
                donation_std,
                recency_score
            ]
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def _compute_cluster_profiles(self, features: np.ndarray, labels: np.ndarray):
        """Compute profile statistics for each cluster"""
        self.cluster_profiles = {}
        
        for cluster_id in range(self.n_clusters):
            mask = labels == cluster_id
            cluster_features = features[mask]
            
            if len(cluster_features) == 0:
                continue
            
            profile = {}
            for i, name in enumerate(self.feature_names):
                profile[name] = {
                    'mean': float(np.mean(cluster_features[:, i])),
                    'std': float(np.std(cluster_features[:, i])),
                    'min': float(np.min(cluster_features[:, i])),
                    'max': float(np.max(cluster_features[:, i]))
                }
            
            profile['size'] = int(np.sum(mask))
            profile['percentage'] = float(np.mean(mask) * 100)
            
            self.cluster_profiles[cluster_id] = profile
    
    def _assign_segment_names(self):
        """Assign meaningful names to clusters based on profiles"""
        if not self.cluster_profiles:
            return
        
        # Sort clusters by total_donated mean
        sorted_clusters = sorted(
            self.cluster_profiles.keys(),
            key=lambda x: self.cluster_profiles[x]['total_donated']['mean'],
            reverse=True
        )
        
        # Assign names based on characteristics
        for i, cluster_id in enumerate(sorted_clusters):
            profile = self.cluster_profiles[cluster_id]
            
            # Determine segment based on features
            total = profile['total_donated']['mean']
            freq = profile['donation_frequency']['mean']
            recency = profile['recency_score']['mean']
            count = profile['donation_count']['mean']
            
            if total > 1000 and freq > 2:
                name = 'High-Value Champions'
            elif recency < 0.3 and count > 1:
                name = 'At-Risk / Churned'
            elif count == 1 or freq < 0.5:
                name = 'One-Time Donors'
            else:
                name = 'Regular Supporters'
            
            self.cluster_profiles[cluster_id]['segment_name'] = name
    
    def fit(self, donor_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the clustering model.
        
        Args:
            donor_data: DataFrame with donor_id and donations list
        
        Returns:
            Dictionary of training metrics
        """
        X = self.prepare_features(donor_data)
        X_scaled = self.scaler.fit_transform(X)
        
        # Remove any rows with NaN
        valid_mask = ~np.isnan(X_scaled).any(axis=1)
        X_valid = X_scaled[valid_mask]
        
        # Create and fit model
        self.model = self._create_model()
        labels = self.model.fit_predict(X_valid)
        
        # Update n_clusters for DBSCAN
        if self.method == 'dbscan':
            self.n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        # Calculate metrics
        if self.n_clusters > 1 and len(np.unique(labels)) > 1:
            silhouette = silhouette_score(X_valid, labels)
            calinski = calinski_harabasz_score(X_valid, labels)
        else:
            silhouette = 0
            calinski = 0
        
        # Compute cluster profiles
        self._compute_cluster_profiles(X[valid_mask], labels)
        self._assign_segment_names()
        
        self.training_metrics = {
            'n_clusters': self.n_clusters,
            'silhouette_score': float(silhouette),
            'calinski_harabasz_score': float(calinski),
            'n_donors': len(donor_data),
            'cluster_sizes': {
                int(k): v['size'] 
                for k, v in self.cluster_profiles.items()
            },
            'trained_at': datetime.now().isoformat()
        }
        
        self.is_fitted = True
        return self.training_metrics
    
    def predict(self, donor_data: pd.DataFrame) -> np.ndarray:
        """
        Predict cluster assignments for donors.
        
        Returns:
            Array of cluster labels
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = self.prepare_features(donor_data)
        X_scaled = self.scaler.transform(X)
        
        if self.method == 'kmeans':
            return self.model.predict(X_scaled)
        else:
            # DBSCAN doesn't have predict, use nearest centroid
            return self.model.fit_predict(X_scaled)
    
    def get_segment(self, donor_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Get segment information for donors.
        
        Returns:
            List of segment dicts with cluster_id, segment_name, and profile
        """
        labels = self.predict(donor_data)
        
        results = []
        for i, label in enumerate(labels):
            profile = self.cluster_profiles.get(label, {})
            results.append({
                'cluster_id': int(label),
                'segment_name': profile.get('segment_name', 'Unknown'),
                'cluster_size': profile.get('size', 0)
            })
        
        return results
    
    def get_cluster_profiles(self) -> Dict[int, Dict[str, Any]]:
        """Get profiles for all clusters"""
        return self.cluster_profiles
    
    def get_optimal_k(self, donor_data: pd.DataFrame, k_range: range = range(2, 10)) -> Dict[str, Any]:
        """
        Find optimal number of clusters using elbow method.
        
        Returns:
            Dictionary with scores for each k
        """
        X = self.prepare_features(donor_data)
        X_scaled = self.scaler.fit_transform(X)
        
        results = {'k': [], 'inertia': [], 'silhouette': []}
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = kmeans.fit_predict(X_scaled)
            
            results['k'].append(k)
            results['inertia'].append(float(kmeans.inertia_))
            results['silhouette'].append(float(silhouette_score(X_scaled, labels)))
        
        # Find optimal k (highest silhouette)
        optimal_idx = np.argmax(results['silhouette'])
        results['optimal_k'] = results['k'][optimal_idx]
        
        return results
    
    def save(self, path: str):
        """Save model to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'n_clusters': self.n_clusters,
                'method': self.method,
                'feature_names': self.feature_names,
                'cluster_profiles': self.cluster_profiles,
                'training_metrics': self.training_metrics
            }, f)
    
    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.n_clusters = data['n_clusters']
            self.method = data['method']
            self.feature_names = data['feature_names']
            self.cluster_profiles = data['cluster_profiles']
            self.training_metrics = data['training_metrics']
            self.is_fitted = True


def generate_synthetic_donor_data(n_donors: int = 500) -> pd.DataFrame:
    """Generate synthetic donor data for demonstration"""
    np.random.seed(42)
    
    data = []
    
    for i in range(n_donors):
        # Different donor types
        donor_type = np.random.choice(
            ['high_value', 'regular', 'one_time', 'churned'],
            p=[0.1, 0.3, 0.4, 0.2]
        )
        
        base_time = datetime.now()
        
        if donor_type == 'high_value':
            n_donations = np.random.randint(10, 50)
            avg_amount = np.random.uniform(500, 5000)
            recency = np.random.randint(1, 30)
        elif donor_type == 'regular':
            n_donations = np.random.randint(5, 15)
            avg_amount = np.random.uniform(50, 500)
            recency = np.random.randint(1, 60)
        elif donor_type == 'one_time':
            n_donations = 1
            avg_amount = np.random.uniform(10, 200)
            recency = np.random.randint(1, 365)
        else:  # churned
            n_donations = np.random.randint(3, 10)
            avg_amount = np.random.uniform(50, 300)
            recency = np.random.randint(90, 365)
        
        donations = []
        for j in range(n_donations):
            donations.append({
                'amount': avg_amount * np.random.uniform(0.5, 1.5),
                'timestamp': base_time - pd.Timedelta(days=recency + j * np.random.randint(1, 30)),
                'proposal_id': f'proposal_{np.random.randint(1, 20)}'
            })
        
        data.append({
            'donor_id': f'donor_{i}',
            'donations': donations
        })
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    print("Generating synthetic donor data...")
    donor_data = generate_synthetic_donor_data(500)
    
    print("Training Clustering Model...")
    clustering = DonorClustering(n_clusters=4)
    metrics = clustering.fit(donor_data)
    
    print(f"\nTraining Results:")
    print(f"  Silhouette Score: {metrics['silhouette_score']:.4f}")
    print(f"  Calinski-Harabasz Score: {metrics['calinski_harabasz_score']:.2f}")
    print(f"  Cluster Sizes: {metrics['cluster_sizes']}")
    
    print(f"\nCluster Profiles:")
    for cluster_id, profile in clustering.get_cluster_profiles().items():
        print(f"\n  Cluster {cluster_id} - {profile.get('segment_name', 'Unknown')}:")
        print(f"    Size: {profile['size']} ({profile['percentage']:.1f}%)")
        print(f"    Avg Total Donated: ${profile['total_donated']['mean']:.2f}")
        print(f"    Avg Donation Count: {profile['donation_count']['mean']:.1f}")
        print(f"    Avg Recency Score: {profile['recency_score']['mean']:.2f}")
    
    # Save model
    clustering.save('models/saved/clustering.pkl')
    print("\nModel saved to models/saved/clustering.pkl")
