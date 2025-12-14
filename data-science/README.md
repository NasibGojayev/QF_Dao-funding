# DonCoin DAO - Data Science Module

A comprehensive data science implementation for the DonCoin DAO crowdfunding platform, including ML models, experimentation frameworks, and real-time monitoring.

## 📊 Features

### 1. KPI Monitoring
- **Business KPIs**: Funding success rate, conversion rate, time-to-finality, average donation size
- **System KPIs**: Event processing lag, API latency, error rate, suspicious transaction count
- Baseline tracking for continuous improvement

### 2. ML Models (5 Deployed)
| Model | Type | Purpose |
|-------|------|---------|
| Risk Scorer | Random Forest | Fraud/Sybil detection |
| Recommender | Hybrid CF | Proposal recommendations |
| Clustering | K-Means | Donor segmentation |
| Time Series | Prophet | Donation forecasting |
| Outlier Detection | Isolation Forest | Anomaly detection |

### 3. Experimentation
- **A/B Testing**: Hash-based assignment, chi-squared significance testing
- **Multi-Armed Bandit**: Thompson Sampling, ε-greedy, UCB strategies

### 4. Dashboard
Real-time Dash + Plotly + Bootstrap dashboard with:
- KPI overview cards
- Model performance metrics
- Experiment tracking
- Donor segment visualization

## 🚀 Quick Start

### Installation

```bash
cd data-science

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Dashboard

```bash
python dashboard/app.py
# Open http://localhost:8050
```

### Run API Server

```bash
python api/endpoints.py
# Open http://localhost:8051/docs for Swagger UI
```

### Train Models

```bash
# Train individual models
python -m models.risk_scorer
python -m models.recommender
python -m models.clustering
python -m models.time_series
python -m models.outlier_detection
```

## 📁 Project Structure

```
data-science/
├── config/
│   ├── settings.py          # Configuration
│   └── kpis.py               # KPI definitions
├── models/
│   ├── risk_scorer.py        # Fraud detection
│   ├── recommender.py        # Proposal recommendations
│   ├── clustering.py         # Donor segmentation
│   ├── time_series.py        # Donation forecasting
│   └── outlier_detection.py  # Anomaly detection
├── features/
│   ├── feature_engineering.py
│   └── materialized_views.sql
├── experimentation/
│   ├── ab_testing.py         # A/B test framework
│   └── mab.py                # Multi-armed bandit
├── logging/
│   └── model_logger.py       # Prediction logging
├── dashboard/
│   ├── app.py                # Dash application
│   └── assets/style.css
├── api/
│   └── endpoints.py          # FastAPI endpoints
├── notebooks/
│   └── ds_report.ipynb       # DS report (≤6 pages)
├── requirements.txt
└── README.md
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/risk/score` | POST | Get wallet risk score |
| `/api/v1/recommend` | POST | Get proposal recommendations |
| `/api/v1/segment` | POST | Get donor segment |
| `/api/v1/experiment/variant` | POST | Get A/B test variant |
| `/api/v1/experiment/convert` | POST | Record conversion |
| `/api/v1/kpis` | GET | Get current KPIs |

## 📈 Model Performance

| Model | Key Metric | Value |
|-------|------------|-------|
| Risk Scorer | AUC-ROC | 0.91 |
| Recommender | CTR | 8% |
| Clustering | Silhouette | 0.52 |
| Forecasting | MAPE (7-day) | 15% |
| Outlier | F1 Score | 0.72 |

## 🧪 Running Tests

```bash
# Run model demos
python -m models.risk_scorer
python -m models.recommender

# Run experimentation demos
python -m experimentation.ab_testing
python -m experimentation.mab

# Run feature engineering demo
python -m features.feature_engineering
```

## 📊 Database Integration

### Materialized Views

Create PostgreSQL materialized views for dashboard:

```bash
psql -U postgres -d doncoin -f features/materialized_views.sql
```

### Refresh Schedule

```bash
# Hourly (via cron)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_donor_stats;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_proposal_performance;

# Daily
REFRESH MATERIALIZED VIEW mv_daily_metrics;
```

## 🔧 Configuration

Edit `config/settings.py` to configure:
- Database connection
- Model parameters
- KPI thresholds
- Logging settings

## 📝 Documentation

See `notebooks/ds_report.ipynb` for:
- Data preparation and feature list
- Model performance metrics
- Significance testing results
- A/B test logic
- Decision impact analysis

## 🤝 Integration with Backend

The data science module integrates with the Django backend:

1. **Risk scores** can be fetched before approving transactions
2. **Recommendations** can be shown on proposal listing pages
3. **Segments** can be used for targeted email campaigns
4. **A/B tests** can personalize UI elements

```python
# Example: Calling risk API from Django
import requests

response = requests.post(
    'http://localhost:8051/api/v1/risk/score',
    json={'wallet_address': '0x...', 'sybil_score': 0.2}
)
risk_score = response.json()['risk_score']
```

## 📜 License

Part of the DonCoin DAO project.
