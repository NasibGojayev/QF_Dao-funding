"""
Professional Security Operations Center Dashboard
Multi-section dashboard with Overview, Firewall, SIEM, and Django/Map sections
"""
import dash
from dash import dcc, html, callback, Input, Output, State, ALL, ctx
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

# Import data providers
try:
    from dashboard.data_provider import get_real_kpi_data, get_dashboard_stats, get_real_events
    from dashboard.firewall_data import (
        get_blacklist, get_whitelist, add_to_blacklist, add_to_whitelist,
        remove_from_blacklist, remove_from_whitelist, get_blocked_stats,
        get_blocked_requests, seed_sample_data as seed_firewall_data
    )
    from dashboard.siem_data import (
        search_logs, get_transaction_history, get_event_summary,
        get_security_alerts, export_logs, seed_sample_logs
    )
    from dashboard.geo_data import (
        get_connection_map_data, get_connection_stats, get_django_endpoint_stats,
        get_active_sessions, seed_sample_geo_data
    )
    DATA_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some data providers not available: {e}")
    DATA_AVAILABLE = False

# Initialize app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title='DonCoin DAO - Security Operations Center'
)

# =============================================================================
# NAVIGATION
# =============================================================================

def create_navbar():
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col(html.I(className="fas fa-shield-alt fa-2x text-primary"), width="auto"),
                dbc.Col(dbc.NavbarBrand("Security Operations Center", className="ms-2 fw-bold")),
            ], align="center", className="g-0"),
            dbc.Nav([
                dbc.NavItem(dbc.NavLink([html.I(className="fas fa-tachometer-alt me-2"), "Overview"], 
                                        href="#", id="nav-overview", active=True)),
                dbc.NavItem(dbc.NavLink([html.I(className="fas fa-fire-alt me-2"), "Firewall"], 
                                        href="#", id="nav-firewall")),
                dbc.NavItem(dbc.NavLink([html.I(className="fas fa-search me-2"), "SIEM"], 
                                        href="#", id="nav-siem")),
                dbc.NavItem(dbc.NavLink([html.I(className="fas fa-globe me-2"), "Django & Map"], 
                                        href="#", id="nav-geomap")),
            ], className="ms-auto", navbar=True),
            html.Div([
                dbc.Badge(id="alert-count-badge", color="danger", className="me-2"),
                dbc.Badge("● LIVE", color="success", className="pulse"),
            ])
        ], fluid=True),
        color="dark",
        dark=True,
        className="mb-3 shadow"
    )

# =============================================================================
# OVERVIEW SECTION
# =============================================================================

def create_overview_section():
    return html.Div([
        # Stats Row
        dbc.Row([
            dbc.Col(create_stat_card("Total Proposals", "proposals-count", "fas fa-file-alt", "primary"), lg=3, md=6),
            dbc.Col(create_stat_card("Total Donations", "donations-amount", "fas fa-donate", "success"), lg=3, md=6),
            dbc.Col(create_stat_card("Active Wallets", "wallets-count", "fas fa-wallet", "info"), lg=3, md=6),
            dbc.Col(create_stat_card("Blocked IPs", "blocked-count", "fas fa-ban", "danger"), lg=3, md=6),
        ], className="mb-4"),
        
        # KPIs Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-chart-line me-2"), "System KPIs"]),
                    dbc.CardBody(id="kpi-cards-container")
                ], className="h-100")
            ], lg=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-bell me-2"), "Active Alerts"]),
                    dbc.CardBody(id="alerts-panel", style={"maxHeight": "300px", "overflowY": "auto"})
                ], className="h-100")
            ], lg=4),
        ], className="mb-4"),
        
        # Charts Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-stream me-2"), "Recent Events"]),
                    dbc.CardBody(id="recent-events-table", style={"maxHeight": "400px", "overflowY": "auto"})
                ])
            ], lg=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-chart-area me-2"), "Event Timeline"]),
                    dbc.CardBody(dcc.Graph(id="events-timeline-chart", config={'displayModeBar': False}))
                ])
            ], lg=6),
        ]),
    ], id="overview-section")


def create_stat_card(title, id, icon, color):
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.I(className=f"{icon} fa-2x text-{color}"), width="auto"),
                dbc.Col([
                    html.H3(id=id, className="mb-0"),
                    html.Small(title, className="text-muted")
                ]),
            ], align="center")
        ])
    ], className=f"border-start border-{color} border-4")


# =============================================================================
# FIREWALL SECTION
# =============================================================================

def create_firewall_section():
    return html.Div([
        dbc.Row([
            # IP Management
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-plus-circle me-2"),
                        "Add IP to List"
                    ]),
                    dbc.CardBody([
                        dbc.InputGroup([
                            dbc.Input(id="ip-input", placeholder="Enter IP address..."),
                            dbc.Input(id="ip-reason", placeholder="Reason..."),
                            dbc.Select(id="ip-list-type", options=[
                                {"label": "Blacklist", "value": "blacklist"},
                                {"label": "Whitelist", "value": "whitelist"},
                            ], value="blacklist"),
                            dbc.Button([html.I(className="fas fa-plus")], id="add-ip-btn", color="primary"),
                        ], className="mb-3"),
                        html.Div(id="add-ip-feedback")
                    ])
                ], className="mb-3"),
                
                # Blacklist
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-ban me-2 text-danger"),
                        "Blacklist ",
                        dbc.Badge(id="blacklist-count", color="danger", className="ms-2")
                    ]),
                    dbc.CardBody(id="blacklist-table", style={"maxHeight": "300px", "overflowY": "auto"})
                ], className="mb-3"),
                
                # Whitelist
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-check-circle me-2 text-success"),
                        "Whitelist ",
                        dbc.Badge(id="whitelist-count", color="success", className="ms-2")
                    ]),
                    dbc.CardBody(id="whitelist-table", style={"maxHeight": "300px", "overflowY": "auto"})
                ]),
            ], lg=6),
            
            # Blocked Requests
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-shield-alt me-2"),
                        "Blocking Statistics"
                    ]),
                    dbc.CardBody(id="blocking-stats")
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-history me-2"),
                        "Recent Blocked Requests"
                    ]),
                    dbc.CardBody(id="blocked-requests-log", style={"maxHeight": "400px", "overflowY": "auto"})
                ]),
            ], lg=6),
        ]),
    ], id="firewall-section", style={"display": "none"})


# =============================================================================
# SIEM SECTION
# =============================================================================

def create_siem_section():
    return html.Div([
        # Search Bar
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.InputGroup([
                            dbc.InputGroupText(html.I(className="fas fa-search")),
                            dbc.Input(id="siem-search", placeholder="Search logs...", debounce=True),
                        ])
                    ], lg=4),
                    dbc.Col([
                        dbc.Select(id="siem-category", options=[
                            {"label": "All Categories", "value": ""},
                            {"label": "Authentication", "value": "authentication"},
                            {"label": "Admin Action", "value": "admin_action"},
                            {"label": "Data Access", "value": "data_access"},
                            {"label": "API Request", "value": "api_request"},
                            {"label": "Smart Contract", "value": "smart_contract"},
                        ], value="")
                    ], lg=2),
                    dbc.Col([
                        dbc.Select(id="siem-outcome", options=[
                            {"label": "All Outcomes", "value": ""},
                            {"label": "Success", "value": "success"},
                            {"label": "Failure", "value": "failure"},
                            {"label": "Blocked", "value": "blocked"},
                        ], value="")
                    ], lg=2),
                    dbc.Col([
                        dbc.Input(id="siem-ip-filter", placeholder="Filter by IP...")
                    ], lg=2),
                    dbc.Col([
                        dbc.Button([html.I(className="fas fa-download me-2"), "Export"], 
                                   id="export-logs-btn", color="secondary", className="w-100")
                    ], lg=2),
                ], className="g-2")
            ])
        ], className="mb-3"),
        
        dbc.Row([
            # Log Stream
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-stream me-2"),
                        "Log Stream ",
                        dbc.Badge(id="log-count", color="primary", className="ms-2")
                    ]),
                    dbc.CardBody(id="siem-log-stream", 
                                 style={"height": "500px", "overflowY": "auto", "fontFamily": "monospace", "fontSize": "0.85rem"})
                ])
            ], lg=8),
            
            # Side Panel
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-chart-pie me-2"), "Event Summary"]),
                    dbc.CardBody(dcc.Graph(id="siem-summary-chart", config={'displayModeBar': False}))
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-exchange-alt me-2"), "Transaction History"]),
                    dbc.CardBody(id="transaction-history", style={"maxHeight": "200px", "overflowY": "auto"})
                ]),
            ], lg=4),
        ]),
        
        # Download component
        dcc.Download(id="download-logs")
    ], id="siem-section", style={"display": "none"})


# =============================================================================
# GEO MAP SECTION
# =============================================================================

def create_geomap_section():
    return html.Div([
        dbc.Row([
            # Map
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-globe-americas me-2"),
                        "Geographic Connection Map"
                    ]),
                    dbc.CardBody(dcc.Graph(id="geo-map", config={'displayModeBar': False}, style={"height": "500px"}))
                ])
            ], lg=8),
            
            # Stats
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-flag me-2"), "Top Countries"]),
                    dbc.CardBody(id="top-countries", style={"maxHeight": "200px", "overflowY": "auto"})
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-city me-2"), "Top Cities"]),
                    dbc.CardBody(id="top-cities", style={"maxHeight": "200px", "overflowY": "auto"})
                ]),
            ], lg=4),
        ], className="mb-4"),
        
        dbc.Row([
            # Django Stats
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fab fa-python me-2"),
                        "Django API Endpoints"
                    ]),
                    dbc.CardBody(id="django-endpoints", style={"maxHeight": "300px", "overflowY": "auto"})
                ])
            ], lg=6),
            
            # Active Sessions
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-users me-2"),
                        "Active Sessions"
                    ]),
                    dbc.CardBody(id="active-sessions", style={"maxHeight": "300px", "overflowY": "auto"})
                ])
            ], lg=6),
        ]),
    ], id="geomap-section", style={"display": "none"})


# =============================================================================
# MAIN LAYOUT
# =============================================================================

app.layout = html.Div([
    create_navbar(),
    
    dbc.Container([
        # Auto-refresh
        dcc.Interval(id='refresh-interval', interval=10000, n_intervals=0),
        
        # Hidden store for current section
        dcc.Store(id='current-section', data='overview'),
        
        # All sections
        create_overview_section(),
        create_firewall_section(),
        create_siem_section(),
        create_geomap_section(),
        
    ], fluid=True, className="pb-4"),
    
    # Footer
    html.Footer([
        dbc.Container([
            html.Hr(),
            html.P([
                "DonCoin DAO Security Operations Center • ",
                html.Span(id='footer-time'),
                " • ",
                dbc.Badge("System Status: Healthy", color="success")
            ], className="text-muted text-center mb-0")
        ])
    ])
])


# =============================================================================
# CALLBACKS - NAVIGATION
# =============================================================================

@app.callback(
    [Output("overview-section", "style"),
     Output("firewall-section", "style"),
     Output("siem-section", "style"),
     Output("geomap-section", "style"),
     Output("nav-overview", "active"),
     Output("nav-firewall", "active"),
     Output("nav-siem", "active"),
     Output("nav-geomap", "active"),
     Output("current-section", "data")],
    [Input("nav-overview", "n_clicks"),
     Input("nav-firewall", "n_clicks"),
     Input("nav-siem", "n_clicks"),
     Input("nav-geomap", "n_clicks")],
    prevent_initial_call=True
)
def switch_section(n1, n2, n3, n4):
    triggered = ctx.triggered_id
    
    show = {"display": "block"}
    hide = {"display": "none"}
    
    if triggered == "nav-overview":
        return show, hide, hide, hide, True, False, False, False, "overview"
    elif triggered == "nav-firewall":
        return hide, show, hide, hide, False, True, False, False, "firewall"
    elif triggered == "nav-siem":
        return hide, hide, show, hide, False, False, True, False, "siem"
    elif triggered == "nav-geomap":
        return hide, hide, hide, show, False, False, False, True, "geomap"
    
    return show, hide, hide, hide, True, False, False, False, "overview"


# =============================================================================
# CALLBACKS - OVERVIEW
# =============================================================================

@app.callback(
    [Output("proposals-count", "children"),
     Output("donations-amount", "children"),
     Output("wallets-count", "children"),
     Output("blocked-count", "children"),
     Output("kpi-cards-container", "children"),
     Output("alerts-panel", "children"),
     Output("recent-events-table", "children"),
     Output("events-timeline-chart", "figure"),
     Output("alert-count-badge", "children"),
     Output("footer-time", "children")],
    Input("refresh-interval", "n_intervals")
)
def update_overview(n):
    # Get stats
    if DATA_AVAILABLE:
        stats = get_dashboard_stats()
        kpis = get_real_kpi_data()
        events = get_real_events(50)
        blocked = get_blocked_stats()
        alerts = get_security_alerts()
    else:
        stats = {"total_proposals": 0, "total_donations": 0, "total_donation_amount": 0, "active_wallets": 0}
        kpis = {}
        events = []
        blocked = {"blacklist_size": 0}
        alerts = []
    
    # Stats
    proposals = stats.get("total_proposals", 0)
    donations = f"${stats.get('total_donation_amount', 0):,.0f}"
    wallets = stats.get("active_wallets", 0)
    blocked_ips = blocked.get("blacklist_size", 0)
    
    # KPI cards
    kpi_cards = dbc.Row([
        dbc.Col(create_kpi_mini_card(k, v), md=6, lg=3) 
        for k, v in kpis.items()
    ]) if kpis else html.P("No KPI data", className="text-muted")
    
    # Alerts
    if alerts:
        alerts_content = html.Div([
            dbc.Alert([
                html.Strong(f"[{a.get('severity', 'info').upper()}] "),
                a.get("message", "Alert")
            ], color="danger" if a.get("severity") == "high" else "warning", className="mb-2 py-2")
            for a in alerts[:5]
        ])
    else:
        alerts_content = html.P("✓ No active alerts", className="text-success")
    
    # Events table
    events_table = create_events_table(events[:20])
    
    # Timeline chart
    timeline_fig = create_timeline_chart(events)
    
    # Alert badge
    alert_badge = f"{len(alerts)} Alerts" if alerts else "0 Alerts"
    
    # Footer time
    footer_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return proposals, donations, wallets, blocked_ips, kpi_cards, alerts_content, events_table, timeline_fig, alert_badge, footer_time


def create_kpi_mini_card(name, data):
    status_colors = {"ok": "success", "warning": "warning", "critical": "danger"}
    color = status_colors.get(data.get("status", "ok"), "secondary")
    config = MONITORING_KPIS.get(name, {})
    
    return dbc.Card([
        dbc.CardBody([
            html.H6(config.get("name", name), className="text-muted mb-1", style={"fontSize": "0.8rem"}),
            html.Div([
                html.Span(f"{data.get('value', 0)}", className="h4 mb-0"),
                html.Span(f" {config.get('unit', '')}", className="text-muted"),
                dbc.Badge("●", color=color, className="ms-2")
            ])
        ], className="py-2")
    ], className=f"border-start border-{color} border-3 mb-2")


def create_events_table(events):
    if not events:
        return html.P("No events", className="text-muted")
    
    rows = []
    for e in events:
        outcome = e.get("outcome", "success")
        color = "success" if outcome == "success" else "danger" if outcome == "failure" else "warning"
        rows.append(html.Tr([
            html.Td(e.get("timestamp", "")[:19], style={"fontSize": "0.8rem"}),
            html.Td(dbc.Badge(e.get("category", "")[:15], color="secondary")),
            html.Td(e.get("action", "")[:30], style={"fontSize": "0.85rem"}),
            html.Td(dbc.Badge(outcome, color=color, pill=True))
        ]))
    
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Time"), html.Th("Category"), html.Th("Action"), html.Th("")])),
        html.Tbody(rows)
    ], size="sm", hover=True, responsive=True)


def create_timeline_chart(events):
    if not events:
        return go.Figure()
    
    # Count events by hour
    df = pd.DataFrame(events)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["hour"] = df["timestamp"].dt.floor("H")
        counts = df.groupby("hour").size().reset_index(name="count")
        
        fig = px.area(counts, x="hour", y="count", 
                      color_discrete_sequence=["#00bc8c"])
    else:
        fig = go.Figure()
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=20, b=40),
        height=300,
        xaxis_title="",
        yaxis_title="Events"
    )
    
    return fig


# =============================================================================
# CALLBACKS - FIREWALL
# =============================================================================

@app.callback(
    [Output("blacklist-table", "children"),
     Output("whitelist-table", "children"),
     Output("blacklist-count", "children"),
     Output("whitelist-count", "children"),
     Output("blocking-stats", "children"),
     Output("blocked-requests-log", "children")],
    Input("refresh-interval", "n_intervals")
)
def update_firewall(n):
    if not DATA_AVAILABLE:
        empty = html.P("Data not available", className="text-muted")
        return empty, empty, 0, 0, empty, empty
    
    blacklist = get_blacklist()
    whitelist = get_whitelist()
    stats = get_blocked_stats()
    blocked_reqs = get_blocked_requests(50)
    
    # Blacklist table
    bl_table = create_ip_table(blacklist, "blacklist") if blacklist else html.P("No blocked IPs", className="text-muted")
    
    # Whitelist table
    wl_table = create_ip_table(whitelist, "whitelist") if whitelist else html.P("No whitelisted IPs", className="text-muted")
    
    # Stats
    stats_content = html.Div([
        dbc.Row([
            dbc.Col([html.H3(stats.get("total_blocked_24h", 0)), html.Small("Blocked (24h)")], className="text-center"),
            dbc.Col([html.H3(stats.get("blacklist_size", 0)), html.Small("Blacklisted")], className="text-center"),
            dbc.Col([html.H3(stats.get("whitelist_size", 0)), html.Small("Whitelisted")], className="text-center"),
        ])
    ])
    
    # Blocked requests
    blocked_log = create_blocked_log(blocked_reqs) if blocked_reqs else html.P("No blocked requests", className="text-muted")
    
    return bl_table, wl_table, len(blacklist), len(whitelist), stats_content, blocked_log


def create_ip_table(ips, list_type):
    rows = []
    for ip_data in ips[:20]:
        rows.append(html.Tr([
            html.Td(ip_data.get("ip", ""), style={"fontFamily": "monospace"}),
            html.Td(ip_data.get("reason", "")[:20]),
            html.Td(ip_data.get("added_at", "")[:10]),
            html.Td(dbc.Button(html.I(className="fas fa-times"), 
                               id={"type": f"remove-{list_type}", "ip": ip_data.get("ip")},
                               size="sm", color="danger", outline=True))
        ]))
    
    return dbc.Table([html.Tbody(rows)], size="sm", hover=True)


def create_blocked_log(requests):
    items = []
    for r in requests[:30]:
        items.append(html.Div([
            html.Span(r.get("timestamp", "")[:19], className="text-muted me-2", style={"fontSize": "0.8rem"}),
            html.Span(r.get("ip", ""), className="me-2", style={"fontFamily": "monospace"}),
            dbc.Badge(r.get("reason", "")[:20], color="warning")
        ], className="mb-1"))
    return html.Div(items)


@app.callback(
    Output("add-ip-feedback", "children"),
    Input("add-ip-btn", "n_clicks"),
    [State("ip-input", "value"), State("ip-reason", "value"), State("ip-list-type", "value")],
    prevent_initial_call=True
)
def add_ip(n_clicks, ip, reason, list_type):
    if not ip:
        return dbc.Alert("Please enter an IP address", color="warning", dismissable=True)
    
    if list_type == "blacklist":
        success = add_to_blacklist(ip, reason or "Manual block")
    else:
        success = add_to_whitelist(ip, reason or "Manual allow")
    
    if success:
        return dbc.Alert(f"Added {ip} to {list_type}", color="success", dismissable=True)
    else:
        return dbc.Alert(f"IP already in {list_type}", color="info", dismissable=True)


# =============================================================================
# CALLBACKS - SIEM
# =============================================================================

@app.callback(
    [Output("siem-log-stream", "children"),
     Output("log-count", "children"),
     Output("siem-summary-chart", "figure"),
     Output("transaction-history", "children")],
    [Input("refresh-interval", "n_intervals"),
     Input("siem-search", "value"),
     Input("siem-category", "value"),
     Input("siem-outcome", "value"),
     Input("siem-ip-filter", "value")]
)
def update_siem(n, query, category, outcome, ip_filter):
    if not DATA_AVAILABLE:
        empty = html.P("Data not available", className="text-muted")
        return empty, 0, go.Figure(), empty
    
    # Search logs
    logs = search_logs(
        query=query or "",
        category=category or "",
        outcome=outcome or "",
        source_ip=ip_filter or "",
        limit=200
    )
    
    # Log stream
    log_items = []
    for log in logs[:100]:
        outcome_val = log.get("outcome", "success")
        color = "#00bc8c" if outcome_val == "success" else "#e74c3c" if outcome_val == "failure" else "#f39c12"
        log_items.append(html.Div([
            html.Span(log.get("timestamp", "")[:19], style={"color": "#666"}),
            html.Span(f" [{log.get('source', 'log')}]", style={"color": "#3498db"}),
            html.Span(f" {log.get('category', '')}", style={"color": "#9b59b6"}),
            html.Span(f" {log.get('action', '')}", style={"color": color}),
            html.Span(f" {log.get('source_ip', log.get('ip', ''))}", style={"color": "#666"}),
        ], style={"borderBottom": "1px solid #333", "padding": "4px 0"}))
    
    # Summary chart
    summary = get_event_summary()
    by_cat = summary.get("by_category", {})
    if by_cat:
        fig = px.pie(values=list(by_cat.values()), names=list(by_cat.keys()),
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=20, b=20),
            height=200,
            showlegend=False
        )
    else:
        fig = go.Figure()
    
    # Transactions
    txs = get_transaction_history(20)
    if txs:
        tx_items = [html.Div([
            html.Span(t.get("timestamp", "")[:10], className="text-muted me-2"),
            dbc.Badge(f"${t.get('amount', 0):,.2f}", color="success"),
            html.Span(f" → {t.get('to', '')[:20]}", className="ms-1")
        ], className="mb-1") for t in txs[:10]]
    else:
        tx_items = [html.P("No transactions", className="text-muted")]
    
    return html.Div(log_items), len(logs), fig, html.Div(tx_items)


@app.callback(
    Output("download-logs", "data"),
    Input("export-logs-btn", "n_clicks"),
    [State("siem-search", "value"), State("siem-category", "value")],
    prevent_initial_call=True
)
def download_logs(n_clicks, query, category):
    content = export_logs(format="json", query=query or "", category=category or "", limit=1000)
    return dict(content=content, filename=f"security_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")


# =============================================================================
# CALLBACKS - GEO MAP
# =============================================================================

@app.callback(
    [Output("geo-map", "figure"),
     Output("top-countries", "children"),
     Output("top-cities", "children"),
     Output("django-endpoints", "children"),
     Output("active-sessions", "children")],
    Input("refresh-interval", "n_intervals")
)
def update_geomap(n):
    if not DATA_AVAILABLE:
        empty = html.P("Data not available", className="text-muted")
        return go.Figure(), empty, empty, empty, empty
    
    # Map
    map_data = get_connection_map_data()
    if map_data.get("lats"):
        fig = go.Figure(go.Scattergeo(
            lat=map_data["lats"],
            lon=map_data["lons"],
            mode="markers",
            marker=dict(
                size=map_data["sizes"],
                color=map_data["colors"],
                colorscale="Viridis",
                showscale=True
            ),
            text=map_data["texts"],
            hoverinfo="text"
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            geo=dict(
                bgcolor="rgba(0,0,0,0)",
                showland=True,
                landcolor="#1a1a2e",
                showocean=True,
                oceancolor="#0d1117",
                showcoastlines=True,
                coastlinecolor="#333",
                projection_type="natural earth"
            ),
            margin=dict(l=0, r=0, t=0, b=0)
        )
    else:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(text="No geographic data yet", showarrow=False, font=dict(size=16, color="#666"))]
        )
    
    # Stats
    stats = get_connection_stats()
    
    countries = html.Div([
        html.Div([
            html.Span(f"{c['country']}", className="me-2"),
            dbc.Badge(c["count"], color="primary")
        ], className="mb-1") for c in stats.get("top_countries", [])[:10]
    ]) if stats.get("top_countries") else html.P("No data", className="text-muted")
    
    cities = html.Div([
        html.Div([
            html.Span(f"{c['city']}", className="me-2"),
            dbc.Badge(c["count"], color="info")
        ], className="mb-1") for c in stats.get("top_cities", [])[:10]
    ]) if stats.get("top_cities") else html.P("No data", className="text-muted")
    
    # Django endpoints
    django = get_django_endpoint_stats()
    if django.get("endpoints"):
        endpoint_rows = [html.Tr([
            html.Td(e["endpoint"][:30], style={"fontFamily": "monospace", "fontSize": "0.8rem"}),
            html.Td(e["requests"]),
            html.Td(f"{e['avg_response_ms']:.0f}ms"),
            html.Td(dbc.Badge(f"{e['error_rate']}%", color="danger" if e["error_rate"] > 5 else "success"))
        ]) for e in django["endpoints"][:15]]
        endpoints_table = dbc.Table([
            html.Thead(html.Tr([html.Th("Endpoint"), html.Th("Reqs"), html.Th("Avg"), html.Th("Err")])),
            html.Tbody(endpoint_rows)
        ], size="sm", hover=True)
    else:
        endpoints_table = html.P("No Django requests logged yet", className="text-muted")
    
    # Sessions
    sessions = get_active_sessions()
    if sessions:
        session_items = [html.Div([
            html.I(className="fas fa-user me-2 text-success"),
            html.Span(s.get("user", "anonymous"), className="me-2"),
            html.Small(f"({s.get('ip', '')})", className="text-muted me-2"),
            html.Small(s.get("location", ""), className="text-muted")
        ], className="mb-2") for s in sessions[:10]]
    else:
        session_items = [html.P("No active sessions", className="text-muted")]
    
    return fig, countries, cities, endpoints_table, html.Div(session_items)


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
                box-shadow: 0 2px 15px rgba(0,0,0,0.3);
            }
            .card-header {
                background: rgba(255,255,255,0.05);
                border-bottom: 1px solid rgba(255,255,255,0.1);
                font-weight: 600;
            }
            ::-webkit-scrollbar {
                width: 8px;
            }
            ::-webkit-scrollbar-track {
                background: #1a1a2e;
            }
            ::-webkit-scrollbar-thumb {
                background: #444;
                border-radius: 4px;
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
# RUN
# =============================================================================

if __name__ == '__main__':
    # NOTE: No sample data seeding - dashboard uses real data only
    # Real data sources:
    # - PostgreSQL: proposals, donations, wallets, contract events
    # - Django middleware: request logs, security events
    # - Firewall: actual blocked IPs (managed through UI)
    
    print("=" * 60)
    print("  DonCoin DAO - Security Operations Center")
    print("=" * 60)
    print("Data Sources:")
    print("  ✓ PostgreSQL database (proposals, donations, wallets)")
    print("  ✓ Contract events from blockchain indexer")
    print("  ✓ Django request logs (via middleware)")
    print("  ✓ Security events (authentication, admin actions)")
    print("")
    print(f"Open http://localhost:{DASHBOARD_CONFIG['port']} in your browser")
    print("=" * 60)
    
    app.run(
        debug=DASHBOARD_CONFIG['debug'],
        host=DASHBOARD_CONFIG['host'],
        port=DASHBOARD_CONFIG['port']
    )
