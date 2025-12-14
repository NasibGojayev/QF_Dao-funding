"""
Proposal Recommender System - Hybrid Collaborative + Content-Based Filtering
Recommends proposals to donors based on their donation history and preferences.
"""
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler, LabelEncoder
from scipy.sparse import csr_matrix
from typing import Dict, Any, Optional, List, Tuple
import pickle
import os
from datetime import datetime
from collections import defaultdict


class ProposalRecommender:
    """
    Hybrid Recommender System for DonCoin DAO proposals.
    
    Combines:
    1. Collaborative Filtering: Find similar donors and recommend what they liked
    2. Content-Based Filtering: Recommend proposals similar to what donor has funded
    3. Popularity-based fallback for cold-start problems
    """
    
    def __init__(self, n_recommendations: int = 5, min_similarity: float = 0.3):
        self.n_recommendations = n_recommendations
        self.min_similarity = min_similarity
        
        # Collaborative filtering components
        self.donor_proposal_matrix = None
        self.donor_similarity = None
        self.donor_ids = []
        self.proposal_ids = []
        
        # Content-based components
        self.proposal_features = None
        self.proposal_similarity = None
        self.category_encoder = LabelEncoder()
        
        # Popularity baseline
        self.proposal_popularity = {}
        
        self.is_fitted = False
        self.training_info = {}
    
    def _build_donor_proposal_matrix(self, donations: pd.DataFrame) -> csr_matrix:
        """
        Build donor-proposal interaction matrix.
        Values represent donation amounts (normalized).
        """
        # Get unique donors and proposals
        self.donor_ids = donations['donor_id'].unique().tolist()
        self.proposal_ids = donations['proposal_id'].unique().tolist()
        
        donor_idx = {d: i for i, d in enumerate(self.donor_ids)}
        proposal_idx = {p: i for i, p in enumerate(self.proposal_ids)}
        
        # Build sparse matrix
        rows, cols, data = [], [], []
        
        for _, row in donations.iterrows():
            if row['donor_id'] in donor_idx and row['proposal_id'] in proposal_idx:
                rows.append(donor_idx[row['donor_id']])
                cols.append(proposal_idx[row['proposal_id']])
                # Use log of amount to reduce impact of very large donations
                data.append(np.log1p(row['amount']))
        
        matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(len(self.donor_ids), len(self.proposal_ids))
        )
        
        return matrix
    
    def _build_proposal_features(self, proposals: pd.DataFrame) -> np.ndarray:
        """
        Build proposal feature matrix for content-based filtering.
        """
        features = []
        
        for _, row in proposals.iterrows():
            # Category encoding
            category = row.get('category', 'Other')
            
            # Numeric features
            budget = row.get('budget', 0)
            total_donations = row.get('total_donations', 0)
            days_active = row.get('days_active', 0)
            unique_donors = row.get('unique_donors', 0)
            funding_pct = row.get('funding_pct', 0)
            
            feature_vector = [
                budget,
                total_donations,
                days_active,
                unique_donors,
                funding_pct
            ]
            features.append(feature_vector)
        
        # Normalize features
        scaler = StandardScaler()
        features_normalized = scaler.fit_transform(features)
        
        # Add one-hot encoded categories
        if 'category' in proposals.columns:
            categories = proposals['category'].fillna('Other').values
            self.category_encoder.fit(categories)
            category_encoded = np.eye(len(self.category_encoder.classes_))[
                self.category_encoder.transform(categories)
            ]
            features_normalized = np.hstack([features_normalized, category_encoded])
        
        return features_normalized
    
    def _calculate_popularity(self, donations: pd.DataFrame):
        """Calculate proposal popularity scores"""
        popularity = donations.groupby('proposal_id').agg({
            'amount': 'sum',
            'donor_id': 'nunique'
        }).rename(columns={'donor_id': 'unique_donors', 'amount': 'total_amount'})
        
        # Combine amount and donor count into popularity score
        popularity['score'] = (
            0.5 * (popularity['total_amount'] / popularity['total_amount'].max()) +
            0.5 * (popularity['unique_donors'] / popularity['unique_donors'].max())
        )
        
        self.proposal_popularity = popularity['score'].to_dict()
    
    def fit(self, donations: pd.DataFrame, proposals: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the recommender system.
        
        Args:
            donations: DataFrame with columns [donor_id, proposal_id, amount, timestamp]
            proposals: DataFrame with columns [proposal_id, category, budget, ...]
        
        Returns:
            Dictionary of training info
        """
        # Build collaborative filtering matrix
        self.donor_proposal_matrix = self._build_donor_proposal_matrix(donations)
        
        # Calculate donor similarity
        self.donor_similarity = cosine_similarity(self.donor_proposal_matrix)
        
        # Build proposal features
        self.proposal_features = self._build_proposal_features(proposals)
        
        # Calculate proposal similarity
        self.proposal_similarity = cosine_similarity(self.proposal_features)
        
        # Calculate popularity
        self._calculate_popularity(donations)
        
        self.training_info = {
            'n_donors': len(self.donor_ids),
            'n_proposals': len(self.proposal_ids),
            'n_donations': len(donations),
            'sparsity': 1 - (self.donor_proposal_matrix.nnz / 
                           (len(self.donor_ids) * len(self.proposal_ids))),
            'trained_at': datetime.now().isoformat()
        }
        
        self.is_fitted = True
        return self.training_info
    
    def _collaborative_scores(self, donor_id: str) -> Dict[str, float]:
        """Get collaborative filtering scores for a donor"""
        if donor_id not in self.donor_ids:
            return {}
        
        donor_idx = self.donor_ids.index(donor_id)
        
        # Get similar donors
        similarities = self.donor_similarity[donor_idx]
        similar_donors_idx = np.argsort(similarities)[::-1][1:11]  # Top 10 similar
        
        # Get proposals they donated to that this donor hasn't
        donor_proposals = set(
            self.proposal_ids[i] 
            for i in self.donor_proposal_matrix[donor_idx].nonzero()[1]
        )
        
        scores = defaultdict(float)
        for sim_idx in similar_donors_idx:
            if similarities[sim_idx] < self.min_similarity:
                continue
            
            sim_proposals = self.donor_proposal_matrix[sim_idx].nonzero()[1]
            for p_idx in sim_proposals:
                proposal_id = self.proposal_ids[p_idx]
                if proposal_id not in donor_proposals:
                    # Weight by similarity and donation amount
                    scores[proposal_id] += (
                        similarities[sim_idx] * 
                        self.donor_proposal_matrix[sim_idx, p_idx]
                    )
        
        return dict(scores)
    
    def _content_scores(self, donor_id: str) -> Dict[str, float]:
        """Get content-based scores based on donor's past funded proposals"""
        if donor_id not in self.donor_ids:
            return {}
        
        donor_idx = self.donor_ids.index(donor_id)
        
        # Get proposals this donor has funded
        funded_proposal_indices = self.donor_proposal_matrix[donor_idx].nonzero()[1]
        
        if len(funded_proposal_indices) == 0:
            return {}
        
        # Calculate average similarity to funded proposals
        scores = {}
        funded_proposals = set(self.proposal_ids[i] for i in funded_proposal_indices)
        
        for p_idx, proposal_id in enumerate(self.proposal_ids):
            if proposal_id in funded_proposals:
                continue
            
            # Average similarity to all funded proposals
            avg_similarity = np.mean([
                self.proposal_similarity[p_idx, fp_idx]
                for fp_idx in funded_proposal_indices
            ])
            
            if avg_similarity >= self.min_similarity:
                scores[proposal_id] = avg_similarity
        
        return scores
    
    def recommend(self, donor_id: str, exclude_funded: bool = True) -> List[Dict[str, Any]]:
        """
        Get recommendations for a donor.
        
        Args:
            donor_id: The donor to get recommendations for
            exclude_funded: Whether to exclude already-funded proposals
        
        Returns:
            List of recommendation dicts with proposal_id and score
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Get scores from different methods
        collab_scores = self._collaborative_scores(donor_id)
        content_scores = self._content_scores(donor_id)
        
        # Combine scores (weighted average)
        combined_scores = defaultdict(float)
        
        for pid, score in collab_scores.items():
            combined_scores[pid] += 0.5 * score
        
        for pid, score in content_scores.items():
            combined_scores[pid] += 0.3 * score
        
        # Add popularity scores for diversity
        for pid, score in self.proposal_popularity.items():
            if pid not in combined_scores or combined_scores[pid] == 0:
                combined_scores[pid] += 0.2 * score
        
        # If no scores (cold start), use popularity only
        if not combined_scores:
            combined_scores = {
                pid: score for pid, score in self.proposal_popularity.items()
            }
        
        # Sort and return top N
        sorted_proposals = sorted(
            combined_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:self.n_recommendations]
        
        return [
            {
                'proposal_id': pid,
                'score': float(score),
                'method': 'hybrid'
            }
            for pid, score in sorted_proposals
        ]
    
    def recommend_for_new_donor(self) -> List[Dict[str, Any]]:
        """Cold-start recommendations for new donors (popularity-based)"""
        sorted_proposals = sorted(
            self.proposal_popularity.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.n_recommendations]
        
        return [
            {
                'proposal_id': pid,
                'score': float(score),
                'method': 'popularity'
            }
            for pid, score in sorted_proposals
        ]
    
    def save(self, path: str):
        """Save model to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'donor_proposal_matrix': self.donor_proposal_matrix,
                'donor_similarity': self.donor_similarity,
                'donor_ids': self.donor_ids,
                'proposal_ids': self.proposal_ids,
                'proposal_features': self.proposal_features,
                'proposal_similarity': self.proposal_similarity,
                'proposal_popularity': self.proposal_popularity,
                'category_encoder': self.category_encoder,
                'n_recommendations': self.n_recommendations,
                'min_similarity': self.min_similarity,
                'training_info': self.training_info
            }, f)
    
    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.donor_proposal_matrix = data['donor_proposal_matrix']
            self.donor_similarity = data['donor_similarity']
            self.donor_ids = data['donor_ids']
            self.proposal_ids = data['proposal_ids']
            self.proposal_features = data['proposal_features']
            self.proposal_similarity = data['proposal_similarity']
            self.proposal_popularity = data['proposal_popularity']
            self.category_encoder = data['category_encoder']
            self.n_recommendations = data['n_recommendations']
            self.min_similarity = data['min_similarity']
            self.training_info = data['training_info']
            self.is_fitted = True


def generate_synthetic_data(n_donors: int = 100, n_proposals: int = 50, n_donations: int = 500):
    """Generate synthetic data for demonstration"""
    np.random.seed(42)
    
    categories = ['Education', 'Environment', 'Healthcare', 'Technology', 'Community']
    
    # Generate proposals
    proposals = pd.DataFrame({
        'proposal_id': [f'proposal_{i}' for i in range(n_proposals)],
        'category': np.random.choice(categories, n_proposals),
        'budget': np.random.uniform(1000, 100000, n_proposals),
        'total_donations': np.random.uniform(0, 50000, n_proposals),
        'days_active': np.random.randint(1, 90, n_proposals),
        'unique_donors': np.random.randint(1, 50, n_proposals),
        'funding_pct': np.random.uniform(0, 100, n_proposals)
    })
    
    # Generate donations with patterns
    donations = []
    for _ in range(n_donations):
        donor_id = f'donor_{np.random.randint(0, n_donors)}'
        proposal_id = f'proposal_{np.random.randint(0, n_proposals)}'
        amount = np.random.exponential(100)  # Most donations are small
        
        donations.append({
            'donor_id': donor_id,
            'proposal_id': proposal_id,
            'amount': amount,
            'timestamp': datetime.now()
        })
    
    return pd.DataFrame(donations), proposals


if __name__ == "__main__":
    print("Generating synthetic data...")
    donations, proposals = generate_synthetic_data(100, 50, 500)
    
    print("Training Recommender...")
    recommender = ProposalRecommender(n_recommendations=5)
    info = recommender.fit(donations, proposals)
    
    print(f"\nTraining Info:")
    print(f"  Donors: {info['n_donors']}")
    print(f"  Proposals: {info['n_proposals']}")
    print(f"  Sparsity: {info['sparsity']:.2%}")
    
    # Get recommendations for a sample donor
    donor_id = 'donor_1'
    recs = recommender.recommend(donor_id)
    
    print(f"\nRecommendations for {donor_id}:")
    for rec in recs:
        print(f"  {rec['proposal_id']}: {rec['score']:.4f} ({rec['method']})")
    
    # Cold start recommendations
    new_recs = recommender.recommend_for_new_donor()
    print(f"\nCold-start recommendations (new donor):")
    for rec in new_recs:
        print(f"  {rec['proposal_id']}: {rec['score']:.4f}")
    
    # Save model
    recommender.save('models/saved/recommender.pkl')
    print("\nModel saved to models/saved/recommender.pkl")
