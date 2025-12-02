"""Simple heuristics for transaction risk and detection."""
from typing import Dict

class TransactionHeuristic:
    """Rule-based heuristics for scoring a transaction.

    Example rules:
    - high amount (> threshold) -> higher risk
    - high frequency (tx_count within short window) -> higher risk
    - low account age -> higher risk
    """
    def __init__(self, amount_threshold: float = 1000.0):
        self.amount_threshold = amount_threshold

    def evaluate(self, tx: Dict, user_features: Dict = None) -> float:
        """Return a risk score between 0.0 (low) and 1.0 (high)."""
        score = 0.0
        amt = float(tx.get("amount", 0))
        if amt >= self.amount_threshold:
            score += 0.6
        if user_features:
            tx_count = user_features.get("tx_count", 0)
            conv = user_features.get("conversion_rate", 1.0)
            if tx_count > 10:
                score += 0.2
            if conv < 0.2:
                score += 0.1
        # clamp
        return min(1.0, score)
