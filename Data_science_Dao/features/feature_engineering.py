"""Simple feature engineering utilities used by pipelines and tests.

Functions:
- derive_features(raw_tx_df): returns DataFrame with derived features per user
- user_conversion_rate(transactions): returns conversion rate per user
"""
from typing import List, Dict
import statistics
import datetime
import csv

def derive_features(transactions: List[Dict]) -> List[Dict]:
    """Derive simple features from a list of transaction dicts.

    Each transaction dict expected keys: 'user_id', 'amount', 'timestamp', 'success'
    Returns list of feature dicts keyed by user_id.
    """
    users = {}
    for tx in transactions:
        uid = tx.get("user_id")
        if uid not in users:
            users[uid] = {
                "user_id": uid,
                "tx_count": 0,
                "total_amount": 0.0,
                "success_count": 0,
                "first_seen": tx.get("timestamp"),
                "last_seen": tx.get("timestamp"),
            }
        users[uid]["tx_count"] += 1
        users[uid]["total_amount"] += float(tx.get("amount", 0))
        if tx.get("success"):
            users[uid]["success_count"] += 1
        # update times
        if tx.get("timestamp") and tx.get("timestamp") < users[uid]["first_seen"]:
            users[uid]["first_seen"] = tx.get("timestamp")
        if tx.get("timestamp") and tx.get("timestamp") > users[uid]["last_seen"]:
            users[uid]["last_seen"] = tx.get("timestamp")

    # compute derived features
    out = []
    for uid, v in users.items():
        duration = 0
        try:
            fs = datetime.datetime.fromisoformat(v["first_seen"]) if v["first_seen"] else None
            ls = datetime.datetime.fromisoformat(v["last_seen"]) if v["last_seen"] else None
            if fs and ls:
                duration = max(0, (ls - fs).total_seconds())
        except Exception:
            duration = 0
        avg_amount = v["total_amount"] / v["tx_count"] if v["tx_count"] else 0
        conv_rate = v["success_count"] / v["tx_count"] if v["tx_count"] else 0
        out.append({
            "user_id": uid,
            "tx_count": v["tx_count"],
            "total_amount": round(v["total_amount"], 6),
            "avg_amount": round(avg_amount, 6),
            "success_count": v["success_count"],
            "conversion_rate": round(conv_rate, 4),
            "activity_seconds": int(duration),
        })
    return out

def user_conversion_rate(transactions: List[Dict]) -> Dict[str, float]:
    """Return conversion rate per user as a dict user_id->rate."""
    feats = derive_features(transactions)
    return {f["user_id"]: f["conversion_rate"] for f in feats}
