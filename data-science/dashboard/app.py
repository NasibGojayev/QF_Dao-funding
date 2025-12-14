"""
DonCoin DAO Data Science Dashboard
Built with Dash + Plotly + Bootstrap
"""
import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.kpis import BUSINESS_KPIS, SYSTEM_KPIS, KPITracker

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    title='DonCoin DAO - Data Science Dashboard'
)

# ============================================================
# SAMPLE DATA GENERATORS (Replace with real database queries)
# ============================================================

def generate_sample_kpi_data():
    """Generate sample KPI data for demonstration"""
    return {
        'funding_success_rate': {'value': 62.5, 'trend': 'up', 'change': 5.2},
        'conversion_rate': {'value': 12.8, 'trend': 'up', 'change': 1.3},
        'time_to_finality_days': {'value': 18.3, 'trend': 'down', 'change': -2.1},
        'average_donation_size': {'value': 156.42, 'trend': 'up', 'change': 12.5},
        'event_processing_lag': {'value': 2.3, 'trend': 'stable', 'change': 0.1},
        'api_response_latency_p95': {'value': 145, 'trend': 'down', 'change': -15},
        'error_rate': {'value': 0.05, 'trend': 'stable', 'change': 0.0},
        'suspicious_transaction_count': {'value': 3, 'trend': 'down', 'change': -2},
    }


def generate_sample_time_series():
    """Generate sample time series data"""
    dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
    np.random.seed(42)
    
    base_donations = 1000
    trend = np.linspace(0, 200, 90)
    seasonality = 100 * np.sin(np.linspace(0, 6*np.pi, 90))
    noise = np.random.normal(0, 50, 90)
    
    donations = base_donations + trend + seasonality + noise
    
    return pd.DataFrame({
        'date': dates,
        'donations': donations.clip(min=0),
        'unique_donors': (donations / 10 + np.random.normal(0, 5, 90)).clip(min=0).astype(int),
        'proposals_funded': np.random.poisson(3, 90)
    })


def generate_sample_model_performance():
    """Generate sample model performance data"""
    return {
        'risk_scorer': {
            'accuracy': 0.89,
            'precision': 0.85,
            'recall': 0.72,
            'auc_roc': 0.91,
            'predictions_today': 1250,
            'avg_latency_ms': 12.3
        },
        'recommender': {
            'click_through_rate': 0.08,
            'conversion_rate': 0.03,
            'coverage': 0.75,
            'predictions_today': 3420,
            'avg_latency_ms': 45.6
        },
        'outlier_detector': {
            'precision': 0.82,
            'recall': 0.65,
            'f1_score': 0.72,
            'anomalies_detected_today': 8,
            'avg_latency_ms': 8.7
        }
    }


def generate_sample_experiment_data():
    """Generate sample A/B test data"""
    return {
        'recommender_v2': {
            'status': 'running',
            'days_running': 14,
            'variants': {
                'control': {'impressions': 5234, 'conversions': 418, 'rate': 0.080},
                'treatment': {'impressions': 5189, 'conversions': 519, 'rate': 0.100}
            },
            'lift': 25.0,
            'p_value': 0.023,
            'is_significant': True
        },
        'risk_threshold_test': {
            'status': 'running',
            'days_running': 7,
            'variants': {
                'low': {'impressions': 2100, 'rate': 0.05},
                'medium': {'impressions': 2050, 'rate': 0.06},
                'high': {'impressions': 2080, 'rate': 0.08}
            },
            'p_value': 0.12,
            'is_significant': False
        }
    }


def generate_sample_cluster_data():
    """Generate sample donor cluster data"""
    return pd.DataFrame({
        'segment': ['High-Value Champions', 'Regular Supporters', 'One-Time Donors', 'At-Risk / Churned'],
        'count': [45, 230, 580, 120],
        'avg_donation': [1250.50, 185.30, 42.10, 95.60],
        'total_value': [56272.50, 42619.00, 24418.00, 11472.00]
    })


# ============================================================
# LAYOUT COMPONENTS
# ============================================================

def create_kpi_card(title, value, unit, trend, change, target=None):
    """Create a KPI card component"""
    trend_icon = "▲" if trend == 'up' else ("▼" if trend == 'down' else "→")
    trend_color = "success" if (trend == 'up') else ("danger" if trend == 'down' else "secondary")
    
    # Adjust color based on KPI (some KPIs are better when lower)
    if title in ['Time to Finality', 'Event Lag', 'API Latency', 'Error Rate', 'Suspicious TX']:
        trend_color = "danger" if trend == 'up' else ("success" if trend == 'down' else "secondary")
    
    card = dbc.Card([
        dbc.CardBody([
            html.H6(title, className="text-muted mb-1", style={'fontSize': '0.85rem'}),
            html.Div([
                html.Span(f"{value}", className="h3 mb-0 me-2"),
                html.Span(unit, className="text-muted small"),
            ]),
            html.Div([
                dbc.Badge(f"{trend_icon} {abs(change):.1f}%", color=trend_color, className="me-2"),
                html.Small(f"Target: {target}" if target else "", className="text-muted")
            ], className="mt-2")
        ])
    ], className="h-100")
    
    return card


def create_navbar():
    """Create navigation bar"""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Img(src="/assets/logo.png", height="30px"), width="auto"),
                dbc.Col(dbc.NavbarBrand("DonCoin DAO - DS Dashboard", className="ms-2")),
            ], align="center", className="g-0"),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("KPI Overview", href="#", id="nav-kpi", active=True)),
                    dbc.NavItem(dbc.NavLink("Model Performance", href="#", id="nav-models")),
                    dbc.NavItem(dbc.NavLink("Experiments", href="#", id="nav-experiments")),
                    dbc.NavItem(dbc.NavLink("Clusters", href="#", id="nav-clusters")),
                ], className="ms-auto", navbar=True),
                id="navbar-collapse",
                navbar=True,
            ),
        ], fluid=True),
        color="dark",
        dark=True,
        className="mb-4"
    )


def create_kpi_overview_tab():
    """Create KPI overview layout"""
    kpi_data = generate_sample_kpi_data()
    time_series = generate_sample_time_series()
    
    # Business KPI Cards
    business_kpi_cards = dbc.Row([
        dbc.Col(create_kpi_card(
            "Funding Success Rate",
            f"{kpi_data['funding_success_rate']['value']:.1f}",
            "%",
            kpi_data['funding_success_rate']['trend'],
            kpi_data['funding_success_rate']['change'],
            "60%"
        ), lg=3, md=6, className="mb-3"),
        dbc.Col(create_kpi_card(
            "Conversion Rate",
            f"{kpi_data['conversion_rate']['value']:.1f}",
            "%",
            kpi_data['conversion_rate']['trend'],
            kpi_data['conversion_rate']['change'],
            "15%"
        ), lg=3, md=6, className="mb-3"),
        dbc.Col(create_kpi_card(
            "Time to Finality",
            f"{kpi_data['time_to_finality_days']['value']:.1f}",
            "days",
            kpi_data['time_to_finality_days']['trend'],
            kpi_data['time_to_finality_days']['change'],
            "14 days"
        ), lg=3, md=6, className="mb-3"),
        dbc.Col(create_kpi_card(
            "Avg Donation",
            f"${kpi_data['average_donation_size']['value']:.0f}",
            "",
            kpi_data['average_donation_size']['trend'],
            kpi_data['average_donation_size']['change'],
            "$100"
        ), lg=3, md=6, className="mb-3"),
    ])
    
    # System KPI Cards  
    system_kpi_cards = dbc.Row([
        dbc.Col(create_kpi_card(
            "Event Lag",
            f"{kpi_data['event_processing_lag']['value']:.1f}",
            "sec",
            kpi_data['event_processing_lag']['trend'],
            kpi_data['event_processing_lag']['change'],
            "<5s"
        ), lg=3, md=6, className="mb-3"),
        dbc.Col(create_kpi_card(
            "API Latency (P95)",
            f"{kpi_data['api_response_latency_p95']['value']:.0f}",
            "ms",
            kpi_data['api_response_latency_p95']['trend'],
            kpi_data['api_response_latency_p95']['change'],
            "<200ms"
        ), lg=3, md=6, className="mb-3"),
        dbc.Col(create_kpi_card(
            "Error Rate",
            f"{kpi_data['error_rate']['value']:.2f}",
            "%",
            kpi_data['error_rate']['trend'],
            kpi_data['error_rate']['change'],
            "<0.1%"
        ), lg=3, md=6, className="mb-3"),
        dbc.Col(create_kpi_card(
            "Suspicious TX",
            f"{kpi_data['suspicious_transaction_count']['value']}",
            "/day",
            kpi_data['suspicious_transaction_count']['trend'],
            kpi_data['suspicious_transaction_count']['change'],
            "<10"
        ), lg=3, md=6, className="mb-3"),
    ])
    
    # Donation Trend Chart
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=time_series['date'],
        y=time_series['donations'],
        mode='lines',
        name='Daily Donations',
        line=dict(color='#00bc8c', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 188, 140, 0.2)'
    ))
    fig_trend.update_layout(
        title='Donation Volume (Last 90 Days)',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis_title='Date',
        yaxis_title='Donation Volume ($)'
    )
    
    # Unique Donors Chart
    fig_donors = go.Figure()
    fig_donors.add_trace(go.Bar(
        x=time_series['date'],
        y=time_series['unique_donors'],
        name='Unique Donors',
        marker_color='#375a7f'
    ))
    fig_donors.update_layout(
        title='Unique Donors per Day',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis_title='Date',
        yaxis_title='Unique Donors'
    )
    
    return html.Div([
        html.H4("Business KPIs", className="mb-3"),
        business_kpi_cards,
        html.H4("System Monitoring KPIs", className="mb-3 mt-4"),
        system_kpi_cards,
        dbc.Row([
            dbc.Col(dbc.Card(dcc.Graph(figure=fig_trend)), lg=6, className="mb-3"),
            dbc.Col(dbc.Card(dcc.Graph(figure=fig_donors)), lg=6, className="mb-3"),
        ])
    ])


def create_model_performance_tab():
    """Create model performance layout"""
    model_data = generate_sample_model_performance()
    
    # Risk Scorer Performance
    risk_metrics = model_data['risk_scorer']
    fig_risk = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_metrics['auc_roc'] * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "AUC-ROC Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#00bc8c"},
            'steps': [
                {'range': [0, 50], 'color': "#e74c3c"},
                {'range': [50, 70], 'color': "#f39c12"},
                {'range': [70, 90], 'color': "#3498db"},
                {'range': [90, 100], 'color': "#00bc8c"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': 85
            }
        }
    ))
    fig_risk.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        height=250
    )
    
    # Model metrics table
    metrics_table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Model"),
            html.Th("Predictions/Day"),
            html.Th("Avg Latency"),
            html.Th("Key Metric"),
            html.Th("Status")
        ])),
        html.Tbody([
            html.Tr([
                html.Td("Risk Scorer"),
                html.Td(f"{risk_metrics['predictions_today']:,}"),
                html.Td(f"{risk_metrics['avg_latency_ms']:.1f}ms"),
                html.Td(f"AUC: {risk_metrics['auc_roc']:.2f}"),
                html.Td(dbc.Badge("Healthy", color="success"))
            ]),
            html.Tr([
                html.Td("Recommender"),
                html.Td(f"{model_data['recommender']['predictions_today']:,}"),
                html.Td(f"{model_data['recommender']['avg_latency_ms']:.1f}ms"),
                html.Td(f"CTR: {model_data['recommender']['click_through_rate']:.1%}"),
                html.Td(dbc.Badge("Healthy", color="success"))
            ]),
            html.Tr([
                html.Td("Outlier Detector"),
                html.Td(f"{model_data['outlier_detector']['anomalies_detected_today']}"),
                html.Td(f"{model_data['outlier_detector']['avg_latency_ms']:.1f}ms"),
                html.Td(f"F1: {model_data['outlier_detector']['f1_score']:.2f}"),
                html.Td(dbc.Badge("Healthy", color="success"))
            ]),
        ])
    ], bordered=True, hover=True, responsive=True, className="mb-4")
    
    # Latency distribution (simulated)
    np.random.seed(42)
    latencies = np.random.lognormal(2.5, 0.5, 1000)
    fig_latency = go.Figure()
    fig_latency.add_trace(go.Histogram(
        x=latencies,
        nbinsx=50,
        name='Latency Distribution',
        marker_color='#375a7f'
    ))
    fig_latency.add_vline(x=np.percentile(latencies, 95), 
                          line_dash="dash", line_color="red",
                          annotation_text="P95")
    fig_latency.update_layout(
        title='Model Latency Distribution (All Models)',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        xaxis_title='Latency (ms)',
        yaxis_title='Count'
    )
    
    return html.Div([
        html.H4("Model Performance Overview", className="mb-3"),
        metrics_table,
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5("Risk Scorer"),
                dcc.Graph(figure=fig_risk)
            ])), lg=4, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5("Latency Distribution"),
                dcc.Graph(figure=fig_latency)
            ])), lg=8, className="mb-3"),
        ])
    ])


def create_experiments_tab():
    """Create experiments layout"""
    exp_data = generate_sample_experiment_data()
    
    # Experiment cards
    exp_cards = []
    for exp_name, data in exp_data.items():
        variants = data.get('variants', {})
        
        # Create bar chart for variants
        fig = go.Figure()
        for variant_name, variant_data in variants.items():
            fig.add_trace(go.Bar(
                name=variant_name,
                x=[variant_name],
                y=[variant_data['rate'] * 100],
                text=[f"{variant_data['rate']*100:.1f}%"],
                textposition='outside'
            ))
        
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=200,
            showlegend=False,
            yaxis_title='Conversion Rate (%)',
            margin=dict(l=40, r=20, t=20, b=40)
        )
        
        status_color = 'success' if data.get('is_significant') else 'warning'
        sig_text = f"p={data['p_value']:.3f}" if 'p_value' in data else "N/A"
        
        card = dbc.Card([
            dbc.CardHeader([
                html.H5(exp_name.replace('_', ' ').title(), className="mb-0 d-inline"),
                dbc.Badge(data['status'].upper(), color=status_color, className="float-end")
            ]),
            dbc.CardBody([
                dcc.Graph(figure=fig, config={'displayModeBar': False}),
                html.Div([
                    html.Span(f"Running: {data['days_running']} days", className="me-3"),
                    html.Span(sig_text),
                    dbc.Badge("SIGNIFICANT" if data.get('is_significant') else "NOT SIGNIFICANT",
                             color="success" if data.get('is_significant') else "secondary",
                             className="ms-2")
                ], className="text-muted small")
            ])
        ], className="mb-3")
        
        exp_cards.append(dbc.Col(card, lg=6))
    
    return html.Div([
        html.H4("A/B Tests & Experiments", className="mb-3"),
        dbc.Row(exp_cards)
    ])


def create_clusters_tab():
    """Create donor clusters layout"""
    cluster_data = generate_sample_cluster_data()
    
    # Pie chart for segment distribution
    fig_pie = go.Figure(go.Pie(
        labels=cluster_data['segment'],
        values=cluster_data['count'],
        hole=0.4,
        marker=dict(colors=['#00bc8c', '#375a7f', '#f39c12', '#e74c3c'])
    ))
    fig_pie.update_layout(
        title='Donor Segments Distribution',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        height=350
    )
    
    # Bar chart for value contribution
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=cluster_data['segment'],
        y=cluster_data['total_value'],
        marker_color=['#00bc8c', '#375a7f', '#f39c12', '#e74c3c'],
        text=[f"${v:,.0f}" for v in cluster_data['total_value']],
        textposition='outside'
    ))
    fig_bar.update_layout(
        title='Total Value by Segment',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        yaxis_title='Total Value ($)'
    )
    
    # Segment table
    segment_table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Segment"),
            html.Th("Donor Count"),
            html.Th("Avg Donation"),
            html.Th("Total Value"),
            html.Th("Action")
        ])),
        html.Tbody([
            html.Tr([
                html.Td(row['segment']),
                html.Td(f"{row['count']:,}"),
                html.Td(f"${row['avg_donation']:,.2f}"),
                html.Td(f"${row['total_value']:,.2f}"),
                html.Td(dbc.Button("View", size="sm", color="primary"))
            ]) for _, row in cluster_data.iterrows()
        ])
    ], bordered=True, hover=True, responsive=True)
    
    return html.Div([
        html.H4("Donor Segmentation", className="mb-3"),
        dbc.Row([
            dbc.Col(dbc.Card(dcc.Graph(figure=fig_pie)), lg=6, className="mb-3"),
            dbc.Col(dbc.Card(dcc.Graph(figure=fig_bar)), lg=6, className="mb-3"),
        ]),
        dbc.Card(dbc.CardBody([
            html.H5("Segment Details"),
            segment_table
        ]))
    ])


# ============================================================
# MAIN LAYOUT
# ============================================================

app.layout = html.Div([
    create_navbar(),
    dbc.Container([
        dcc.Tabs(id='tabs', value='kpi', children=[
            dcc.Tab(label='KPI Overview', value='kpi'),
            dcc.Tab(label='Model Performance', value='models'),
            dcc.Tab(label='Experiments', value='experiments'),
            dcc.Tab(label='Donor Clusters', value='clusters'),
        ], className="mb-4"),
        html.Div(id='tab-content')
    ], fluid=True),
    html.Footer([
        html.Hr(),
        html.P(
            f"DonCoin DAO Data Science Dashboard • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            className="text-muted text-center"
        )
    ], className="mt-4")
])


# ============================================================
# CALLBACKS
# ============================================================

@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'value')
)
def render_tab(tab):
    if tab == 'kpi':
        return create_kpi_overview_tab()
    elif tab == 'models':
        return create_model_performance_tab()
    elif tab == 'experiments':
        return create_experiments_tab()
    elif tab == 'clusters':
        return create_clusters_tab()
    return html.P("Select a tab")


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == '__main__':
    print("Starting DonCoin DAO Data Science Dashboard...")
    print("Open http://localhost:8050 in your browser")
    app.run(debug=True, host='0.0.0.0', port=8050)
