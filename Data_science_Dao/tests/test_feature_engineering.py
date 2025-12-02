import os
from doncoin.data_science.features.feature_engineering import derive_features

def test_derive_features_basic():
    txs = [
        {"user_id": "u1", "amount": 10, "timestamp": "2025-12-01T00:00:00", "success": True},
        {"user_id": "u1", "amount": 20, "timestamp": "2025-12-01T01:00:00", "success": False},
        {"user_id": "u2", "amount": 5, "timestamp": "2025-12-01T02:00:00", "success": True},
    ]
    feats = derive_features(txs)
    users = {f['user_id']: f for f in feats}
    assert users['u1']['tx_count'] == 2
    assert users['u1']['success_count'] == 1
    assert users['u2']['tx_count'] == 1
