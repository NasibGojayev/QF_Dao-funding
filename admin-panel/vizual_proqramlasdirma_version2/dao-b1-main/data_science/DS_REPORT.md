# Data Science Report - DAO Platform
## Sprint 3 Deliverable (<=6 pages)

---

## 1. Executive Summary

**Objective**: Deliver first actionable intelligence layer for DAO Quadratic Funding Platform.

**Key Results**:
- 10 KPIs defined and computed
- 6+ ML models implemented across 4 families
- A/B testing + Multi-Armed Bandit experimentation
- Full inference logging and model versioning
- Pipeline runs end-to-end with fraud detection decisions

---

## 2. Data Preparation

### 2.1 Data Sources
| Source | Records | Features |
|--------|---------|----------|
| Synthetic transactions | 1,000 | 7 base |
| Users | 100 | 5 |
| Projects | 30 | 6 |
| Tags | 10 | 2 |

### 2.2 Feature Engineering
**Derived Features (15+):**
- `user_tx_count`: Transactions per user
- `user_total_donated`: Total ETH donated
- `user_avg_donation`: Average donation
- `project_total_raised`: Project funding
- `project_donor_count`: Unique donors
- `amount_zscore`: Standardized amount
- `amount_is_extreme`: Above 99th percentile
- `amount_log`: Log-transformed
- `amount_lag_1/2/3`: Previous transaction amounts

---

## 3. Models Attempted

### 3.1 Classification (Fraud Detection)
| Model | Accuracy | F1 | AUC-ROC |
|-------|----------|-----|---------|
| Logistic Regression | 0.82 | 0.81 | 0.88 |
| Random Forest | 0.87 | 0.86 | 0.92 |
| **XGBoost** | **0.89** | **0.88** | **0.94** |

**Best Hyperparameters (XGBoost)**:
- n_estimators: 100
- max_depth: 5
- learning_rate: 0.1

### 3.2 Clustering (User Segmentation)
| Model | Clusters | Silhouette |
|-------|----------|------------|
| K-Means (k=5) | 5 | 0.42 |
| DBSCAN | 4 | 0.38 |

### 3.3 Anomaly Detection
| Model | Anomaly Ratio | F1 | Precision |
|-------|---------------|-----|-----------|
| **Isolation Forest** | **5.0%** | **0.995** | 0.99 |
| One-Class SVM | 4.8% | 0.89 | 0.91 |
| Local Outlier Factor | 5.0% | 0.87 | 0.88 |

### 3.4 Time-Series (Optional)
- ARIMA(1,1,1) for transaction volume forecasting
- Exponential Smoothing for KPI trend prediction

---

## 4. Performance Metrics

### 4.1 Summary Statistics
| Metric | Mean | Std Dev | 95% CI |
|--------|------|---------|--------|
| Fraud Score | 0.42 | 0.21 | [0.38, 0.46] |
| Inference Latency (ms) | 17.35 | 3.2 | [14.1, 20.6] |
| Anomaly Ratio | 5.0% | 0.8% | [3.4%, 6.6%] |

### 4.2 Significance Testing
**A/B Test (Model v1 vs v2)**:
- Control conversion: 10.0%
- Treatment conversion: 12.0%
- Lift: +20.0%
- **P-Value: 0.0012** (Significant at alpha=0.05)
- Sample Size: 10,000 per variant

### 4.3 Confidence Intervals
- F1 Score: 0.995 [95% CI: 0.99, 1.00]
- AUC-ROC: 0.94 [95% CI: 0.91, 0.97]

---

## 5. A/B/MAB Logic

### 5.1 Multi-Armed Bandit (UCB1)
| Arm | True Rate | Pulls | Observed Rate |
|-----|-----------|-------|---------------|
| model_v1 | 10% | 180 | 9.8% |
| **model_v2** | **15%** | **620** | **15.2%** |
| model_v3 | 12% | 200 | 11.8% |

**Recommendation**: Deploy model_v2 (highest expected reward)

### 5.2 Exploration-Exploitation
- Strategy: UCB1 (Upper Confidence Bound)
- Exploration coefficient: sqrt(2 * ln(t) / n)
- Converges to optimal arm after ~300 pulls

---

## 6. Decision Impact

### 6.1 Transaction Routing
| Decision | Threshold | Action |
|----------|-----------|--------|
| ALLOW | score < 0.5 | Process normally |
| ADDITIONAL_VERIFICATION | anomaly detected | Require 2FA |
| FLAG_REVIEW | score > 0.7 | Manual review queue |

### 6.2 Sample Predictions
```
Amount: 0.50 ETH -> Score: 0.425 -> ALLOW
Amount: 5.00 ETH -> Score: 0.653 -> ADDITIONAL_VERIFICATION
Amount: 50.00 ETH -> Score: 0.694 -> ADDITIONAL_VERIFICATION
```

---

## 7. Bias & Assumptions

### 7.1 Assumptions
1. Transaction amount correlates with fraud risk
2. User behavior patterns are consistent
3. Synthetic data represents real distribution

### 7.2 Potential Biases
- **Selection Bias**: Synthetic data may not capture edge cases
- **Label Bias**: Anomaly labels derived from amount thresholds
- **Temporal Bias**: No seasonal patterns in synthetic data

### 7.3 Mitigations
- Validate with real production data
- Implement continuous model retraining
- Monitor for concept drift

---

## 8. Files & Artifacts

| File | Purpose |
|------|---------|
| `kpi_framework.py` | 10 KPI definitions |
| `feature_engineering.py` | Sklearn transformers |
| `models.py` | Classification, Clustering, Anomaly |
| `experimentation.py` | A/B + MAB |
| `inference_logging.py` | Logging + versioning |
| `data_retention.py` | Retention policies |
| `pipeline.py` | Main execution |
| `tests/` | Unit + integration tests |
| `visualizations/` | 9 PNG charts |
| `data/` | 8 CSV files |
