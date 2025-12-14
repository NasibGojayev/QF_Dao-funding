"""
Multi-Armed Bandit Framework for DonCoin DAO
Implements Thompson Sampling and Epsilon-Greedy for explore/exploit.
"""
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


@dataclass
class BanditArm:
    """Represents an arm (variant) in the bandit"""
    name: str
    # Beta distribution parameters for Thompson Sampling
    alpha: float = 1.0  # Successes + 1
    beta: float = 1.0   # Failures + 1
    pulls: int = 0
    total_reward: float = 0.0
    
    @property
    def mean_reward(self) -> float:
        return self.total_reward / self.pulls if self.pulls > 0 else 0.0
    
    @property
    def success_rate(self) -> float:
        """Estimate of success rate from Beta distribution"""
        return self.alpha / (self.alpha + self.beta)
    
    def sample_thompson(self) -> float:
        """Sample from Beta distribution for Thompson Sampling"""
        return np.random.beta(self.alpha, self.beta)
    
    def update(self, reward: float):
        """Update arm statistics after a pull"""
        self.pulls += 1
        self.total_reward += reward
        
        # Update Beta parameters (treat reward as binary success/failure)
        if reward > 0:
            self.alpha += 1
        else:
            self.beta += 1


class MultiArmedBandit:
    """
    Multi-Armed Bandit implementation.
    
    Supports:
    - Thompson Sampling: Bayesian approach, good for exploration
    - Epsilon-Greedy: Simple, mostly exploit with random exploration
    - UCB (Upper Confidence Bound): Balance exploration with uncertainty
    """
    
    def __init__(self,
                 arms: List[str],
                 strategy: str = 'thompson',
                 epsilon: float = 0.1):
        """
        Initialize the bandit.
        
        Args:
            arms: List of arm names
            strategy: 'thompson', 'epsilon_greedy', or 'ucb'
            epsilon: Exploration rate for epsilon-greedy
        """
        self.strategy = strategy
        self.epsilon = epsilon
        self.arms: Dict[str, BanditArm] = {
            name: BanditArm(name=name)
            for name in arms
        }
        self.total_pulls = 0
        self.history: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
    
    def select_arm(self) -> str:
        """
        Select an arm based on the strategy.
        
        Returns:
            Name of the selected arm
        """
        if self.strategy == 'thompson':
            return self._thompson_sampling()
        elif self.strategy == 'epsilon_greedy':
            return self._epsilon_greedy()
        elif self.strategy == 'ucb':
            return self._ucb()
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    def _thompson_sampling(self) -> str:
        """Thompson Sampling: Sample from posterior and select max"""
        samples = {
            name: arm.sample_thompson()
            for name, arm in self.arms.items()
        }
        return max(samples, key=samples.get)
    
    def _epsilon_greedy(self) -> str:
        """Epsilon-Greedy: Random with probability epsilon, else best arm"""
        if np.random.random() < self.epsilon:
            # Explore: random arm
            return np.random.choice(list(self.arms.keys()))
        else:
            # Exploit: best arm by mean reward
            return max(
                self.arms.keys(),
                key=lambda x: self.arms[x].mean_reward
            )
    
    def _ucb(self) -> str:
        """Upper Confidence Bound: Balance exploration with uncertainty"""
        if self.total_pulls == 0:
            return list(self.arms.keys())[0]
        
        ucb_values = {}
        for name, arm in self.arms.items():
            if arm.pulls == 0:
                ucb_values[name] = float('inf')  # Unexplored arms have infinite value
            else:
                exploitation = arm.mean_reward
                exploration = np.sqrt(2 * np.log(self.total_pulls) / arm.pulls)
                ucb_values[name] = exploitation + exploration
        
        return max(ucb_values, key=ucb_values.get)
    
    def update(self, arm_name: str, reward: float):
        """
        Update arm after observing reward.
        
        Args:
            arm_name: Name of the arm that was pulled
            reward: Observed reward (0 or 1 for binary, any float for continuous)
        """
        if arm_name not in self.arms:
            raise ValueError(f"Unknown arm: {arm_name}")
        
        self.arms[arm_name].update(reward)
        self.total_pulls += 1
        
        # Record history
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'arm': arm_name,
            'reward': reward,
            'total_pulls': self.total_pulls
        })
    
    def get_arm_probabilities(self) -> Dict[str, float]:
        """
        Get selection probabilities for each arm.
        Useful for understanding current state.
        """
        if self.strategy == 'thompson':
            # Simulate many samples to estimate selection probability
            n_samples = 1000
            selections = {name: 0 for name in self.arms}
            
            for _ in range(n_samples):
                samples = {
                    name: arm.sample_thompson()
                    for name, arm in self.arms.items()
                }
                winner = max(samples, key=samples.get)
                selections[winner] += 1
            
            return {name: count / n_samples for name, count in selections.items()}
        
        elif self.strategy == 'epsilon_greedy':
            best_arm = max(
                self.arms.keys(),
                key=lambda x: self.arms[x].mean_reward
            )
            
            n_arms = len(self.arms)
            probs = {}
            for name in self.arms:
                if name == best_arm:
                    probs[name] = 1 - self.epsilon + self.epsilon / n_arms
                else:
                    probs[name] = self.epsilon / n_arms
            return probs
        
        else:
            return {name: 1.0 / len(self.arms) for name in self.arms}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current bandit statistics"""
        return {
            'strategy': self.strategy,
            'total_pulls': self.total_pulls,
            'arms': {
                name: {
                    'pulls': arm.pulls,
                    'mean_reward': arm.mean_reward,
                    'total_reward': arm.total_reward,
                    'success_rate': arm.success_rate,
                    'alpha': arm.alpha,
                    'beta': arm.beta
                }
                for name, arm in self.arms.items()
            },
            'selection_probabilities': self.get_arm_probabilities(),
            'created_at': self.created_at.isoformat()
        }
    
    def get_regret(self, optimal_reward: float = 1.0) -> Dict[str, Any]:
        """
        Calculate regret (difference from optimal).
        
        Args:
            optimal_reward: The reward that would be obtained by always selecting the best arm
        """
        if self.total_pulls == 0:
            return {'cumulative_regret': 0, 'avg_regret': 0}
        
        total_obtained = sum(arm.total_reward for arm in self.arms.values())
        optimal_total = self.total_pulls * optimal_reward
        
        cumulative_regret = optimal_total - total_obtained
        avg_regret = cumulative_regret / self.total_pulls
        
        return {
            'cumulative_regret': cumulative_regret,
            'avg_regret': avg_regret,
            'total_reward': total_obtained,
            'optimal_reward': optimal_total
        }
    
    def recommend_best_arm(self) -> Tuple[str, float]:
        """
        Recommend the best arm based on current data.
        
        Returns:
            Tuple of (arm_name, confidence)
        """
        if self.total_pulls == 0:
            return (list(self.arms.keys())[0], 0.0)
        
        # Best by mean reward
        best_arm = max(
            self.arms.keys(),
            key=lambda x: self.arms[x].mean_reward
        )
        
        # Confidence based on number of pulls relative to total
        arm = self.arms[best_arm]
        confidence = min(1.0, arm.pulls / 100)  # Max confidence at 100 pulls
        
        return (best_arm, confidence)
    
    def save(self, path: str):
        """Save bandit state to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        data = {
            'strategy': self.strategy,
            'epsilon': self.epsilon,
            'total_pulls': self.total_pulls,
            'created_at': self.created_at.isoformat(),
            'arms': {
                name: {
                    'alpha': arm.alpha,
                    'beta': arm.beta,
                    'pulls': arm.pulls,
                    'total_reward': arm.total_reward
                }
                for name, arm in self.arms.items()
            },
            'history': self.history[-1000:]  # Keep last 1000 entries
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, path: str):
        """Load bandit state from disk"""
        with open(path, 'r') as f:
            data = json.load(f)
        
        self.strategy = data['strategy']
        self.epsilon = data['epsilon']
        self.total_pulls = data['total_pulls']
        self.created_at = datetime.fromisoformat(data['created_at'])
        self.history = data.get('history', [])
        
        self.arms = {}
        for name, arm_data in data['arms'].items():
            arm = BanditArm(
                name=name,
                alpha=arm_data['alpha'],
                beta=arm_data['beta'],
                pulls=arm_data['pulls'],
                total_reward=arm_data['total_reward']
            )
            self.arms[name] = arm


class ContextualBandit(MultiArmedBandit):
    """
    Extension for contextual bandits.
    Uses context features to make arm selection decisions.
    """
    
    def __init__(self, arms: List[str], n_features: int = 10, **kwargs):
        super().__init__(arms, **kwargs)
        self.n_features = n_features
        
        # Linear weights for each arm
        self.weights = {
            name: np.zeros(n_features)
            for name in arms
        }
    
    def select_arm_with_context(self, context: np.ndarray) -> str:
        """
        Select arm using context features.
        
        Args:
            context: Feature vector of shape (n_features,)
        """
        if self.strategy == 'epsilon_greedy':
            if np.random.random() < self.epsilon:
                return np.random.choice(list(self.arms.keys()))
            else:
                # Select arm with highest predicted reward
                predictions = {
                    name: np.dot(self.weights[name], context)
                    for name in self.arms
                }
                return max(predictions, key=predictions.get)
        else:
            # Fallback to regular Thompson Sampling
            return self._thompson_sampling()
    
    def update_with_context(self, arm_name: str, context: np.ndarray, reward: float, learning_rate: float = 0.1):
        """Update weights using gradient descent"""
        # Update regular arm statistics
        self.update(arm_name, reward)
        
        # Update linear weights
        prediction = np.dot(self.weights[arm_name], context)
        error = reward - prediction
        self.weights[arm_name] += learning_rate * error * context


if __name__ == "__main__":
    # Demo Multi-Armed Bandit
    print("="*60)
    print("Multi-Armed Bandit Demonstration")
    print("="*60)
    
    # Create bandit with 3 arms
    arms = ['algorithm_v1', 'algorithm_v2', 'algorithm_v3']
    true_rewards = {'algorithm_v1': 0.3, 'algorithm_v2': 0.5, 'algorithm_v3': 0.35}
    
    np.random.seed(42)
    
    # Test each strategy
    for strategy in ['thompson', 'epsilon_greedy', 'ucb']:
        print(f"\n{strategy.upper()} Strategy:")
        print("-" * 40)
        
        bandit = MultiArmedBandit(arms=arms, strategy=strategy, epsilon=0.1)
        
        # Simulate 1000 pulls
        for _ in range(1000):
            arm = bandit.select_arm()
            # Simulate reward based on true probabilities
            reward = 1.0 if np.random.random() < true_rewards[arm] else 0.0
            bandit.update(arm, reward)
        
        # Print results
        stats = bandit.get_statistics()
        print(f"  Total Pulls: {stats['total_pulls']}")
        print(f"  Arm Statistics:")
        for name, arm_stats in stats['arms'].items():
            true_p = true_rewards[name]
            print(f"    {name}:")
            print(f"      Pulls: {arm_stats['pulls']}")
            print(f"      Est. Success Rate: {arm_stats['success_rate']:.2%} (true: {true_p:.2%})")
        
        # Selection probabilities
        probs = stats['selection_probabilities']
        print(f"  Selection Probabilities: {', '.join(f'{k}: {v:.2%}' for k, v in probs.items())}")
        
        # Best arm recommendation
        best, confidence = bandit.recommend_best_arm()
        print(f"  Recommended Arm: {best} (confidence: {confidence:.2%})")
        
        # Regret
        regret = bandit.get_regret(optimal_reward=0.5)  # algorithm_v2 is optimal
        print(f"  Cumulative Regret: {regret['cumulative_regret']:.2f}")
    
    # Save example
    bandit.save('experimentation/mab_state.json')
    print(f"\nBandit state saved to experimentation/mab_state.json")
