"""Minimal ETL pipeline that generates synthetic raw transactions and transforms
them into feature vectors using the feature_engineering utilities.
"""
import os
import uuid
import random
import datetime
import csv
from typing import List, Dict
from doncoin.data_science.features.feature_engineering import derive_features

class ETLPipeline:
    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)

    def generate_raw_transactions(self, n_transactions: int = 500):
        rows = []
        now = datetime.datetime.utcnow()
        for i in range(n_transactions):
            uid = str(uuid.uuid4()) if random.random() < 0.7 else f"user_{random.randint(1,50)}"
            ts = (now - datetime.timedelta(seconds=random.randint(0, 86400))).isoformat()
            amt = round(random.expovariate(1/50), 6)
            success = random.random() > 0.2
            rows.append({
                "tx_id": str(uuid.uuid4()),
                "user_id": uid,
                "amount": amt,
                "timestamp": ts,
                "success": success,
            })
        raw_path = os.path.join(self.out_dir, "raw_transactions.csv")
        keys = ["tx_id", "user_id", "amount", "timestamp", "success"]
        with open(raw_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        return raw_path, rows

    def transform_to_features(self, transactions: List[Dict]):
        feats = derive_features(transactions)
        feat_path = os.path.join(self.out_dir, "features.csv")
        keys = ["user_id", "tx_count", "total_amount", "avg_amount", "success_count", "conversion_rate", "activity_seconds"]
        with open(feat_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in feats:
                writer.writerow(r)
        return feat_path, feats
