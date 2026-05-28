"""
GreenChain Electronics – Sustainability Intelligence System
Full Dash Dashboard (Steps 1, 2, 3)

Run:  python src/dashboard.py
Open: http://127.0.0.1:8050
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, dash_table, Input, Output
import dash_bootstrap_components as dbc

from step1_supplier_risk import load_suppliers, compute_risk_score, top_non_compliant, summary_by_segment
from step2_esg_reporting import (build_dim_time, build_dim_factory, build_dim_supplier,
                                   build_fact_table, compute_kpis, supplier_compliance_rate)
from step3_monitoring import (evaluate_alerts_emissions, evaluate_supplier_alerts,
                               traffic_light, generate_decision_memo, ALERT_RULES)

# ─────────────────────────────────────────────
# DATA PREP
# ─────────────────────────────────────────────
df_sup  = compute_risk_score(load_suppliers())
dim_time = build_dim_time()
dim_fact = build_dim_factory()
fact     = build_fact_table()
kpis     = compute_kpis(fact, dim_time)
em_alerts = evaluate_alerts_emissions(fact, dim_time)
su_alerts = evaluate_supplier_alerts(df_sup)
compliance_rate = supplier_compliance_rate()
memo = generate_decision_memo(df_sup, em_alerts, su_alerts, kpis)

FACTORY_NAMES = {1: "Kyiv Assembly", 2: "Warsaw Component Hub", 3: "Tallinn R&D"}

# ─────────────────────────────────────────────
# COLOR CONSTANTS
# ─────────────────────────────────────────────
GREEN  = "#2ecc71"
AMBER  = "#f39c12"
RED    = "#e74c3c"
BLUE   = "#3498db"
DARK   = "#1a1a2e"
CARD   = "#16213e"
TEXT   = "#ecf0f1"
MUTED  = "#95a5a6"

SEG_COLORS = {"low": GREEN, "medium": AMBER, "high": RED}
TL_COLORS  = {"GREEN": GREEN, "AMBER": AMBER, "RED": RED, "GREY": MUTED}

def tl_badge(status: str, label: str) -> html.Div:
    color = TL_COLORS.get(status, MUTED)
    return html.Div([
        html.Div(style={
            "width": "14px", "height": "14px", "borderRadius": "50%",
            "backgroundColor": color, "display": "inline-block",
            "marginRight": "8px", "verticalAlign": "middle",
            "boxShadow": f"0 0 8px {color}",
        }),
        html.Span(label, style={"color": TEXT, "fontSize": "13px"}),
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"})


def kpi_card(title, value, sub="", color=BLUE):
    return dbc.Card([
        dbc.CardBody([
            html.P(title, style={"color": MUTED, "fontSize": "12px", "margin": "0"}),
            html.H3(value, style={"color": color, "margin": "4px 0", "fontWeight": "700"}),
            html.P(sub,   style={"color": MUTED, "fontSize": "11px", "margin": "0"}),
        ])
    ], style={"backgroundColor": CARD, "border": f"1px solid {color}33",
              "borderRadius": "10px", "textAlign": "center"})


# ─────────────────────────────────────────────
# FIGURES
# ─────────────────────────────────────────────

def fig_risk_heatmap():
    df = df_sup.copy()
    df["seg_color"] = df["Risk_Segment"].map(SEG_COLORS)
    fig = px.scatter(
        df, x="EcoVadis", y="Labor Audit Score",
        size="ESG_Risk_Score", color="Risk_Segment",
        color_discrete_map=SEG_COLORS,
        hover_name="Supplier",
        hover_data={"Country": True, "ESG_Risk_Score": True,
                    "Incident History": True, "Certification Status": True},
        title="Supplier Risk Heatmap – EcoVadis vs Labor Audit",
        labels={"EcoVadis": "EcoVadis Score (higher = better)",
                "Labor Audit Score": "Labor Audit Score"},
    )
    fig.update_layout(paper_bgcolor=DARK, plot_bgcolor=CARD,
                      font_color=TEXT, legend_title="Risk Segment")
    return fig


def fig_radar(supplier_name: str):
    row = df_sup[df_sup["Supplier"] == supplier_name].iloc[0]
    categories = ["EcoVadis", "Labor", "Location", "Certification", "No Incidents"]
    cert_map = {"ISO 14001, SA8000": 100, "ISO 14001, ISO 45001": 100,
                "ISO 14001": 70, "ISO 45001": 60, "SA8000": 60, "Partial": 30}
    values = [
        row["EcoVadis"],
        row["Labor Audit Score"],
        row["Score_location"],
        cert_map.get(str(row["Certification Status"]).strip(), 0),
        max(0, 100 - row["Incident History"] * 25),
    ]
    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]], theta=categories + [categories[0]],
        fill="toself", fillcolor=BLUE + "44", line_color=BLUE,
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100]),
                   bgcolor=CARD),
        paper_bgcolor=DARK, font_color=TEXT,
        title=f"ESG Profile: {supplier_name}",
    )
    return fig


def fig_co2_trend():
    monthly = kpis["monthly_trend"]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=monthly["month"], y=monthly["co2"],
                          name="Total CO₂ (tCO₂e)", marker_color=BLUE + "cc"), secondary_y=False)
    fig.add_trace(go.Scatter(x=monthly["month"], y=monthly["energy"],
                              name="Energy (MWh)", line=dict(color=AMBER, width=2),
                              mode="lines+markers"), secondary_y=True)
    fig.update_layout(paper_bgcolor=DARK, plot_bgcolor=CARD,
                      font_color=TEXT, title="Monthly CO₂ Emissions & Energy Consumption",
                      barmode="group", legend=dict(bgcolor=CARD))
    fig.update_yaxes(title_text="CO₂ (tCO₂e)", secondary_y=False, gridcolor="#2a2a4a")
    fig.update_yaxes(title_text="Energy (MWh)", secondary_y=True)
    return fig


def fig_scope_donut():
    s1 = kpis["total_scope1_tco2"]
    s2 = kpis["total_scope2_tco2"]
    s3 = kpis["total_scope3_tco2"]
    fig = go.Figure(go.Pie(
        labels=["Scope 1 (Direct)", "Scope 2 (Energy)", "Scope 3 (Supply Chain)"],
        values=[s1, s2, s3],
        hole=0.55,
        marker_colors=[RED, AMBER, BLUE],
    ))
    fig.update_layout(paper_bgcolor=DARK, font_color=TEXT,
                      title="Annual Emissions by Scope")
    return fig


def fig_factory_co2():
    fb = kpis["factory_breakdown"].copy()
    fb["factory_name"] = fb["factory_id"].map(FACTORY_NAMES)
    fig = px.bar(fb, x="factory_name", y="co2", color="co2",
                 color_continuous_scale=["green", "orange", "red"],
                 title="CO₂ by Factory",
                 labels={"co2": "Total CO₂ (tCO₂e)", "factory_name": ""})
    fig.update_layout(paper_bgcolor=DARK, plot_bgcolor=CARD,
                      font_color=TEXT, showlegend=False)
    return fig


def fig_waste_trend():
    monthly = kpis["monthly_trend"]
    fig = go.Figure(go.Scatter(
        x=monthly["month"], y=monthly["waste_pct"],
        mode="lines+markers+text",
        text=[f"{v:.0f}%" for v in monthly["waste_pct"]],
        textposition="top center",
        line=dict(color=GREEN, width=2),
        fill="tozeroy", fillcolor=GREEN + "22",
        name="Waste Recycled %",
    ))
    fig.add_hline(y=70, line_dash="dash", line_color=AMBER,
                  annotation_text="Target 70%")
    fig.update_layout(paper_bgcolor=DARK, plot_bgcolor=CARD,
                      font_color=TEXT, title="Waste Recycling Rate (%)",
                      yaxis=dict(range=[55, 80], gridcolor="#2a2a4a"))
    return fig


def fig_segment_bar():
    seg = summary_by_segment(df_sup)
    seg["color"] = seg["Risk_Segment"].map(SEG_COLORS)
    fig = go.Figure(go.Bar(
        x=seg["Risk_Segment"], y=seg["Count"],
        marker_color=seg["color"],
        text=seg["Count"], textposition="outside",
    ))
    fig.update_layout(paper_bgcolor=DARK, plot_bgcolor=CARD,
                      font_color=TEXT, title="Suppliers by Risk Segment",
                      yaxis=dict(gridcolor="#2a2a4a"))
    return fig


def fig_alerts_timeline():
    if len(em_alerts) == 0:
        return go.Figure().update_layout(paper_bgcolor=DARK, font_color=TEXT,
                                          title="No Alerts Triggered")
    df_a = em_alerts.copy()
    df_a["severity_color"] = df_a["severity"].map(TL_COLORS)
    fig = px.scatter(df_a, x="month", y="rule_name", color="severity",
                     color_discrete_map=TL_COLORS,
                     size_max=18, symbol="severity",
                     hover_data=["value", "threshold", "action"],
                     title="Alert Timeline")
    fig.update_traces(marker_size=12)
    fig.update_layout(paper_bgcolor=DARK, plot_bgcolor=CARD,
                      font_color=TEXT)
    return fig


def fig_supplier_scatter():
    fig = px.scatter(
        df_sup, x="ESG_Risk_Score", y="EcoVadis",
        color="Risk_Segment", color_discrete_map=SEG_COLORS,
        hover_name="Supplier",
        hover_data={"Country": True, "Incident History": True},
        title="Risk Score vs EcoVadis",
        size="Incident History",
        size_max=20,
    )
    fig.update_layout(paper_bgcolor=DARK, plot_bgcolor=CARD, font_color=TEXT)
    return fig


# ─────────────────────────────────────────────
# APP LAYOUT
# ─────────────────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG],
                suppress_callback_exceptions=True)
app.title = "GreenChain ESG Intelligence"

SIDEBAR = dbc.Nav([
    html.Div([
        html.Img(src="https://img.icons8.com/fluency/48/leaf.png",
                 style={"width": "36px", "marginBottom": "4px"}),
        html.H5("GreenChain ESG", style={"color": GREEN, "fontWeight": "700",
                                          "marginBottom": "0", "fontSize": "14px"}),
        html.Small("Intelligence System", style={"color": MUTED}),
    ], style={"textAlign": "center", "padding": "16px 0 20px"}),
    dbc.NavLink("🏠 Overview",          href="/",         active="exact", style={"color": TEXT}),
    dbc.NavLink("🔍 Supplier Risk",      href="/step1",    active="exact", style={"color": TEXT}),
    dbc.NavLink("📊 ESG Reporting",      href="/step2",    active="exact", style={"color": TEXT}),
    dbc.NavLink("🚨 Monitoring",         href="/step3",    active="exact", style={"color": TEXT}),
    dbc.NavLink("📋 Decision Memo",      href="/memo",     active="exact", style={"color": TEXT}),
], vertical=True, pills=True,
   style={"backgroundColor": CARD, "height": "100vh", "padding": "8px",
          "borderRight": f"1px solid #2a2a4a", "position": "fixed",
          "width": "200px", "top": 0, "left": 0})

app.layout = html.Div([
    dcc.Location(id="url"),
    SIDEBAR,
    html.Div(id="page-content", style={
        "marginLeft": "210px", "backgroundColor": DARK,
        "minHeight": "100vh", "padding": "24px",
        "color": TEXT, "fontFamily": "Inter, sans-serif",
    }),
], style={"backgroundColor": DARK})


# ─────────────────────────────────────────────
# PAGE RENDERERS
# ─────────────────────────────────────────────

def page_overview():
    n_high   = len(df_sup[df_sup["Risk_Segment"] == "high"])
    n_medium = len(df_sup[df_sup["Risk_Segment"] == "medium"])
    n_low    = len(df_sup[df_sup["Risk_Segment"] == "low"])
    n_red_al = len(em_alerts[em_alerts["severity"] == "RED"]) if len(em_alerts) else 0
    n_amb_al = len(em_alerts[em_alerts["severity"] == "AMBER"]) if len(em_alerts) else 0

    co2_tl = traffic_light("co2_monthly_kpi", kpis["monthly_trend"]["co2"].mean())
    en_tl  = traffic_light("energy_monthly_kpi", kpis["monthly_trend"]["energy"].mean())
    ws_tl  = traffic_light("waste_recycled_pct", kpis["monthly_trend"]["waste_pct"].mean())
    sh_pct = round(n_high / len(df_sup) * 100)
    su_tl  = traffic_light("supplier_high_risk_pct", sh_pct)

    return html.Div([
        html.H2("ESG Control Tower", style={"color": GREEN, "marginBottom": "4px"}),
        html.P("GreenChain Electronics – Real-time Sustainability Intelligence",
               style={"color": MUTED, "marginBottom": "24px"}),

        dbc.Row([
            dbc.Col(kpi_card("Total CO₂ (Annual)", f"{kpis['total_co2_tco2']:,.0f}", "tCO₂e", RED), width=2),
            dbc.Col(kpi_card("Energy (Annual)", f"{kpis['total_energy_mwh']:,.0f}", "MWh", AMBER), width=2),
            dbc.Col(kpi_card("Avg Recycling Rate", f"{kpis['avg_waste_recycled_pct']}%", "Target: 70%", GREEN), width=2),
            dbc.Col(kpi_card("Supplier Compliance", f"{compliance_rate}%", "EcoVadis ≥ 60 & 0 incidents", BLUE), width=2),
            dbc.Col(kpi_card("High-Risk Suppliers", f"{n_high}", f"of {len(df_sup)} total", RED), width=2),
            dbc.Col(kpi_card("RED Alerts", f"{n_red_al}", f"{n_amb_al} AMBER active", AMBER), width=2),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Traffic Light Status", style={"color": GREEN, "backgroundColor": CARD}),
                    dbc.CardBody([
                        tl_badge(co2_tl, f"CO₂ emissions – {co2_tl}"),
                        tl_badge(en_tl,  f"Energy usage – {en_tl}"),
                        tl_badge(ws_tl,  f"Waste recycling – {ws_tl}"),
                        tl_badge(su_tl,  f"Supplier risk – {su_tl} ({sh_pct}% high)"),
                    ]),
                ], style={"backgroundColor": CARD, "border": f"1px solid #2a2a4a", "borderRadius": "10px"}),
            ], width=3),
            dbc.Col(dcc.Graph(figure=fig_scope_donut(), config={"displayModeBar": False}), width=4),
            dbc.Col(dcc.Graph(figure=fig_segment_bar(), config={"displayModeBar": False}), width=5),
        ]),
    ])


def page_step1():
    top5 = top_non_compliant(df_sup)
    supplier_options = [{"label": s, "value": s} for s in sorted(df_sup["Supplier"].tolist())]

    return html.Div([
        html.H2("Step 1 – Supplier ESG Due Diligence", style={"color": GREEN}),
        html.P("Risk scoring, segmentation, and identification of non-compliant suppliers.",
               style={"color": MUTED, "marginBottom": "24px"}),

        # Formula explanation
        dbc.Card([
            dbc.CardHeader("Risk Score Formula", style={"color": AMBER, "backgroundColor": CARD}),
            dbc.CardBody([
                html.Code(
                    "ESG_Risk = 100 "
                    "− 0.30×EcoVadis "
                    "− 0.20×LaborAudit "
                    "− 0.20×LocationScore "
                    "− 0.10×IndustryScore "
                    "− 0.10×CertScore "
                    "+ 0.10×IncidentPenalty",
                    style={"color": GREEN, "fontSize": "13px", "backgroundColor": DARK,
                           "padding": "10px", "borderRadius": "6px", "display": "block"}
                ),
                html.Small("Segments: Low < 25 | Medium 25–44 | High ≥ 45",
                           style={"color": MUTED, "marginTop": "8px", "display": "block"}),
            ]),
        ], style={"backgroundColor": CARD, "border": "1px solid #2a2a4a",
                  "borderRadius": "10px", "marginBottom": "20px"}),

        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_risk_heatmap()), width=8),
            dbc.Col(dcc.Graph(figure=fig_supplier_scatter()), width=4),
        ], className="mb-4"),

        html.H5("Top 5 Non-Compliant Suppliers", style={"color": RED, "marginBottom": "12px"}),
        dash_table.DataTable(
            data=top5.to_dict("records"),
            columns=[{"name": c, "id": c} for c in top5.columns],
            style_table={"overflowX": "auto"},
            style_cell={"backgroundColor": CARD, "color": TEXT,
                        "border": "1px solid #2a2a4a", "fontSize": "12px",
                        "padding": "8px"},
            style_header={"backgroundColor": DARK, "color": GREEN,
                          "fontWeight": "bold", "border": "1px solid #2a2a4a"},
            style_data_conditional=[
                {"if": {"filter_query": '{Risk_Label} contains "High"'},
                 "color": RED},
            ],
        ),

        html.H5("Supplier ESG Radar", style={"color": BLUE, "marginTop": "24px", "marginBottom": "12px"}),
        dcc.Dropdown(id="radar-supplier", options=supplier_options,
                     value="Pegatron",
                     style={"backgroundColor": CARD, "color": DARK, "marginBottom": "12px"}),
        dcc.Graph(id="radar-chart"),
    ])


def page_step2():
    fb = kpis["factory_breakdown"].copy()
    fb["factory_name"] = fb["factory_id"].map(FACTORY_NAMES)

    return html.Div([
        html.H2("Step 2 – Internal ESG Reporting", style={"color": GREEN}),
        html.P("Star schema model, executive KPIs, and monthly trend analysis.",
               style={"color": MUTED, "marginBottom": "24px"}),

        # Star schema description
        dbc.Card([
            dbc.CardHeader("Star Schema Design", style={"color": AMBER, "backgroundColor": CARD}),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Strong("FACT: fact_sustainability_metrics", style={"color": BLUE}),
                        html.Ul([
                            html.Li("scope1/2/3_tco2, total_co2"),
                            html.Li("energy_mwh, waste_recycled_pct"),
                            html.Li("water_usage_m3, units_produced"),
                            html.Li("co2/energy/water per unit (KPIs)"),
                        ], style={"color": TEXT, "fontSize": "12px"}),
                    ], width=4),
                    dbc.Col([
                        html.Strong("DIMENSIONS", style={"color": AMBER}),
                        html.Ul([
                            html.Li("dim_time (month, quarter, year, half)"),
                            html.Li("dim_factory (name, country, region, capacity)"),
                            html.Li("dim_supplier (EcoVadis, certification, incidents)"),
                            html.Li("dim_region (framework, climate zone)"),
                            html.Li("dim_product (category, weight, repairability)"),
                        ], style={"color": TEXT, "fontSize": "12px"}),
                    ], width=4),
                    dbc.Col([
                        html.Strong("KEY KPIs", style={"color": GREEN}),
                        html.Ul([
                            html.Li("Total CO₂ (Scope 1–3)"),
                            html.Li("Energy per unit produced"),
                            html.Li("Waste recycling rate"),
                            html.Li("Supplier compliance rate"),
                            html.Li("Water usage per unit"),
                        ], style={"color": TEXT, "fontSize": "12px"}),
                    ], width=4),
                ]),
            ]),
        ], style={"backgroundColor": CARD, "border": "1px solid #2a2a4a",
                  "borderRadius": "10px", "marginBottom": "20px"}),

        dbc.Row([
            dbc.Col(kpi_card("Scope 1", f"{kpis['total_scope1_tco2']:,.0f}", "tCO₂e Direct", RED), width=3),
            dbc.Col(kpi_card("Scope 2", f"{kpis['total_scope2_tco2']:,.0f}", "tCO₂e Energy", AMBER), width=3),
            dbc.Col(kpi_card("Scope 3", f"{kpis['total_scope3_tco2']:,.0f}", "tCO₂e Supply Chain", BLUE), width=3),
            dbc.Col(kpi_card("Supplier Compliance", f"{compliance_rate}%", "EcoVadis≥60, 0 incidents", GREEN), width=3),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_co2_trend()), width=8),
            dbc.Col(dcc.Graph(figure=fig_waste_trend()), width=4),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_factory_co2()), width=6),
            dbc.Col([
                html.H5("Factory KPI Breakdown", style={"color": GREEN, "marginBottom": "12px"}),
                dash_table.DataTable(
                    data=fb[["factory_name","co2","energy","waste","water"]].round(0).to_dict("records"),
                    columns=[
                        {"name": "Factory",           "id": "factory_name"},
                        {"name": "CO₂ (tCO₂e)",      "id": "co2"},
                        {"name": "Energy (MWh)",      "id": "energy"},
                        {"name": "Recycling (%)",     "id": "waste"},
                        {"name": "Water (m³)",        "id": "water"},
                    ],
                    style_cell={"backgroundColor": CARD, "color": TEXT,
                                "border": "1px solid #2a2a4a", "fontSize": "12px",
                                "padding": "10px"},
                    style_header={"backgroundColor": DARK, "color": GREEN, "fontWeight": "bold"},
                ),
            ], width=6),
        ]),
    ])


def page_step3():
    rules_df = pd.DataFrame([{
        "Rule ID":   r["rule_id"],
        "Name":      r["name"],
        "Metric":    r["metric"],
        "Condition": r.get("condition",""),
        "Threshold": r.get("threshold", "rolling"),
        "Severity":  r["severity"],
        "Action":    r["action"][:60] + "…" if len(r["action"]) > 60 else r["action"],
    } for r in ALERT_RULES])

    co2_tl = traffic_light("co2_monthly_kpi", kpis["monthly_trend"]["co2"].mean())
    en_tl  = traffic_light("energy_monthly_kpi", kpis["monthly_trend"]["energy"].mean())
    ws_tl  = traffic_light("waste_recycled_pct", kpis["monthly_trend"]["waste_pct"].mean())
    n_high = len(df_sup[df_sup["Risk_Segment"] == "high"])
    su_tl  = traffic_light("supplier_high_risk_pct", round(n_high / len(df_sup) * 100))

    return html.Div([
        html.H2("Step 3 – Monitoring & Decision Intelligence", style={"color": GREEN}),
        html.P("Alert rules, traffic light system, and real-time ESG control tower.",
               style={"color": MUTED, "marginBottom": "24px"}),

        # Traffic lights
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("ESG Control Tower", style={"color": GREEN, "backgroundColor": CARD}),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Div(style={
                                    "width": "60px", "height": "60px", "borderRadius": "50%",
                                    "backgroundColor": TL_COLORS[co2_tl],
                                    "margin": "0 auto 8px",
                                    "boxShadow": f"0 0 20px {TL_COLORS[co2_tl]}",
                                }),
                                html.P("CO₂ Emissions", style={"color": TEXT, "textAlign": "center", "fontSize": "12px"}),
                                html.P(co2_tl, style={"color": TL_COLORS[co2_tl], "textAlign": "center",
                                                       "fontWeight": "bold", "fontSize": "11px"}),
                            ]),
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.Div(style={
                                    "width": "60px", "height": "60px", "borderRadius": "50%",
                                    "backgroundColor": TL_COLORS[en_tl],
                                    "margin": "0 auto 8px",
                                    "boxShadow": f"0 0 20px {TL_COLORS[en_tl]}",
                                }),
                                html.P("Energy Usage", style={"color": TEXT, "textAlign": "center", "fontSize": "12px"}),
                                html.P(en_tl, style={"color": TL_COLORS[en_tl], "textAlign": "center",
                                                      "fontWeight": "bold", "fontSize": "11px"}),
                            ]),
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.Div(style={
                                    "width": "60px", "height": "60px", "borderRadius": "50%",
                                    "backgroundColor": TL_COLORS[ws_tl],
                                    "margin": "0 auto 8px",
                                    "boxShadow": f"0 0 20px {TL_COLORS[ws_tl]}",
                                }),
                                html.P("Waste Recycling", style={"color": TEXT, "textAlign": "center", "fontSize": "12px"}),
                                html.P(ws_tl, style={"color": TL_COLORS[ws_tl], "textAlign": "center",
                                                      "fontWeight": "bold", "fontSize": "11px"}),
                            ]),
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.Div(style={
                                    "width": "60px", "height": "60px", "borderRadius": "50%",
                                    "backgroundColor": TL_COLORS[su_tl],
                                    "margin": "0 auto 8px",
                                    "boxShadow": f"0 0 20px {TL_COLORS[su_tl]}",
                                }),
                                html.P("Supplier Risk", style={"color": TEXT, "textAlign": "center", "fontSize": "12px"}),
                                html.P(su_tl, style={"color": TL_COLORS[su_tl], "textAlign": "center",
                                                      "fontWeight": "bold", "fontSize": "11px"}),
                            ]),
                        ], width=3),
                    ]),
                ]),
            ], style={"backgroundColor": CARD, "border": "1px solid #2a2a4a",
                      "borderRadius": "10px"}), width=12),
        ], className="mb-4"),

        dcc.Graph(figure=fig_alerts_timeline(), className="mb-4"),

        dbc.Row([
            dbc.Col([
                html.H5("Alert Rule Engine", style={"color": AMBER, "marginBottom": "12px"}),
                dash_table.DataTable(
                    data=rules_df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in rules_df.columns],
                    style_table={"overflowX": "auto"},
                    style_cell={"backgroundColor": CARD, "color": TEXT,
                                "border": "1px solid #2a2a4a", "fontSize": "11px",
                                "padding": "8px", "whiteSpace": "normal",
                                "maxWidth": "200px"},
                    style_header={"backgroundColor": DARK, "color": AMBER, "fontWeight": "bold"},
                    style_data_conditional=[
                        {"if": {"filter_query": '{Severity} = "RED"'},   "color": RED},
                        {"if": {"filter_query": '{Severity} = "AMBER"'}, "color": AMBER},
                    ],
                ),
            ], width=12),
        ]),

        html.Div(className="mb-4"),

        dbc.Row([
            dbc.Col([
                html.H5("Active Emission Alerts", style={"color": RED, "marginBottom": "12px"}),
                dash_table.DataTable(
                    data=em_alerts.to_dict("records") if len(em_alerts) else [],
                    columns=[{"name": c, "id": c} for c in em_alerts.columns] if len(em_alerts) else [],
                    style_table={"overflowX": "auto"},
                    style_cell={"backgroundColor": CARD, "color": TEXT,
                                "border": "1px solid #2a2a4a", "fontSize": "11px", "padding": "8px"},
                    style_header={"backgroundColor": DARK, "color": RED, "fontWeight": "bold"},
                    style_data_conditional=[
                        {"if": {"filter_query": '{severity} = "RED"'},   "color": RED},
                        {"if": {"filter_query": '{severity} = "AMBER"'}, "color": AMBER},
                    ],
                ) if len(em_alerts) else html.P("No emission alerts triggered.", style={"color": GREEN}),
            ], width=12),
        ]),
    ])


def page_memo():
    return html.Div([
        html.H2("Decision Memo", style={"color": GREEN}),
        html.P("AI-generated strategic recommendations based on live data analysis.",
               style={"color": MUTED, "marginBottom": "24px"}),
        dbc.Card([
            dbc.CardBody([
                html.Pre(memo, style={
                    "color": TEXT, "fontSize": "12px", "lineHeight": "1.6",
                    "whiteSpace": "pre-wrap", "fontFamily": "monospace",
                    "backgroundColor": "transparent", "border": "none",
                }),
            ]),
        ], style={"backgroundColor": CARD, "border": "1px solid #2a2a4a", "borderRadius": "10px"}),
    ])


# ─────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname):
    if pathname == "/step1":   return page_step1()
    elif pathname == "/step2": return page_step2()
    elif pathname == "/step3": return page_step3()
    elif pathname == "/memo":  return page_memo()
    return page_overview()


@app.callback(Output("radar-chart", "figure"), Input("radar-supplier", "value"))
def update_radar(supplier):
    if supplier:
        return fig_radar(supplier)
    return go.Figure()


if __name__ == "__main__":
    print("=" * 60)
    print("GreenChain ESG Intelligence System")
    print("Open http://127.0.0.1:8050 in your browser")
    print("=" * 60)
    app.run(debug=False, host="0.0.0.0", port=8050)
