"""
A/B Testing Framework for DonCoin DAO
Implements traffic splitting, variant assignment, and statistical analysis.
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import os


@dataclass
class Variant:
    """Represents a test variant"""
    name: str
    weight: float = 0.5
    conversions: int = 0
    impressions: int = 0
    total_value: float = 0.0
    
    @property
    def conversion_rate(self) -> float:
        return self.conversions / self.impressions if self.impressions > 0 else 0.0
    
    @property
    def avg_value(self) -> float:
        return self.total_value / self.conversions if self.conversions > 0 else 0.0


@dataclass
class ABTest:
    """
    A/B Test configuration and tracking.
    
    Features:
    - Deterministic variant assignment based on user ID hash
    - Statistical significance testing
    - Conversion rate and value tracking
    - Confidence interval calculation
    """
    name: str
    variants: List[Variant] = field(default_factory=list)
    primary_metric: str = 'conversion_rate'
    significance_level: float = 0.05
    min_sample_size: int = 100
    created_at: datetime = field(default_factory=datetime.now)
    status: str = 'running'  # running, paused, concluded
    
    def __post_init__(self):
        if not self.variants:
            # Default: control vs treatment
            self.variants = [
                Variant(name='control', weight=0.5),
                Variant(name='treatment', weight=0.5)
            ]
    
    def assign_variant(self, user_id: str) -> str:
        """
        Deterministically assign user to a variant based on hash.
        Same user always gets same variant.
        """
        # Create hash from user_id + test name for consistency
        hash_input = f"{user_id}:{self.name}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Normalize to [0, 1]
        normalized = (hash_value % 10000) / 10000
        
        # Assign based on weights
        cumulative = 0
        for variant in self.variants:
            cumulative += variant.weight
            if normalized < cumulative:
                return variant.name
        
        return self.variants[-1].name
    
    def record_impression(self, variant_name: str):
        """Record that a user saw a variant"""
        for variant in self.variants:
            if variant.name == variant_name:
                variant.impressions += 1
                break
    
    def record_conversion(self, variant_name: str, value: float = 1.0):
        """Record a conversion for a variant"""
        for variant in self.variants:
            if variant.name == variant_name:
                variant.conversions += 1
                variant.total_value += value
                break
    
    def get_variant(self, name: str) -> Optional[Variant]:
        """Get variant by name"""
        for variant in self.variants:
            if variant.name == name:
                return variant
        return None
    
    def _calculate_confidence_interval(self, 
                                       conversions: int, 
                                       impressions: int,
                                       confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate Wilson score confidence interval"""
        if impressions == 0:
            return (0.0, 0.0)
        
        z = stats.norm.ppf(1 - (1 - confidence) / 2)
        p = conversions / impressions
        
        denominator = 1 + z**2 / impressions
        center = (p + z**2 / (2 * impressions)) / denominator
        margin = z * np.sqrt(p * (1 - p) / impressions + z**2 / (4 * impressions**2)) / denominator
        
        return (max(0, center - margin), min(1, center + margin))
    
    def get_results(self) -> Dict[str, Any]:
        """Get current test results with statistical analysis"""
        results = {
            'test_name': self.name,
            'status': self.status,
            'primary_metric': self.primary_metric,
            'created_at': self.created_at.isoformat(),
            'variants': []
        }
        
        for variant in self.variants:
            ci_low, ci_high = self._calculate_confidence_interval(
                variant.conversions, variant.impressions
            )
            
            results['variants'].append({
                'name': variant.name,
                'impressions': variant.impressions,
                'conversions': variant.conversions,
                'conversion_rate': variant.conversion_rate,
                'avg_value': variant.avg_value,
                'total_value': variant.total_value,
                'ci_lower': ci_low,
                'ci_upper': ci_high
            })
        
        # Calculate statistical significance between control and treatment
        if len(self.variants) >= 2:
            control = self.variants[0]
            treatment = self.variants[1]
            
            if control.impressions >= self.min_sample_size and treatment.impressions >= self.min_sample_size:
                # Chi-squared test for proportions
                contingency = np.array([
                    [control.conversions, control.impressions - control.conversions],
                    [treatment.conversions, treatment.impressions - treatment.conversions]
                ])
                
                if contingency.min() >= 0:
                    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
                    
                    results['significance'] = {
                        'chi2': float(chi2),
                        'p_value': float(p_value),
                        'is_significant': p_value < self.significance_level,
                        'significance_level': self.significance_level,
                        'winner': treatment.name if (
                            treatment.conversion_rate > control.conversion_rate and 
                            p_value < self.significance_level
                        ) else (
                            control.name if p_value < self.significance_level else 'none'
                        ),
                        'lift': (
                            (treatment.conversion_rate - control.conversion_rate) / 
                            control.conversion_rate * 100
                        ) if control.conversion_rate > 0 else 0
                    }
                else:
                    results['significance'] = {'error': 'Insufficient data'}
            else:
                results['significance'] = {
                    'is_significant': False,
                    'message': f'Need at least {self.min_sample_size} samples per variant'
                }
        
        return results
    
    def should_conclude(self) -> Tuple[bool, str]:
        """
        Determine if test should be concluded.
        
        Returns:
            Tuple of (should_conclude, reason)
        """
        results = self.get_results()
        
        if 'significance' not in results:
            return False, 'Insufficient data'
        
        sig = results['significance']
        
        if sig.get('is_significant'):
            return True, f"Statistical significance reached. Winner: {sig['winner']}"
        
        # Check if we have enough data with no significance (futility)
        total_impressions = sum(v.impressions for v in self.variants)
        if total_impressions > self.min_sample_size * 10:
            return True, "No significant difference found after extended testing"
        
        return False, "Continue testing"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize test to dictionary"""
        return {
            'name': self.name,
            'primary_metric': self.primary_metric,
            'significance_level': self.significance_level,
            'min_sample_size': self.min_sample_size,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'variants': [
                {
                    'name': v.name,
                    'weight': v.weight,
                    'conversions': v.conversions,
                    'impressions': v.impressions,
                    'total_value': v.total_value
                }
                for v in self.variants
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ABTest':
        """Deserialize test from dictionary"""
        variants = [
            Variant(
                name=v['name'],
                weight=v['weight'],
                conversions=v['conversions'],
                impressions=v['impressions'],
                total_value=v['total_value']
            )
            for v in data['variants']
        ]
        
        return cls(
            name=data['name'],
            variants=variants,
            primary_metric=data['primary_metric'],
            significance_level=data['significance_level'],
            min_sample_size=data['min_sample_size'],
            status=data['status'],
            created_at=datetime.fromisoformat(data['created_at'])
        )


class ABTestManager:
    """
    Manages multiple A/B tests.
    Handles persistence and experiment routing.
    """
    
    def __init__(self, storage_path: str = 'experimentation/ab_tests.json'):
        self.storage_path = storage_path
        self.tests: Dict[str, ABTest] = {}
        self._load_tests()
    
    def _load_tests(self):
        """Load tests from storage"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for test_data in data.get('tests', []):
                    test = ABTest.from_dict(test_data)
                    self.tests[test.name] = test
    
    def _save_tests(self):
        """Save tests to storage"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = {
            'tests': [test.to_dict() for test in self.tests.values()],
            'updated_at': datetime.now().isoformat()
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_test(self,
                    name: str,
                    variants: Optional[List[str]] = None,
                    weights: Optional[List[float]] = None,
                    primary_metric: str = 'conversion_rate',
                    min_sample_size: int = 100) -> ABTest:
        """Create a new A/B test"""
        if name in self.tests:
            raise ValueError(f"Test '{name}' already exists")
        
        if variants:
            if weights is None:
                weights = [1.0 / len(variants)] * len(variants)
            
            variant_objects = [
                Variant(name=v, weight=w)
                for v, w in zip(variants, weights)
            ]
        else:
            variant_objects = None
        
        test = ABTest(
            name=name,
            variants=variant_objects,
            primary_metric=primary_metric,
            min_sample_size=min_sample_size
        )
        
        self.tests[name] = test
        self._save_tests()
        
        return test
    
    def get_test(self, name: str) -> Optional[ABTest]:
        """Get a test by name"""
        return self.tests.get(name)
    
    def get_variant_for_user(self, test_name: str, user_id: str) -> Optional[str]:
        """Get variant assignment for a user in a test"""
        test = self.get_test(test_name)
        if test and test.status == 'running':
            variant = test.assign_variant(user_id)
            test.record_impression(variant)
            self._save_tests()
            return variant
        return None
    
    def record_conversion(self, test_name: str, variant_name: str, value: float = 1.0):
        """Record a conversion"""
        test = self.get_test(test_name)
        if test:
            test.record_conversion(variant_name, value)
            self._save_tests()
    
    def conclude_test(self, test_name: str, winner: Optional[str] = None) -> Dict[str, Any]:
        """Conclude a test and return final results"""
        test = self.get_test(test_name)
        if not test:
            return {'error': 'Test not found'}
        
        test.status = 'concluded'
        results = test.get_results()
        results['winner'] = winner or results.get('significance', {}).get('winner', 'none')
        
        self._save_tests()
        return results
    
    def list_tests(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all tests, optionally filtered by status"""
        tests = []
        for test in self.tests.values():
            if status is None or test.status == status:
                tests.append({
                    'name': test.name,
                    'status': test.status,
                    'variants': len(test.variants),
                    'total_impressions': sum(v.impressions for v in test.variants),
                    'created_at': test.created_at.isoformat()
                })
        return tests


def generate_evaluation_report(test: ABTest) -> str:
    """
    Generate a markdown evaluation report for an A/B test.
    
    Includes:
    - Summary metrics (mean, std dev, CI)
    - Significance testing
    - Discussion on bias and assumptions
    """
    results = test.get_results()
    
    report = f"""# A/B Test Evaluation Report: {test.name}

## Summary

**Test Status:** {test.status}
**Primary Metric:** {test.primary_metric}
**Significance Level:** {test.significance_level}
**Created:** {test.created_at.strftime('%Y-%m-%d %H:%M')}

## Variant Performance

| Variant | Impressions | Conversions | Conv. Rate | 95% CI |
|---------|-------------|-------------|------------|--------|
"""
    
    for v in results['variants']:
        ci_str = f"[{v['ci_lower']:.2%}, {v['ci_upper']:.2%}]"
        report += f"| {v['name']} | {v['impressions']} | {v['conversions']} | {v['conversion_rate']:.2%} | {ci_str} |\n"
    
    report += "\n## Statistical Analysis\n\n"
    
    if 'significance' in results:
        sig = results['significance']
        if 'error' in sig:
            report += f"**Error:** {sig['error']}\n"
        elif 'message' in sig:
            report += f"**Status:** {sig['message']}\n"
        else:
            report += f"""- **Chi-squared statistic:** {sig['chi2']:.4f}
- **P-value:** {sig['p_value']:.4f}
- **Statistically Significant:** {'Yes' if sig['is_significant'] else 'No'}
- **Winner:** {sig['winner']}
- **Lift:** {sig['lift']:.2f}%

"""
    
    report += """## Assumptions and Limitations

1. **Random Assignment:** Users are assigned to variants using a hash-based deterministic function, ensuring consistent experience.
2. **Sample Size:** Results are most reliable when each variant has at least 100 impressions.
3. **Selection Bias:** No known selection bias in variant assignment.
4. **Time Effects:** Test does not account for day-of-week or time effects that may influence behavior.

## Feature Derivation

- **Conversion Rate:** Conversions / Impressions
- **Confidence Intervals:** Wilson score interval (95%)
- **Statistical Test:** Chi-squared test for proportions

## Recommendations

"""
    
    if 'significance' in results and results['significance'].get('is_significant'):
        winner = results['significance']['winner']
        report += f"- **Implement the winning variant ({winner})** in production.\n"
        report += f"- Monitor for any regression in performance after full rollout.\n"
    else:
        report += "- **Continue testing** to gather more data.\n"
        report += "- Consider extending the test duration or increasing traffic.\n"
    
    return report


if __name__ == "__main__":
    # Demo A/B test
    print("Creating A/B test...")
    test = ABTest(
        name='recommender_algorithm_v2',
        variants=[
            Variant(name='control', weight=0.5),
            Variant(name='new_algorithm', weight=0.5)
        ],
        primary_metric='conversion_rate',
        min_sample_size=100
    )
    
    # Simulate some traffic
    np.random.seed(42)
    for i in range(500):
        user_id = f'user_{i}'
        variant = test.assign_variant(user_id)
        test.record_impression(variant)
        
        # Simulate conversions (treatment has 20% higher rate)
        conv_rate = 0.10 if variant == 'control' else 0.12
        if np.random.random() < conv_rate:
            test.record_conversion(variant, value=np.random.uniform(10, 100))
    
    # Get results
    results = test.get_results()
    print(f"\nTest Results:")
    print(f"  Status: {results['status']}")
    
    for v in results['variants']:
        print(f"\n  {v['name']}:")
        print(f"    Impressions: {v['impressions']}")
        print(f"    Conversions: {v['conversions']}")
        print(f"    Conv. Rate: {v['conversion_rate']:.2%}")
        print(f"    95% CI: [{v['ci_lower']:.2%}, {v['ci_upper']:.2%}]")
    
    if 'significance' in results:
        sig = results['significance']
        print(f"\n  Statistical Significance:")
        print(f"    P-value: {sig.get('p_value', 'N/A')}")
        print(f"    Significant: {sig.get('is_significant', 'N/A')}")
        print(f"    Winner: {sig.get('winner', 'N/A')}")
    
    # Generate report
    report = generate_evaluation_report(test)
    print("\n" + "="*60)
    print(report)
