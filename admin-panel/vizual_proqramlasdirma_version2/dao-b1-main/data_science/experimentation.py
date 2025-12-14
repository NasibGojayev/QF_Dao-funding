"""
A/B Testing and Multi-Armed Bandit Experimentation
====================================================
Statistical testing, confidence intervals, and dynamic routing.
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import random
from collections import defaultdict


# =============================================================================
# A/B TEST FRAMEWORK
# =============================================================================

@dataclass
class ExperimentVariant:
    """Represents a variant in an experiment."""
    name: str
    conversions: int = 0
    impressions: int = 0
    total_value: float = 0.0
    
    @property
    def conversion_rate(self) -> float:
        return self.conversions / self.impressions if self.impressions > 0 else 0.0
    
    @property
    def average_value(self) -> float:
        return self.total_value / self.conversions if self.conversions > 0 else 0.0


@dataclass
class ABTestResult:
    """Results from an A/B test analysis."""
    control: ExperimentVariant
    treatment: ExperimentVariant
    lift: float
    p_value: float
    confidence_interval: Tuple[float, float]
    is_significant: bool
    power: float
    sample_size_needed: int
    
    
class ABTest:
    """A/B Testing framework with statistical analysis."""
    
    def __init__(
        self, 
        control_name: str = "control",
        treatment_name: str = "treatment",
        significance_level: float = 0.05,
        min_detectable_effect: float = 0.05
    ):
        self.control = ExperimentVariant(name=control_name)
        self.treatment = ExperimentVariant(name=treatment_name)
        self.significance_level = significance_level
        self.min_detectable_effect = min_detectable_effect
        self.logs: List[Dict] = []
        
    def record_impression(self, variant: str):
        """Record an impression for a variant."""
        if variant == self.control.name:
            self.control.impressions += 1
        else:
            self.treatment.impressions += 1
            
    def record_conversion(self, variant: str, value: float = 1.0):
        """Record a conversion with optional value."""
        timestamp = datetime.now().isoformat()
        
        if variant == self.control.name:
            self.control.conversions += 1
            self.control.total_value += value
        else:
            self.treatment.conversions += 1
            self.treatment.total_value += value
            
        self.logs.append({
            "timestamp": timestamp,
            "variant": variant,
            "value": value,
            "event": "conversion"
        })
        
    def calculate_sample_size(
        self, 
        baseline_rate: float = 0.1,
        mde: float = None,
        power: float = 0.8
    ) -> int:
        """Calculate required sample size per variant."""
        mde = mde or self.min_detectable_effect
        
        z_alpha = stats.norm.ppf(1 - self.significance_level / 2)
        z_beta = stats.norm.ppf(power)
        
        p1 = baseline_rate
        p2 = baseline_rate * (1 + mde)
        
        pooled_prob = (p1 + p2) / 2
        
        n = (2 * pooled_prob * (1 - pooled_prob) * (z_alpha + z_beta) ** 2) / (p1 - p2) ** 2
        
        return int(np.ceil(n))
    
    def analyze(self) -> ABTestResult:
        """Perform statistical analysis of the test."""
        # Conversion rates
        p_control = self.control.conversion_rate
        p_treatment = self.treatment.conversion_rate
        
        n_control = self.control.impressions
        n_treatment = self.treatment.impressions
        
        # Lift
        lift = (p_treatment - p_control) / p_control if p_control > 0 else 0
        
        # Z-test for proportions
        pooled_p = (self.control.conversions + self.treatment.conversions) / \
                   (n_control + n_treatment) if (n_control + n_treatment) > 0 else 0
        
        if pooled_p > 0 and pooled_p < 1 and n_control > 0 and n_treatment > 0:
            se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
            z_score = (p_treatment - p_control) / se if se > 0 else 0
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        else:
            z_score = 0
            p_value = 1.0
            
        # Confidence interval for difference
        if n_control > 0 and n_treatment > 0:
            se_diff = np.sqrt(
                p_control * (1 - p_control) / n_control +
                p_treatment * (1 - p_treatment) / n_treatment
            )
            z = stats.norm.ppf(1 - self.significance_level / 2)
            diff = p_treatment - p_control
            ci = (diff - z * se_diff, diff + z * se_diff)
        else:
            ci = (0, 0)
            
        # Statistical power
        if n_control > 0 and se > 0:
            effect_size = abs(p_treatment - p_control) / se
            power = 1 - stats.norm.cdf(z - effect_size)
        else:
            power = 0
            
        # Required sample size
        sample_size_needed = self.calculate_sample_size(p_control)
        
        return ABTestResult(
            control=self.control,
            treatment=self.treatment,
            lift=lift,
            p_value=p_value,
            confidence_interval=ci,
            is_significant=p_value < self.significance_level,
            power=power,
            sample_size_needed=sample_size_needed
        )
    
    def get_summary(self) -> Dict:
        """Get human-readable summary."""
        result = self.analyze()
        
        return {
            "control": {
                "impressions": self.control.impressions,
                "conversions": self.control.conversions,
                "rate": f"{self.control.conversion_rate * 100:.2f}%"
            },
            "treatment": {
                "impressions": self.treatment.impressions,
                "conversions": self.treatment.conversions,
                "rate": f"{self.treatment.conversion_rate * 100:.2f}%"
            },
            "lift": f"{result.lift * 100:.2f}%",
            "p_value": f"{result.p_value:.4f}",
            "confidence_interval": f"[{result.confidence_interval[0]*100:.2f}%, {result.confidence_interval[1]*100:.2f}%]",
            "is_significant": result.is_significant,
            "recommendation": "Deploy treatment" if result.is_significant and result.lift > 0 else "Keep control"
        }


# =============================================================================
# MULTI-ARMED BANDIT
# =============================================================================

class MultiArmedBandit:
    """Multi-armed bandit for dynamic traffic allocation."""
    
    def __init__(self, arms: List[str], strategy: str = "ucb1"):
        self.arms = arms
        self.strategy = strategy
        self.counts = {arm: 0 for arm in arms}
        self.values = {arm: 0.0 for arm in arms}
        self.total_pulls = 0
        self.history: List[Dict] = []
        
    def select_arm(self) -> str:
        """Select an arm based on the strategy."""
        self.total_pulls += 1
        
        # Initial exploration: try each arm at least once
        for arm in self.arms:
            if self.counts[arm] == 0:
                return arm
        
        if self.strategy == "ucb1":
            return self._ucb1_select()
        elif self.strategy == "thompson":
            return self._thompson_select()
        elif self.strategy == "epsilon_greedy":
            return self._epsilon_greedy_select()
        else:
            return self._ucb1_select()
    
    def _ucb1_select(self) -> str:
        """Upper Confidence Bound selection."""
        ucb_values = {}
        
        for arm in self.arms:
            if self.counts[arm] == 0:
                return arm
                
            average = self.values[arm] / self.counts[arm]
            exploration = np.sqrt(2 * np.log(self.total_pulls) / self.counts[arm])
            ucb_values[arm] = average + exploration
            
        return max(ucb_values, key=ucb_values.get)
    
    def _thompson_select(self) -> str:
        """Thompson Sampling for binary rewards."""
        samples = {}
        
        for arm in self.arms:
            # Beta distribution parameters
            successes = self.values[arm]
            failures = self.counts[arm] - successes
            
            # Sample from Beta(successes + 1, failures + 1)
            samples[arm] = np.random.beta(successes + 1, failures + 1)
            
        return max(samples, key=samples.get)
    
    def _epsilon_greedy_select(self, epsilon: float = 0.1) -> str:
        """Epsilon-greedy selection."""
        if random.random() < epsilon:
            # Explore
            return random.choice(self.arms)
        else:
            # Exploit
            averages = {
                arm: self.values[arm] / self.counts[arm] if self.counts[arm] > 0 else 0
                for arm in self.arms
            }
            return max(averages, key=averages.get)
    
    def update(self, arm: str, reward: float):
        """Update the arm with observed reward."""
        self.counts[arm] += 1
        self.values[arm] += reward
        
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "arm": arm,
            "reward": reward,
            "cumulative_reward": sum(self.values.values()),
            "regret": self._calculate_regret()
        })
    
    def _calculate_regret(self) -> float:
        """Calculate cumulative regret."""
        if not self.counts or self.total_pulls == 0:
            return 0.0
            
        best_arm_avg = max(
            self.values[arm] / self.counts[arm] if self.counts[arm] > 0 else 0
            for arm in self.arms
        )
        
        actual_reward = sum(self.values.values())
        optimal_reward = best_arm_avg * self.total_pulls
        
        return optimal_reward - actual_reward
    
    def get_statistics(self) -> Dict:
        """Get current statistics for all arms."""
        stats = {}
        
        for arm in self.arms:
            count = self.counts[arm]
            value = self.values[arm]
            avg = value / count if count > 0 else 0
            
            # Wilson confidence interval
            if count > 0:
                z = 1.96  # 95% confidence
                p = avg
                n = count
                denominator = 1 + z**2 / n
                center = (p + z**2 / (2*n)) / denominator
                spread = z * np.sqrt((p*(1-p) + z**2/(4*n)) / n) / denominator
                ci = (max(0, center - spread), min(1, center + spread))
            else:
                ci = (0, 1)
                
            stats[arm] = {
                "count": count,
                "total_reward": value,
                "average_reward": avg,
                "confidence_interval": ci,
                "pull_ratio": count / self.total_pulls if self.total_pulls > 0 else 0
            }
            
        return stats
    
    def get_recommendation(self) -> str:
        """Get the recommended arm to deploy."""
        stats = self.get_statistics()
        
        # Recommend arm with highest average reward
        best_arm = max(stats, key=lambda x: stats[x]["average_reward"])
        
        return best_arm


# =============================================================================
# EXPERIMENT LOGGER
# =============================================================================

class ExperimentLogger:
    """Logs all experiment activities for reproducibility."""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.logs: List[Dict] = []
        self.start_time = datetime.now()
        
    def log_assignment(self, user_id: str, variant: str):
        """Log user assignment to variant."""
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "event": "assignment",
            "user_id": user_id,
            "variant": variant
        })
        
    def log_outcome(self, user_id: str, variant: str, outcome: float, metadata: Dict = None):
        """Log outcome/conversion."""
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "event": "outcome",
            "user_id": user_id,
            "variant": variant,
            "outcome": outcome,
            "metadata": metadata or {}
        })
        
    def export(self) -> Dict:
        """Export all logs."""
        return {
            "experiment_name": self.experiment_name,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_events": len(self.logs),
            "logs": self.logs
        }


# =============================================================================
# STATISTICAL TESTS
# =============================================================================

def chi_square_test(control_conversions: int, control_total: int,
                    treatment_conversions: int, treatment_total: int) -> Dict:
    """Perform chi-square test for independence."""
    # Contingency table
    observed = np.array([
        [control_conversions, control_total - control_conversions],
        [treatment_conversions, treatment_total - treatment_conversions]
    ])
    
    chi2, p_value, dof, expected = stats.chi2_contingency(observed)
    
    return {
        "chi_square": chi2,
        "p_value": p_value,
        "degrees_of_freedom": dof,
        "is_significant": p_value < 0.05
    }


def t_test(control_values: np.ndarray, treatment_values: np.ndarray) -> Dict:
    """Perform t-test for continuous outcomes."""
    t_stat, p_value = stats.ttest_ind(control_values, treatment_values)
    
    # Cohen's d effect size
    pooled_std = np.sqrt(
        (np.std(control_values)**2 + np.std(treatment_values)**2) / 2
    )
    cohens_d = (np.mean(treatment_values) - np.mean(control_values)) / pooled_std if pooled_std > 0 else 0
    
    return {
        "t_statistic": t_stat,
        "p_value": p_value,
        "effect_size": cohens_d,
        "is_significant": p_value < 0.05,
        "control_mean": np.mean(control_values),
        "treatment_mean": np.mean(treatment_values)
    }


def calculate_uplift(control_rate: float, treatment_rate: float) -> Dict:
    """Calculate uplift metrics."""
    absolute_uplift = treatment_rate - control_rate
    relative_uplift = absolute_uplift / control_rate if control_rate > 0 else 0
    
    return {
        "absolute_uplift": absolute_uplift,
        "relative_uplift": relative_uplift,
        "relative_uplift_pct": f"{relative_uplift * 100:.2f}%"
    }


if __name__ == "__main__":
    print("=" * 60)
    print("A/B TESTING & MULTI-ARMED BANDIT DEMO")
    print("=" * 60)
    
    # A/B Test Demo
    print("\n📊 A/B Test Simulation")
    print("-" * 40)
    
    ab_test = ABTest()
    
    np.random.seed(42)
    for _ in range(1000):
        # Control: 10% conversion rate
        ab_test.record_impression("control")
        if np.random.random() < 0.10:
            ab_test.record_conversion("control", value=1.0)
            
        # Treatment: 12% conversion rate
        ab_test.record_impression("treatment")
        if np.random.random() < 0.12:
            ab_test.record_conversion("treatment", value=1.0)
    
    summary = ab_test.get_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Multi-Armed Bandit Demo
    print("\n📊 Multi-Armed Bandit Simulation")
    print("-" * 40)
    
    bandit = MultiArmedBandit(arms=["model_a", "model_b", "model_c"], strategy="ucb1")
    
    # True conversion rates (unknown to bandit)
    true_rates = {"model_a": 0.10, "model_b": 0.15, "model_c": 0.12}
    
    np.random.seed(42)
    for _ in range(500):
        arm = bandit.select_arm()
        reward = 1 if np.random.random() < true_rates[arm] else 0
        bandit.update(arm, reward)
    
    stats = bandit.get_statistics()
    for arm, stat in stats.items():
        print(f"{arm}: avg={stat['average_reward']:.3f}, pulls={stat['count']}, ratio={stat['pull_ratio']:.2f}")
    
    print(f"\nRecommendation: Deploy {bandit.get_recommendation()}")
