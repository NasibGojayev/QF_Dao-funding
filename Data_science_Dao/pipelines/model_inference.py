"""Inference pipeline: loads features and applies heuristics or model scoring."""
import os
import csv
from typing import List, Dict
from doncoin.data_science.models.heuristics import TransactionHeuristic
from doncoin.data_science.models.risk_scorer import RiskScorer

class InferencePipeline:
    def __init__(self, model_path: str = None):
        self.heuristic = TransactionHeuristic()
        self.scorer = RiskScorer()
        if model_path:
            try:
                self.scorer.load(model_path)
            except Exception:
                pass

    def score_transactions(self, transactions: List[Dict], user_features: Dict[str, Dict] = None):
        out = []
        for tx in transactions:
            uid = tx.get("user_id")
            uf = user_features.get(uid) if user_features else None
            h = self.heuristic.evaluate(tx, uf)
            # simple feature vector: [amount, tx_count, conversion_rate]
            x = [float(tx.get("amount", 0)), uf.get("tx_count", 0) if uf else 0, uf.get("conversion_rate", 0) if uf else 0]
            try:
                m = self.scorer.score(x)
            except Exception:
                m = 0.0
            out.append({
                "tx_id": tx.get("tx_id"),
                "user_id": uid,
                "amount": tx.get("amount"),
                "heuristic_score": round(h, 4),
                "model_score": round(m, 4),
            })
        return out
