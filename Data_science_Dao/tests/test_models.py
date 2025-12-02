from doncoin.data_science.models.heuristics import TransactionHeuristic
from doncoin.data_science.models.risk_scorer import RiskScorer

def test_heuristic_evaluate():
    h = TransactionHeuristic(amount_threshold=50)
    tx = {"amount": 100}
    score = h.evaluate(tx, {})
    assert score > 0

def test_risk_scorer_train_score():
    rs = RiskScorer()
    # train on simple data
    X = [[1,0,1],[10,2,0]]
    y = [0,1]
    rs.train(X, y)
    s = rs.score([5,1,0.5])
    assert isinstance(s, float)
