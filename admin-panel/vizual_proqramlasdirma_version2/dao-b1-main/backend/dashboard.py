"""
Sprint 3: Dash-based Monitoring Dashboard
Real-time KPI visualization, alerts, and SOC/SOAR workflows
"""

import dash
from dash import dcc, html, callback, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import datetime

# Import monitoring module
from monitoring import inference_logger

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "DAO Monitoring Dashboard"

# Simulated metrics for demo
def generate_kpi_timeseries():
    """Generate time series data for KPI trends"""
    times = pd.date_range(end=datetime.now(), periods=60, freq='1min')
    return pd.DataFrame({
        'timestamp': times,
        'event_lag_seconds': np.random.normal(35, 10, 60),
        'error_rate_percent': np.random.normal(0.5, 0.2, 60),
        'api_latency_ms': np.random.normal(150, 50, 60),
        'suspicious_count': np.random.poisson(5, 60),
        'conversion_rate': np.random.normal(6.5, 1, 60),
    })

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("📊 DAO Quadratic Funding - Monitoring Dashboard", 
                   className="mb-4 mt-4 text-center text-light")
        ])
    ]),
    
    # KPI Cards Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Event Processing Lag", className="card-title"),
                    html.H2(id="lag-value", children="--", className="text-warning"),
                    html.P("seconds", className="text-muted")
                ])
            ], className="bg-dark")
        ], md=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Error Rate", className="card-title"),
                    html.H2(id="error-value", children="--", className="text-danger"),
                    html.P("percent", className="text-muted")
                ])
            ], className="bg-dark")
        ], md=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("API Latency P95", className="card-title"),
                    html.H2(id="latency-value", children="--", className="text-info"),
                    html.P("milliseconds", className="text-muted")
                ])
            ], className="bg-dark")
        ], md=4),
    ], className="mb-4"),
    
    # Alerts Section
    dbc.Row([
        dbc.Col([
            html.H3("🚨 Active Alerts", className="text-light mb-3"),
            html.Div(id="alerts-container", children=[
                dbc.Alert("✅ No active critical alerts", color="success")
            ])
        ])
    ], className="mb-4"),
    
    # Charts Row 1
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="lag-timeline")
        ], md=6),
        dbc.Col([
            dcc.Graph(id="error-timeline")
        ], md=6),
    ], className="mb-4"),
    
    # Charts Row 2
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="latency-timeline")
        ], md=6),
        dbc.Col([
            dcc.Graph(id="suspicious-timeline")
        ], md=6),
    ], className="mb-4"),
    
    # Conversion Rate
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="conversion-timeline")
        ])
    ], className="mb-4"),
    
    # Model Inference Log
    dbc.Row([
        dbc.Col([
            html.H3("📋 Recent Model Inferences", className="text-light mb-3"),
            html.Div(id="inference-table-container")
        ])
    ], className="mb-4"),
    
    # Alert Configuration
    dbc.Row([
        dbc.Col([
            html.H3("⚙️ Alert Configuration", className="text-light mb-3"),
            html.Div([
                html.Div([
                    dbc.Label("Event Lag Threshold (seconds):", className="text-light"),
                    dbc.Input(
                        id="lag-threshold-input",
                        type="number",
                        value=60,
                        className="bg-secondary text-light"
                    )
                ]),
                html.Div([
                    dbc.Label("Error Rate Threshold (%):", className="text-light"),
                    dbc.Input(
                        id="error-threshold-input",
                        type="number",
                        value=2.0,
                        step=0.1,
                        className="bg-secondary text-light"
                    )
                ]),
                dbc.Button("Save Configuration", id="save-config-btn", color="primary")
            ])
        ], md=6),
        
        dbc.Col([
            html.H3("📈 A/B Test Status", className="text-light mb-3"),
            dcc.Graph(id="ab-test-chart")
        ], md=6),
    ], className="mb-4"),
    
    # Refresh interval
    dcc.Interval(id="refresh-interval", interval=5000, n_intervals=0),
    
], fluid=True, className="bg-dark", style={"minHeight": "100vh"})


@callback(
    [Output("lag-value", "children"),
     Output("error-value", "children"),
     Output("latency-value", "children"),
     Output("lag-timeline", "figure"),
     Output("error-timeline", "figure"),
     Output("latency-timeline", "figure"),
     Output("suspicious-timeline", "figure"),
     Output("conversion-timeline", "figure"),
     Output("alerts-container", "children"),
     Output("inference-table-container", "children"),
     Output("ab-test-chart", "figure")],
    Input("refresh-interval", "n_intervals")
)
def update_dashboard(n):
    """Update all dashboard elements"""
    
    # Generate timeseries
    df = generate_kpi_timeseries()
    
    # Get current values
    lag_current = df['event_lag_seconds'].iloc[-1]
    error_current = df['error_rate_percent'].iloc[-1]
    latency_p95 = df['api_latency_ms'].quantile(0.95)
    
    # Check alerts
    alerts_html = []
    if lag_current > 60:
        alerts_html.append(
            dbc.Alert([
                html.Strong("🚨 CRITICAL: "),
                f"Event processing lag ({lag_current:.1f}s) exceeds threshold (60s)"
            ], color="danger", dismissable=True)
        )
    if error_current > 2.0:
        alerts_html.append(
            dbc.Alert([
                html.Strong("⚠️ WARNING: "),
                f"Error rate ({error_current:.2f}%) exceeds threshold (2.0%)"
            ], color="warning", dismissable=True)
        )
    
    if not alerts_html:
        alerts_html = [dbc.Alert("✅ All systems nominal", color="success")]
    
    # Timeline figures
    fig_lag = go.Figure()
    fig_lag.add_trace(go.Scatter(x=df['timestamp'], y=df['event_lag_seconds'], mode='lines', name='Lag'))
    fig_lag.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="Threshold")
    fig_lag.update_layout(
        title="Event Processing Lag Over Time",
        xaxis_title="Time",
        yaxis_title="Seconds",
        template="plotly_dark",
        hovermode="x unified"
    )
    
    fig_error = go.Figure()
    fig_error.add_trace(go.Scatter(x=df['timestamp'], y=df['error_rate_percent'], mode='lines', name='Error Rate'))
    fig_error.add_hline(y=2.0, line_dash="dash", line_color="red", annotation_text="Threshold")
    fig_error.update_layout(
        title="Error Rate Over Time",
        xaxis_title="Time",
        yaxis_title="Percentage (%)",
        template="plotly_dark",
        hovermode="x unified"
    )
    
    fig_latency = go.Figure()
    fig_latency.add_trace(go.Scatter(x=df['timestamp'], y=df['api_latency_ms'], mode='lines', name='Latency'))
    fig_latency.update_layout(
        title="API Latency Over Time",
        xaxis_title="Time",
        yaxis_title="Milliseconds",
        template="plotly_dark",
        hovermode="x unified"
    )
    
    fig_suspicious = go.Figure()
    fig_suspicious.add_trace(go.Bar(x=df['timestamp'], y=df['suspicious_count'], name='Suspicious Count'))
    fig_suspicious.update_layout(
        title="Suspicious Transactions Flagged",
        xaxis_title="Time",
        yaxis_title="Count",
        template="plotly_dark",
        hovermode="x unified"
    )
    
    fig_conversion = go.Figure()
    fig_conversion.add_trace(go.Scatter(x=df['timestamp'], y=df['conversion_rate'], mode='lines+markers', name='Conversion %'))
    fig_conversion.update_layout(
        title="Conversion Rate Over Time",
        xaxis_title="Time",
        yaxis_title="Percentage (%)",
        template="plotly_dark",
        hovermode="x unified"
    )
    
    # Model inference table
    inferences = inference_logger.get_recent_inferences(limit=5)
    if inferences:
        inference_df = pd.DataFrame([
            {
                'Timestamp': i['timestamp'][:19],
                'Model': i['model_name'],
                'Score': f"{i['score']:.3f}",
                'Latency (ms)': f"{i['latency_ms']:.2f}"
            }
            for i in inferences
        ])
        inference_table = dash_table.DataTable(
            data=inference_df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in inference_df.columns],
            style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
            style_header={'backgroundColor': 'rgb(100, 100, 100)', 'fontWeight': 'bold'}
        )
    else:
        inference_table = html.P("No inferences logged yet", className="text-muted")
    
    # A/B test chart
    ab_data = {
        'Variant': ['Baseline', 'Variant A\n(Recommend)', 'Variant B\n(Cluster)'],
        'Conversion Rate (%)': [5.0, 8.2, 6.1],
        'Users': [150, 160, 155]
    }
    fig_ab = px.bar(ab_data, x='Variant', y='Conversion Rate (%)', 
                    title='A/B Test Results',
                    template='plotly_dark')
    fig_ab.update_layout(showlegend=False)
    
    return (
        f"{lag_current:.1f}s",
        f"{error_current:.2f}%",
        f"{latency_p95:.1f}ms",
        fig_lag,
        fig_error,
        fig_latency,
        fig_suspicious,
        fig_conversion,
        alerts_html,
        inference_table,
        fig_ab
    )


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8002)
