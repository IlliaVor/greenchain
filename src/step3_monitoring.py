"""
Step 3 – Monitoring & Decision Intelligence
GreenChain Electronics – Sustainability Intelligence System

Alert rule engine + decision memo generation.
"""

import pandas as pd
import numpy as np
from datetime import datetime

# ─────────────────────────────────────────────
# ALERT RULE ENGINE
# ─────────────────────────────────────────────

ALERT_RULES = [
    {
        "rule_id":   "CO2-01",
        "name":      "Absolute CO₂ Threshold",
        "metric":    "total_co2",
        "condition": "gt",
        "threshold": 15000,          # tCO₂ per month company-wide
        "severity":  "RED",
        "action":    "Escalate to Chief Sustainability Officer. Investigate scope 3 drivers.",
        "destination": "CSO, VP Operations",
    },
    {
        "rule_id":   "CO2-02",
        "name":      "CO₂ Rolling Average Spike",
        "metric":    "total_co2",
        "condition": "gt_rolling_avg",
        "window":    3,
        "multiplier": 1.10,           # 10% above 3-month rolling average
        "severity":  "AMBER",
        "action":    "Notify factory managers. Review production schedule & energy mix.",
        "destination": "Factory Managers",
    },
    {
        "rule_id":   "SUPP-01",
        "name":      "Supplier Risk Escalation",
        "metric":    "ESG_Risk_Score",
        "condition": "gt",
        "threshold": 50,
        "severity":  "RED",
        "action":    "Initiate enhanced due diligence. Schedule on-site audit within 30 days.",
        "destination": "Procurement, Legal",
    },
    {
        "rule_id":   "SUPP-02",
        "name":      "New Supplier Incident",
        "metric":    "Incident History",
        "condition": "gt",
        "threshold": 2,
        "severity":  "AMBER",
        "action":    "Issue corrective action request. Re-evaluate contract terms.",
        "destination": "Procurement",
    },
    {
        "rule_id":   "ENERGY-01",
        "name":      "Energy Overuse",
        "metric":    "energy_mwh",
        "condition": "gt",
        "threshold": 7000,            # MWh/month for largest factory
        "severity":  "AMBER",
        "action":    "Run energy audit. Check HVAC, production line efficiency.",
        "destination": "Facilities Manager",
    },
    {
        "rule_id":   "WASTE-01",
        "name":      "Waste Recycling Below Target",
        "metric":    "waste_recycled_pct",
        "condition": "lt",
        "threshold": 60,
        "severity":  "AMBER",
        "action":    "Review waste sorting procedures. Engage recycling partners.",
        "destination": "Operations Manager",
    },
    {
        "rule_id":   "WATER-01",
        "name":      "Water Usage Spike",
        "metric":    "water_usage_m3",
        "condition": "gt",
        "threshold": 20000,
        "severity":  "RED",
        "action":    "Immediate investigation. Check for leaks or process anomalies.",
        "destination": "Facilities, CSO",
    },
]


def evaluate_alerts_emissions(fact: pd.DataFrame, dim_time: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluate CO2, energy, waste, water alert rules against monthly fact data.
    Returns DataFrame of triggered alerts.
    """
    f = fact.merge(dim_time, on="time_id")
    monthly = (
        f.groupby(["month_num", "month"])
         .agg(total_co2=("total_co2","sum"),
              energy_mwh=("energy_mwh","sum"),
              waste_recycled_pct=("waste_recycled_pct","mean"),
              water_usage_m3=("water_usage_m3","sum"))
         .reset_index().sort_values("month_num")
    )

    alerts = []
    for _, row in monthly.iterrows():
        for rule in ALERT_RULES:
            metric = rule.get("metric")
            if metric not in monthly.columns:
                continue
            val = row.get(metric)
            triggered = False

            if rule["condition"] == "gt" and val > rule["threshold"]:
                triggered = True
            elif rule["condition"] == "lt" and val < rule["threshold"]:
                triggered = True
            elif rule["condition"] == "gt_rolling_avg":
                # rolling average
                window = rule.get("window", 3)
                idx = row.name
                if idx >= window - 1:
                    avg = monthly.loc[max(0, idx-window+1):idx, metric].mean()
                    if val > avg * rule.get("multiplier", 1.1):
                        triggered = True

            if triggered:
                alerts.append({
                    "month":     row["month"],
                    "rule_id":   rule["rule_id"],
                    "rule_name": rule["name"],
                    "metric":    metric,
                    "value":     round(val, 1),
                    "threshold": rule.get("threshold", "rolling"),
                    "severity":  rule["severity"],
                    "action":    rule["action"],
                    "destination": rule["destination"],
                })

    return pd.DataFrame(alerts) if alerts else pd.DataFrame()


def evaluate_supplier_alerts(df_scored: pd.DataFrame) -> pd.DataFrame:
    """Apply supplier-specific alert rules to risk-scored supplier data."""
    alerts = []
    for _, row in df_scored.iterrows():
        for rule in ALERT_RULES:
            metric = rule.get("metric")
            if metric not in df_scored.columns:
                continue
            val = row.get(metric)
            if pd.isna(val):
                continue
            if rule["condition"] == "gt" and val > rule["threshold"]:
                alerts.append({
                    "supplier": row["Supplier"],
                    "country":  row["Country"],
                    "rule_id":  rule["rule_id"],
                    "rule_name": rule["name"],
                    "metric":   metric,
                    "value":    round(val, 1),
                    "threshold": rule["threshold"],
                    "severity": rule["severity"],
                    "action":   rule["action"],
                    "destination": rule["destination"],
                })
    return pd.DataFrame(alerts) if alerts else pd.DataFrame()


# ─────────────────────────────────────────────
# TRAFFIC LIGHT SYSTEM
# ─────────────────────────────────────────────

TRAFFIC_THRESHOLDS = {
    "co2_monthly_kpi":       {"GREEN": 13000, "AMBER": 15000},  # tCO₂
    "energy_monthly_kpi":    {"GREEN": 18000, "AMBER": 20000},  # MWh
    "waste_recycled_pct":    {"GREEN": 68,    "AMBER": 60},     # % (inverted)
    "water_monthly_m3":      {"GREEN": 55000, "AMBER": 60000},  # m³
    "supplier_high_risk_pct":{"GREEN": 15,    "AMBER": 30},     # %
}


def traffic_light(metric: str, value: float) -> str:
    t = TRAFFIC_THRESHOLDS.get(metric)
    if not t:
        return "GREY"
    if metric == "waste_recycled_pct":
        # Higher is better
        if value >= t["GREEN"]:
            return "GREEN"
        elif value >= t["AMBER"]:
            return "AMBER"
        else:
            return "RED"
    else:
        if value <= t["GREEN"]:
            return "GREEN"
        elif value <= t["AMBER"]:
            return "AMBER"
        else:
            return "RED"


# ─────────────────────────────────────────────
# DECISION MEMO
# ─────────────────────────────────────────────

def generate_decision_memo(
    df_scored: pd.DataFrame,
    emission_alerts: pd.DataFrame,
    supplier_alerts: pd.DataFrame,
    kpis: dict,
) -> str:
    """Generate a structured decision memo for GreenChain management."""

    high_risk = df_scored[df_scored["Risk_Segment"] == "high"]
    suspend_candidates = df_scored[
        (df_scored["ESG_Risk_Score"] >= 50) |
        (df_scored["Incident History"] >= 3)
    ].sort_values("ESG_Risk_Score", ascending=False)

    red_alerts = emission_alerts[emission_alerts["severity"] == "RED"] if len(emission_alerts) else pd.DataFrame()
    n_red = len(red_alerts)
    n_supp_alerts = len(supplier_alerts)

    memo = f"""
╔══════════════════════════════════════════════════════════════════╗
║       GREENCHAIN ELECTRONICS – ESG DECISION MEMO                 ║
║       Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}                             ║
╚══════════════════════════════════════════════════════════════════╝

1. EXECUTIVE SUMMARY
   ─────────────────
   Total annual CO₂: {kpis.get('total_co2_tco2', 'N/A'):,.0f} tCO₂e
   Scope 1: {kpis.get('total_scope1_tco2', 'N/A'):,.0f} | Scope 2: {kpis.get('total_scope2_tco2', 'N/A'):,.0f} | Scope 3: {kpis.get('total_scope3_tco2', 'N/A'):,.0f}
   Energy consumed: {kpis.get('total_energy_mwh', 'N/A'):,.0f} MWh
   Avg waste recycled: {kpis.get('avg_waste_recycled_pct', 'N/A')}%
   RED alerts triggered: {n_red}
   Supplier risk alerts: {n_supp_alerts}

2. SUPPLIER ACTIONS
   ─────────────────
   High-risk suppliers ({len(high_risk)}):
"""
    for _, s in suspend_candidates.head(5).iterrows():
        memo += f"   • {s['Supplier']} ({s['Country']}) — Risk Score: {s['ESG_Risk_Score']} — Incidents: {s['Incident History']}\n"

    memo += f"""
   RECOMMENDATIONS:
   a) SUSPEND for re-evaluation: {', '.join(suspend_candidates.head(3)['Supplier'].tolist())}
      → Initiate emergency audit; freeze new purchase orders pending review.

   b) WATCHLIST (medium-high risk):
"""
    watchlist = df_scored[df_scored["Risk_Segment"] == "medium"].nlargest(3, "ESG_Risk_Score")
    for _, s in watchlist.iterrows():
        memo += f"      – {s['Supplier']} ({s['Country']}): ESG score {s['ESG_Risk_Score']}\n"

    memo += """
   c) LONG-TERM: Diversify sourcing away from high-incident geographies.
      Target: reduce Tier-1 suppliers in risk ≥ AMBER regions by 20% within 18 months.

3. PRODUCTION OPTIMISATION
   ─────────────────────────
   • Kyiv Assembly Plant: largest CO₂ contributor due to mixed grid energy.
     Action: Negotiate green energy PPA for 2025; target 40% renewable by Q3.
   • Warsaw Component Hub: relatively efficient; prioritise capacity expansion here.
   • Tallinn R&D: already 80% renewable – maintain and document for ESG reporting.

4. EMISSIONS REDUCTION PATHWAY
   ────────────────────────────
   To reach net-zero by 2040 (16-year horizon):
   • Required annual reduction: ~6.25% per year (compound)
   • Immediate wins: Switch Kyiv grid → renewable PPA (-~18% scope 2)
   • Scope 3: Engage top 10 suppliers for Science-Based Targets (SBTi) commitment
   • Offset residuals with verified carbon credits (Gold Standard)

5. COMPLIANCE POSTURE (CSDDD)
   ──────────────────────────
   • {len(df_scored[df_scored["cert_score"] < 50])} suppliers lack adequate certification – must remediate before next EU audit.
   • Annual supplier self-assessment questionnaire to be deployed Q1 next year.
   • Incident register must be maintained and disclosed in CSRD sustainability report.

6. NEXT STEPS (90-DAY SPRINT)
   ────────────────────────────
   □ Week 1–2:  Suspend/escalate top-3 high-risk suppliers
   □ Week 3–4:  Issue corrective action plans to medium-risk suppliers
   □ Month 2:   Deploy supplier ESG portal for real-time score ingestion
   □ Month 3:   Publish interim CSRD-aligned sustainability report
   □ Ongoing:   Monitor dashboard weekly; review alert thresholds quarterly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Prepared by: GreenChain Sustainability Intelligence System v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return memo


# ─────────────────────────────────────────────
if __name__ == "__main__":
    import os, sys
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, "src")
    from step1_supplier_risk import load_suppliers, compute_risk_score
    from step2_esg_reporting import build_fact_table, build_dim_time, compute_kpis

    df = compute_risk_score(load_suppliers())
    fact = build_fact_table()
    dim_time = build_dim_time()
    kpis = compute_kpis(fact, dim_time)

    em_alerts = evaluate_alerts_emissions(fact, dim_time)
    su_alerts = evaluate_supplier_alerts(df)

    print("EMISSION ALERTS TRIGGERED:")
    if len(em_alerts):
        print(em_alerts[["month","rule_name","severity","value","threshold"]].to_string(index=False))
    else:
        print("  None")

    print("\nSUPPLIER ALERTS:")
    if len(su_alerts):
        print(su_alerts[["supplier","rule_name","severity","value"]].to_string(index=False))

    memo = generate_decision_memo(df, em_alerts, su_alerts, kpis)
    print(memo)
