"""
Security Monitoring Dashboard for DonCoin DAO
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

from config.settings import MONITORING_KPIS, DASHBOARD_CONFIG, LOGS_DIR

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],  # Dark cybersecurity theme
    suppress_callback_exceptions=True,
    title='DonCoin DAO - Security Operations Center'
)

# =============================================================================
# SAMPLE DATA GENERATORS
# =============================================================================

def generate_sample_kpi_data():
    """Generate sample KPI data"""
    return {
        'event_processing_lag': {'value': 2.3, 'status': 'ok', 'trend': 'stable'},
        'error_rate': {'value': 0.08, 'status': 'ok', 'trend': 'down'},
        'api_response_latency': {'value': 145, 'status': 'ok', 'trend': 'stable'},
        'suspicious_tx_count': {'value': 3, 'status': 'warning', 'trend': 'up'},
    }


def generate_sample_alerts():
    """Generate sample alert data"""
    return [
        {
            'id': 'ALT-001',
            'name': 'High Event Processing Lag',
            'severity': 'critical',
            'status': 'firing',
            'value': 75.2,
            'fired_at': (datetime.now() - timedelta(minutes=15)).strftime('%H:%M:%S'),
            'acknowledged': False
        },
        {
            'id': 'ALT-002',
            'name': 'Elevated Error Rate',
            'severity': 'warning',
            'status': 'resolved',
            'value': 2.5,
            'fired_at': (datetime.now() - timedelta(hours=2)).strftime('%H:%M:%S'),
            'acknowledged': True
        },
    ]


def generate_sample_events():
    """Generate sample security events"""
    events = []
    categories = ['authentication', 'rate_limit', 'admin_action', 'suspicious_activity']
    outcomes = ['success', 'failure', 'blocked']
    
    for i in range(50):
        events.append({
            'timestamp': (datetime.now() - timedelta(minutes=i*5)).strftime('%Y-%m-%d %H:%M:%S'),
            'category': np.random.choice(categories),
            'source_ip': f'192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}',
            'action': np.random.choice(['login', 'api_call', 'data_access', 'config_change']),
            'outcome': np.random.choice(outcomes, p=[0.7, 0.2, 0.1])
        })
    
    return events


def generate_sample_cases():
    """Generate sample security cases"""
    return [
        {
            'case_id': 'CASE-001',
            'title': 'Brute Force Detection',
            'severity': 'high',
            'status': 'investigating',
            'created_at': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M'),
            'events': 12
        },
        {
            'case_id': 'CASE-002',
            'title': 'Rate Limit Abuse',
            'severity': 'medium',
            'status': 'new',
            'created_at': (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M'),
            'events': 8
        }
    ]


def generate_sample_rate_limit_data():
    """Generate sample rate limit data"""
    times = pd.date_range(end=datetime.now(), periods=24, freq='H')
    return pd.DataFrame({
        'time': times,
        'total_requests': np.random.randint(500, 2000, 24),
        'blocked_requests': np.random.randint(0, 50, 24),
    })


# =============================================================================
# LAYOUT COMPONENTS
# =============================================================================

def create_kpi_card(name, value, unit, status, config):
    """Create a KPI status card"""
    status_colors = {
        'ok': 'success',
        'warning': 'warning',
        'critical': 'danger'
    }
    
    status_icons = {
        'ok': '✓',
        'warning': '⚠',
        'critical': '✕'
    }
    
    color = status_colors.get(status, 'secondary')
    icon = status_icons.get(status, '?')
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                dbc.Badge(icon, color=color, className="float-end fs-5"),
                html.H6(name, className="text-muted mb-1", style={'fontSize': '0.8rem'}),
            ]),
            html.Div([
                html.Span(f"{value}", className="h3 mb-0 me-1"),
                html.Span(unit, className="text-muted small"),
            ]),
            html.Div([
                html.Small(f"Target: {config['target']}{unit}", className="text-muted"),
                html.Progress(
                    value=min(100, (value / config['critical_threshold']) * 100),
                    max=100,
                    className="mt-2",
                    style={'height': '4px'}
                )
            ], className="mt-2")
        ])
    ], className="h-100 border-start border-" + color + " border-3")


def create_alert_row(alert):
    """Create an alert row for the table"""
    severity_colors = {
        'critical': 'danger',
        'warning': 'warning',
        'info': 'info'
    }
    
    status_badge = dbc.Badge(
        alert['status'].upper(),
        color='danger' if alert['status'] == 'firing' else 'success',
        className="me-2"
    )
    
    severity_badge = dbc.Badge(
        alert['severity'].upper(),
        color=severity_colors.get(alert['severity'], 'secondary')
    )
    
    return html.Tr([
        html.Td(status_badge),
        html.Td(alert['name']),
        html.Td(severity_badge),
        html.Td(f"{alert['value']:.1f}"),
        html.Td(alert['fired_at']),
        html.Td(
            dbc.Button("ACK", size="sm", color="secondary", outline=True)
            if not alert['acknowledged'] else html.Span("✓", className="text-success")
        )
    ])


def create_navbar():
    """Create navigation bar"""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Span("🛡️", style={'fontSize': '1.5rem'}), width="auto"),
                dbc.Col(dbc.NavbarBrand("Security Operations Center", className="ms-2")),
            ], align="center", className="g-0"),
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Dashboard", href="#", active=True)),
                dbc.NavItem(dbc.NavLink("Alerts", href="#")),
                dbc.NavItem(dbc.NavLink("Events", href="#")),
                dbc.NavItem(dbc.NavLink("Cases", href="#")),
            ], className="ms-auto", navbar=True),
            html.Div([
                dbc.Badge("2 Active Alerts", color="danger", className="me-2"),
                dbc.Badge("LIVE", color="success", className="pulse"),
            ])
        ], fluid=True),
        color="dark",
        dark=True,
        className="mb-4"
    )


def create_kpi_section():
    """Create KPI overview section"""
    kpi_data = generate_sample_kpi_data()
    
    cards = []
    for kpi_id, data in kpi_data.items():
        config = MONITORING_KPIS.get(kpi_id, {})
        cards.append(
            dbc.Col(
                create_kpi_card(
                    config.get('name', kpi_id),
                    data['value'],
                    config.get('unit', ''),
                    data['status'],
                    config
                ),
                lg=3, md=6, className="mb-3"
            )
        )
    
    return dbc.Row(cards)


def create_alerts_section():
    """Create alerts panel"""
    alerts = generate_sample_alerts()
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Active Alerts", className="mb-0 d-inline"),
            dbc.Badge(
                len([a for a in alerts if a['status'] == 'firing']),
                color="danger",
                className="ms-2"
            )
        ]),
        dbc.CardBody([
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Status"),
                    html.Th("Alert"),
                    html.Th("Severity"),
                    html.Th("Value"),
                    html.Th("Time"),
                    html.Th("Action")
                ])),
                html.Tbody([create_alert_row(a) for a in alerts])
            ], bordered=True, hover=True, responsive=True, size="sm")
        ])
    ])


def create_events_timeline():
    """Create security events timeline chart"""
    events = generate_sample_events()
    df = pd.DataFrame(events)
    
    # Count by category and time
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.floor('H')
    
    summary = df.groupby(['hour', 'category']).size().reset_index(name='count')
    
    fig = px.area(
        summary,
        x='hour',
        y='count',
        color='category',
        title='Security Events (Last 24h)',
        color_discrete_sequence=['#00bc8c', '#f39c12', '#e74c3c', '#3498db']
    )
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    return dbc.Card([
        dbc.CardBody(dcc.Graph(figure=fig, config={'displayModeBar': False}))
    ])


def create_rate_limit_chart():
    """Create rate limit monitoring chart"""
    df = generate_sample_rate_limit_data()
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=df['time'],
            y=df['total_requests'],
            name='Total Requests',
            marker_color='#375a7f',
            opacity=0.7
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['time'],
            y=df['blocked_requests'],
            name='Blocked',
            line=dict(color='#e74c3c', width=2),
            mode='lines+markers'
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title='Rate Limiting Activity',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    fig.update_yaxes(title_text="Total Requests", secondary_y=False)
    fig.update_yaxes(title_text="Blocked", secondary_y=True)
    
    return dbc.Card([
        dbc.CardBody(dcc.Graph(figure=fig, config={'displayModeBar': False}))
    ])


def create_cases_section():
    """Create security cases panel"""
    cases = generate_sample_cases()
    
    severity_colors = {
        'critical': 'danger',
        'high': 'warning',
        'medium': 'info',
        'low': 'secondary'
    }
    
    status_colors = {
        'new': 'primary',
        'investigating': 'warning',
        'contained': 'info',
        'resolved': 'success'
    }
    
    case_cards = []
    for case in cases:
        case_cards.append(
            dbc.Card([
                dbc.CardHeader([
                    dbc.Badge(case['severity'].upper(), color=severity_colors.get(case['severity'], 'secondary'), className="me-2"),
                    html.Strong(case['case_id']),
                ]),
                dbc.CardBody([
                    html.H6(case['title']),
                    html.P([
                        html.Small(f"Created: {case['created_at']} | Events: {case['events']}", className="text-muted")
                    ]),
                    dbc.Badge(case['status'].upper(), color=status_colors.get(case['status'], 'secondary'))
                ])
            ], className="mb-2")
        )
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Security Cases", className="mb-0 d-inline"),
            dbc.Badge(len(cases), color="warning", className="ms-2")
        ]),
        dbc.CardBody(case_cards if case_cards else html.P("No open cases", className="text-muted"))
    ])


def create_threat_summary():
    """Create threat summary gauge"""
    # Calculate overall threat level (0-100)
    threat_level = 35  # Example
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=threat_level,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Threat Level", 'font': {'size': 16}},
        delta={'reference': 25, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "#f39c12"},
            'steps': [
                {'range': [0, 25], 'color': "#00bc8c"},
                {'range': [25, 50], 'color': "#f39c12"},
                {'range': [50, 75], 'color': "#fd7e14"},
                {'range': [75, 100], 'color': "#e74c3c"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return dbc.Card([
        dbc.CardBody(dcc.Graph(figure=fig, config={'displayModeBar': False}))
    ])


def create_recent_events_table():
    """Create recent events table"""
    events = generate_sample_events()[:10]
    
    outcome_colors = {
        'success': 'success',
        'failure': 'danger',
        'blocked': 'warning'
    }
    
    rows = []
    for event in events:
        rows.append(html.Tr([
            html.Td(event['timestamp'].split(' ')[1], style={'fontSize': '0.8rem'}),
            html.Td(event['source_ip'], style={'fontFamily': 'monospace', 'fontSize': '0.8rem'}),
            html.Td(dbc.Badge(event['category'], color='secondary', className="text-truncate")),
            html.Td(event['action']),
            html.Td(dbc.Badge(event['outcome'], color=outcome_colors.get(event['outcome'], 'secondary'), pill=True))
        ]))
    
    return dbc.Card([
        dbc.CardHeader([
            html.H6("Recent Events", className="mb-0 d-inline"),
            html.Small(" (Last 10)", className="text-muted")
        ]),
        dbc.CardBody([
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Time"),
                    html.Th("Source"),
                    html.Th("Category"),
                    html.Th("Action"),
                    html.Th("Outcome")
                ])),
                html.Tbody(rows)
            ], bordered=True, hover=True, responsive=True, size="sm", striped=True)
        ])
    ])


# =============================================================================
# MAIN LAYOUT
# =============================================================================

app.layout = html.Div([
    create_navbar(),
    
    dbc.Container([
        # Auto-refresh
        dcc.Interval(
            id='interval-component',
            interval=DASHBOARD_CONFIG['refresh_interval_ms'],
            n_intervals=0
        ),
        
        # KPIs Row
        html.H5("System KPIs", className="mb-3"),
        create_kpi_section(),
        
        # Main content row
        dbc.Row([
            # Left column - Alerts and Cases
            dbc.Col([
                create_alerts_section(),
                html.Div(className="mb-3"),
                create_cases_section(),
            ], lg=4),
            
            # Right column - Charts
            dbc.Col([
                create_events_timeline(),
                html.Div(className="mb-3"),
                dbc.Row([
                    dbc.Col(create_threat_summary(), lg=5),
                    dbc.Col(create_recent_events_table(), lg=7),
                ])
            ], lg=8),
        ], className="mb-4"),
        
        # Rate limiting row
        dbc.Row([
            dbc.Col(create_rate_limit_chart(), lg=12)
        ])
        
    ], fluid=True),
    
    # Footer
    html.Footer([
        html.Hr(),
        html.P([
            "Security Operations Center • ",
            html.Span(id='current-time'),
            " • ",
            dbc.Badge("System Healthy", color="success")
        ], className="text-muted text-center")
    ], className="mt-4")
])


# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    Output('current-time', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_time(n):
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# =============================================================================
# CUSTOM CSS
# =============================================================================

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .pulse {
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            .card {
                border: none;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }
            progress {
                width: 100%;
                -webkit-appearance: none;
                appearance: none;
            }
            progress::-webkit-progress-bar {
                background-color: #333;
                border-radius: 2px;
            }
            progress::-webkit-progress-value {
                background-color: #00bc8c;
                border-radius: 2px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == '__main__':
    print("Starting Security Operations Center Dashboard...")
    print(f"Open http://localhost:{DASHBOARD_CONFIG['port']} in your browser")
    app.run(
        debug=DASHBOARD_CONFIG['debug'],
        host=DASHBOARD_CONFIG['host'],
        port=DASHBOARD_CONFIG['port']
    )
