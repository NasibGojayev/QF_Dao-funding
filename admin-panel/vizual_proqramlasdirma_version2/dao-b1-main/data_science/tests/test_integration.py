"""
Integration Tests for Data Science Pipeline
============================================
End-to-end tests for the full ML pipeline.
"""
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFullPipeline(unittest.TestCase):
    """Integration tests for the full data science pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests."""
        np.random.seed(42)
        n_samples = 500
        
        # Create realistic transaction data
        cls.raw_data = pd.DataFrame({
            'user_id': np.random.randint(1, 50, n_samples),
            'project_id': np.random.randint(1, 20, n_samples),
            'amount': np.random.exponential(0.5, n_samples),
            'created_at': pd.date_range('2024-01-01', periods=n_samples, freq='H'),
            'tag': np.random.choice(['environment', 'education', 'tech', 'health'], n_samples),
            'success': np.random.choice([True, False], n_samples, p=[0.95, 0.05]),
        })
        
        # Add some anomalies
        anomaly_indices = np.random.choice(n_samples, 25, replace=False)
        cls.raw_data.loc[anomaly_indices, 'amount'] *= 10
        
        # Create labels for classification
        cls.labels = (cls.raw_data['amount'] > cls.raw_data['amount'].quantile(0.9)).astype(int)
    
    def test_feature_engineering_to_model(self):
        """Test feature engineering followed by model training."""
        from data_science.feature_engineering import create_feature_pipeline
        from data_science.models import ClassificationModels
        
        # Feature engineering
        pipeline = create_feature_pipeline()
        features = pipeline.fit_transform(self.raw_data)
        
        # Extract numeric features for model
        if isinstance(features, pd.DataFrame):
            numeric_cols = features.select_dtypes(include=[np.number]).columns
            X = features[numeric_cols].fillna(0).values
        else:
            X = np.nan_to_num(features)
        
        # Train model
        clf = ClassificationModels()
        result = clf.train_logistic_regression(X, self.labels.values, cv=3)
        
        self.assertIsNotNone(result.model)
        self.assertGreater(result.metrics['accuracy'], 0.5)
    
    def test_kpi_to_dashboard(self):
        """Test KPI computation to dashboard data generation."""
        from data_science.kpi_framework import generate_kpi_dashboard_data
        
        dashboard_data = generate_kpi_dashboard_data()
        
        self.assertIn('current', dashboard_data)
        self.assertIn('deltas', dashboard_data)
        self.assertIn('trends', dashboard_data)
        
        # Check trends have data
        for kpi_name, trend_df in dashboard_data['trends'].items():
            self.assertGreater(len(trend_df), 0)
    
    def test_ab_test_full_cycle(self):
        """Test complete A/B test cycle."""
        from data_science.experimentation import ABTest
        
        # Setup test
        test = ABTest(significance_level=0.05)
        
        # Simulate user traffic
        np.random.seed(42)
        control_rate = 0.10
        treatment_rate = 0.12
        
        for _ in range(1000):
            # Control group
            test.record_impression("control")
            if np.random.random() < control_rate:
                test.record_conversion("control", value=np.random.uniform(0.5, 2.0))
            
            # Treatment group
            test.record_impression("treatment")
            if np.random.random() < treatment_rate:
                test.record_conversion("treatment", value=np.random.uniform(0.5, 2.0))
        
        # Analyze
        result = test.analyze()
        summary = test.get_summary()
        
        # Verify
        self.assertIn('lift', summary)
        self.assertIn('p_value', summary)
        self.assertIn('recommendation', summary)
    
    def test_anomaly_detection_pipeline(self):
        """Test anomaly detection from features to predictions."""
        from data_science.feature_engineering import AnomalyFeatures
        from data_science.models import AnomalyDetectionModels
        
        # Feature extraction
        transformer = AnomalyFeatures()
        features = transformer.fit_transform(self.raw_data)
        
        # Extract numeric features
        if isinstance(features, pd.DataFrame):
            numeric_cols = ['amount', 'amount_zscore', 'amount_log']
            numeric_cols = [c for c in numeric_cols if c in features.columns]
            X = features[numeric_cols].fillna(0).values
        else:
            X = features[:, :3]
        
        # Train anomaly detector
        detector = AnomalyDetectionModels(contamination=0.05)
        model, info = detector.train_isolation_forest(X)
        
        # Make predictions
        predictions = model.predict(X)
        
        # Should detect some anomalies
        anomaly_count = (predictions == -1).sum()
        self.assertGreater(anomaly_count, 0)
        self.assertLess(anomaly_count, len(X) * 0.2)  # Not too many
    
    def test_mab_convergence(self):
        """Test Multi-Armed Bandit converges to best arm."""
        from data_science.experimentation import MultiArmedBandit
        
        # True rates
        true_rates = {"arm_a": 0.05, "arm_b": 0.15, "arm_c": 0.10}
        best_arm = "arm_b"
        
        bandit = MultiArmedBandit(arms=list(true_rates.keys()), strategy="ucb1")
        
        # Run simulation
        np.random.seed(42)
        for _ in range(1000):
            arm = bandit.select_arm()
            reward = 1 if np.random.random() < true_rates[arm] else 0
            bandit.update(arm, reward)
        
        # Check convergence
        stats = bandit.get_statistics()
        recommendation = bandit.get_recommendation()
        
        # Best arm should get most pulls (relaxed threshold for UCB1 exploration)
        self.assertEqual(recommendation, best_arm)
        self.assertGreater(stats[best_arm]['pull_ratio'], 0.3)
    
    def test_model_versioning_workflow(self):
        """Test model training, versioning, and loading."""
        from data_science.models import ClassificationModels
        from data_science.inference_logging import ModelVersionManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Train model
            np.random.seed(42)
            X = np.random.randn(100, 5)
            y = (X[:, 0] > 0).astype(int)
            
            clf = ClassificationModels()
            result = clf.train_logistic_regression(X, y, cv=3)
            
            # Register version
            manager = ModelVersionManager(models_dir=tmpdir)
            version = manager.register_model(
                model=result.model,
                model_name="test_classifier",
                metrics=result.metrics,
                hyperparameters=result.best_params
            )
            
            # Load and verify
            loaded_model = manager.load_model("test_classifier")
            self.assertIsNotNone(loaded_model)
            
            # Predictions should match
            original_pred = result.model.predict(X)
            loaded_pred = loaded_model.predict(X)
            np.testing.assert_array_equal(original_pred, loaded_pred)
    
    def test_inference_logging_workflow(self):
        """Test inference logging in production-like scenario."""
        from data_science.models import ClassificationModels
        from data_science.inference_logging import InferenceLogger, TrackedModel
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Train model
            np.random.seed(42)
            X = np.random.randn(100, 5)
            y = (X[:, 0] > 0).astype(int)
            
            clf = ClassificationModels()
            result = clf.train_logistic_regression(X, y, cv=3)
            
            # Wrap model for tracking
            logger = InferenceLogger(log_dir=tmpdir)
            tracked = TrackedModel(
                result.model, 
                model_name="fraud_detector", 
                model_version="1.0.0",
                logger=logger
            )
            
            # Make predictions (automatically logged)
            X_test = np.random.randn(10, 5)
            predictions = tracked.predict(X_test)
            
            # Verify logging
            stats = logger.get_stats()
            self.assertEqual(stats['total_logs'], 10)
            
            # Check log file exists
            log_files = list(os.listdir(tmpdir))
            self.assertGreater(len(log_files), 0)
    
    def test_clustering_to_user_segments(self):
        """Test clustering for user segmentation."""
        from data_science.models import ClusteringModels
        
        # Aggregate user features
        user_features = self.raw_data.groupby('user_id').agg({
            'amount': ['sum', 'mean', 'count'],
        }).reset_index()
        user_features.columns = ['user_id', 'total_amount', 'avg_amount', 'tx_count']
        
        X = user_features[['total_amount', 'avg_amount', 'tx_count']].values
        
        # Cluster users
        cluster = ClusteringModels()
        model, info = cluster.train_kmeans(X, n_clusters_range=[3, 4, 5])
        
        # Assign segments
        user_features['segment'] = model.predict(cluster.scaler.transform(X))
        
        # Verify reasonable distribution
        segment_counts = user_features['segment'].value_counts()
        self.assertGreater(len(segment_counts), 1)
        self.assertLess(segment_counts.min(), segment_counts.max() * 3)  # Not too imbalanced


class TestVisualizationOutput(unittest.TestCase):
    """Test visualization generation."""
    
    def test_generate_all_visualizations(self):
        """Test that all visualizations can be generated."""
        from data_science.visualizations import generate_all_visualizations
        
        with tempfile.TemporaryDirectory() as tmpdir:
            files = generate_all_visualizations(output_dir=tmpdir)
            
            # Should generate multiple files
            self.assertGreater(len(files), 5)
            
            # All files should exist
            for f in files:
                self.assertTrue(os.path.exists(f), f"File not created: {f}")


# =============================================================================
# RUN INTEGRATION TESTS
# =============================================================================

def run_integration_tests():
    """Run all integration tests."""
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestFullPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestVisualizationOutput))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_integration_tests()
    
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
