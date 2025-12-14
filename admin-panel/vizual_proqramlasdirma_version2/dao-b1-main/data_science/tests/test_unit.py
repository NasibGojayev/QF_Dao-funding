"""
Unit Tests for Data Science Module
==================================
Tests for feature engineering, models, and KPIs.
"""
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKPIFramework(unittest.TestCase):
    """Tests for KPI computation."""
    
    def setUp(self):
        from data_science.kpi_framework import KPIComputer, KPI_REGISTRY
        self.computer = KPIComputer()
        self.registry = KPI_REGISTRY
    
    def test_kpi_registry_exists(self):
        """Test that KPI registry has entries."""
        self.assertGreater(len(self.registry), 0)
        
    def test_kpi_has_required_fields(self):
        """Test each KPI has required fields."""
        required_fields = ['name', 'category', 'definition', 'formula', 'data_source']
        for kpi_id, kpi in self.registry.items():
            for field in required_fields:
                self.assertTrue(hasattr(kpi, field), f"KPI {kpi_id} missing {field}")
    
    def test_active_user_rate_returns_percentage(self):
        """Test active user rate is between 0 and 100."""
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()
        rate = self.computer.active_user_rate(start, end)
        self.assertGreaterEqual(rate, 0)
        self.assertLessEqual(rate, 100)
    
    def test_compute_all_returns_dict(self):
        """Test compute_all returns dictionary of KPIs."""
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()
        kpis = self.computer.compute_all(start, end)
        self.assertIsInstance(kpis, dict)
        self.assertIn('active_user_rate', kpis)
    
    def test_time_series_returns_dataframe(self):
        """Test time series computation returns DataFrame."""
        df = self.computer.compute_time_series('active_user_rate', days=30)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 30)
        self.assertIn('date', df.columns)
        self.assertIn('value', df.columns)


class TestFeatureEngineering(unittest.TestCase):
    """Tests for feature engineering pipeline."""
    
    def setUp(self):
        np.random.seed(42)
        self.n_samples = 100
        self.df = pd.DataFrame({
            'user_id': np.random.randint(1, 20, self.n_samples),
            'project_id': np.random.randint(1, 10, self.n_samples),
            'amount': np.random.exponential(0.5, self.n_samples),
            'created_at': pd.date_range('2024-01-01', periods=self.n_samples, freq='H'),
        })
    
    def test_user_behavior_features(self):
        """Test user behavior feature extraction."""
        from data_science.feature_engineering import UserBehaviorFeatures
        
        transformer = UserBehaviorFeatures()
        result = transformer.fit_transform(self.df)
        
        self.assertIn('user_tx_count', result.columns)
        self.assertIn('user_total_donated', result.columns)
        self.assertIn('user_avg_donation', result.columns)
    
    def test_project_features(self):
        """Test project feature extraction."""
        from data_science.feature_engineering import ProjectFeatures
        
        transformer = ProjectFeatures()
        result = transformer.fit_transform(self.df)
        
        self.assertIn('project_total_raised', result.columns)
        self.assertIn('project_avg_donation', result.columns)
    
    def test_anomaly_features(self):
        """Test anomaly detection features."""
        from data_science.feature_engineering import AnomalyFeatures
        
        transformer = AnomalyFeatures()
        result = transformer.fit_transform(self.df)
        
        self.assertIn('amount_zscore', result.columns)
        self.assertIn('amount_log', result.columns)
    
    def test_lag_features(self):
        """Test lag feature creation."""
        from data_science.feature_engineering import LagFeatureCreator
        
        transformer = LagFeatureCreator(columns=['amount'], lags=[1, 2])
        result = transformer.fit_transform(self.df)
        
        self.assertIn('amount_lag_1', result.columns)
        self.assertIn('amount_lag_2', result.columns)
    
    def test_full_pipeline(self):
        """Test full feature pipeline."""
        from data_science.feature_engineering import create_feature_pipeline
        
        pipeline = create_feature_pipeline()
        result = pipeline.fit_transform(self.df)
        
        # Should have more columns than input
        if isinstance(result, pd.DataFrame):
            self.assertGreater(len(result.columns), len(self.df.columns))


class TestModels(unittest.TestCase):
    """Tests for ML models."""
    
    def setUp(self):
        np.random.seed(42)
        self.n_samples = 200
        self.n_features = 5
        self.X = np.random.randn(self.n_samples, self.n_features)
        self.y = (self.X[:, 0] + self.X[:, 1] * 0.5 > 0).astype(int)
    
    def test_logistic_regression_training(self):
        """Test logistic regression model training."""
        from data_science.models import ClassificationModels
        
        clf = ClassificationModels()
        result = clf.train_logistic_regression(self.X, self.y, cv=3)
        
        self.assertIsNotNone(result.model)
        self.assertIn('accuracy', result.metrics)
        self.assertIn('f1', result.metrics)
        self.assertGreater(result.metrics['accuracy'], 0.5)
    
    def test_random_forest_training(self):
        """Test random forest model training."""
        from data_science.models import ClassificationModels
        
        clf = ClassificationModels()
        result = clf.train_random_forest(self.X, self.y, cv=3)
        
        self.assertIsNotNone(result.model)
        self.assertIn('f1', result.metrics)
    
    def test_kmeans_clustering(self):
        """Test K-means clustering."""
        from data_science.models import ClusteringModels
        
        cluster = ClusteringModels()
        model, info = cluster.train_kmeans(self.X, n_clusters_range=[2, 3, 4])
        
        self.assertIsNotNone(model)
        self.assertIn('n_clusters', info)
        self.assertIn('silhouette', info)
    
    def test_isolation_forest_anomaly(self):
        """Test Isolation Forest anomaly detection."""
        from data_science.models import AnomalyDetectionModels
        
        anomaly = AnomalyDetectionModels(contamination=0.1)
        model, info = anomaly.train_isolation_forest(self.X)
        
        self.assertIsNotNone(model)
        self.assertIn('anomaly_ratio', info)
        self.assertGreater(info['anomaly_count'], 0)
    
    def test_get_best_model(self):
        """Test getting best model after training."""
        from data_science.models import ClassificationModels
        
        clf = ClassificationModels()
        clf.train_logistic_regression(self.X, self.y, cv=3)
        clf.train_random_forest(self.X, self.y, cv=3)
        
        best = clf.get_best_model()
        self.assertIsNotNone(best)


class TestExperimentation(unittest.TestCase):
    """Tests for A/B testing and MAB."""
    
    def test_ab_test_basic(self):
        """Test basic A/B test functionality."""
        from data_science.experimentation import ABTest
        
        test = ABTest()
        
        for _ in range(100):
            test.record_impression("control")
            test.record_impression("treatment")
        
        for _ in range(10):
            test.record_conversion("control")
        for _ in range(15):
            test.record_conversion("treatment")
        
        result = test.analyze()
        
        self.assertEqual(test.control.impressions, 100)
        self.assertEqual(test.treatment.impressions, 100)
        self.assertEqual(test.control.conversions, 10)
        self.assertEqual(test.treatment.conversions, 15)
        self.assertIsNotNone(result.p_value)
    
    def test_ab_test_lift_calculation(self):
        """Test lift calculation."""
        from data_science.experimentation import ABTest
        
        test = ABTest()
        
        for _ in range(100):
            test.record_impression("control")
            test.record_impression("treatment")
        
        for _ in range(10):
            test.record_conversion("control")
        for _ in range(12):
            test.record_conversion("treatment")
        
        result = test.analyze()
        
        # Expected lift: (12-10)/10 = 0.2 = 20%
        self.assertAlmostEqual(result.lift, 0.2, places=2)
    
    def test_mab_arm_selection(self):
        """Test Multi-Armed Bandit arm selection."""
        from data_science.experimentation import MultiArmedBandit
        
        bandit = MultiArmedBandit(arms=["a", "b", "c"], strategy="ucb1")
        
        # First 3 pulls should each select a different arm (exploration)
        arms_selected = set()
        for _ in range(3):
            arm = bandit.select_arm()
            bandit.update(arm, 1)
            arms_selected.add(arm)
        
        self.assertEqual(len(arms_selected), 3)
    
    def test_mab_statistics(self):
        """Test MAB statistics."""
        from data_science.experimentation import MultiArmedBandit
        
        bandit = MultiArmedBandit(arms=["a", "b"], strategy="ucb1")
        
        np.random.seed(42)
        for _ in range(50):
            arm = bandit.select_arm()
            reward = np.random.random()
            bandit.update(arm, reward)
        
        stats = bandit.get_statistics()
        
        self.assertIn('a', stats)
        self.assertIn('b', stats)
        self.assertIn('average_reward', stats['a'])
    
    def test_statistical_tests(self):
        """Test statistical test functions."""
        from data_science.experimentation import chi_square_test, t_test
        
        # Chi-square
        chi_result = chi_square_test(100, 1000, 120, 1000)
        self.assertIn('p_value', chi_result)
        
        # T-test
        control = np.random.normal(10, 2, 100)
        treatment = np.random.normal(11, 2, 100)
        t_result = t_test(control, treatment)
        self.assertIn('p_value', t_result)
        self.assertIn('effect_size', t_result)


class TestInferenceLogging(unittest.TestCase):
    """Tests for inference logging."""
    
    def test_log_creation(self):
        """Test inference log creation."""
        from data_science.inference_logging import InferenceLogger
        
        logger = InferenceLogger(log_dir="test_logs")
        
        log = logger.log_inference(
            model_name="test_model",
            model_version="1.0.0",
            input_features={"a": 1.0, "b": 2.0},
            output_score=0.85,
            inference_latency_ms=5.0
        )
        
        self.assertIsNotNone(log.log_id)
        self.assertEqual(log.model_name, "test_model")
        self.assertEqual(log.output_score, 0.85)
    
    def test_log_statistics(self):
        """Test log statistics computation."""
        from data_science.inference_logging import InferenceLogger
        
        logger = InferenceLogger(log_dir="test_logs")
        
        for _ in range(10):
            logger.log_inference(
                model_name="test_model",
                model_version="1.0.0",
                input_features={"a": 1.0},
                output_score=0.5,
                inference_latency_ms=np.random.uniform(1, 10)
            )
        
        stats = logger.get_stats()
        
        self.assertEqual(stats['total_logs'], 10)
        self.assertIn('avg_latency_ms', stats)


class TestVisualization(unittest.TestCase):
    """Tests for visualization functions."""
    
    def test_visualization_imports(self):
        """Test that visualization module imports correctly."""
        from data_science.visualizations import (
            plot_confusion_matrix,
            plot_roc_curve,
            plot_model_comparison,
            plot_kpi_dashboard
        )
        # If we got here without error, the imports work
        self.assertTrue(True)
    
    def test_confusion_matrix_plot(self):
        """Test confusion matrix plotting."""
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        from data_science.visualizations import plot_confusion_matrix
        import matplotlib.pyplot as plt
        
        y_true = np.array([0, 0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 1, 1, 0, 0])
        
        fig = plot_confusion_matrix(y_true, y_pred)
        self.assertIsNotNone(fig)
        plt.close(fig)


# =============================================================================
# RUN TESTS
# =============================================================================

def run_all_tests():
    """Run all unit tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestKPIFramework))
    suite.addTests(loader.loadTestsFromTestCase(TestFeatureEngineering))
    suite.addTests(loader.loadTestsFromTestCase(TestModels))
    suite.addTests(loader.loadTestsFromTestCase(TestExperimentation))
    suite.addTests(loader.loadTestsFromTestCase(TestInferenceLogging))
    suite.addTests(loader.loadTestsFromTestCase(TestVisualization))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_all_tests()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Success: {result.wasSuccessful()}")
