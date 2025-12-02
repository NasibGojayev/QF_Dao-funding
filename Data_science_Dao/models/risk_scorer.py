"""Lightweight RiskScorer wrapper. Uses sklearn RandomForest if available,
otherwise falls back to a simple heuristic scorer.
"""
from typing import Optional, List, Dict
import pickle
try:
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

class RiskScorer:
    def __init__(self):
        self.model = None

    def train(self, X: List[List[float]], y: List[int]):
        if SKLEARN_AVAILABLE:
            self.model = RandomForestClassifier(n_estimators=10, random_state=42)
            self.model.fit(X, y)
        else:
            # fallback: store average label
            self.model = {"mean": sum(y) / len(y) if y else 0}

    def score(self, x: List[float]) -> float:
        if SKLEARN_AVAILABLE and self.model is not None:
            proba = self.model.predict_proba([x])
            return float(proba[0][1])
        else:
            return float(self.model.get("mean", 0) if isinstance(self.model, dict) else 0.0)

    def save(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(self.model, f)

    def load(self, path: str):
        with open(path, "rb") as f:
            self.model = pickle.load(f)
