"""
GreenChain Electronics – Sustainability Intelligence System
Main entry point: runs all 3 steps and prints reports to console.

Usage:
    python main.py            # print all reports
    python src/dashboard.py   # launch interactive dashboard
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
os.chdir(os.path.dirname(__file__))

from step1_supplier_risk import (
    load_suppliers, compute_risk_score, top_non_compliant, summary_by_segment
)
from step2_esg_reporting import (
    build_dim_time, build_dim_factory, build_dim_supplier,
    build_dim_region, build_dim_product,
    build_fact_table, compute_kpis, supplier_compliance_rate
)
from step3_monitoring import (
    evaluate_alerts_emissions, evaluate_supplier_alerts,
    traffic_light, generate_decision_memo
)


def separator(title):
    print(f"\n{'═'*65}")
    print(f"  {title}")
    print(f"{'═'*65}")


def main():
    # ── STEP 1 ──────────────────────────────────────────────────────
    separator("STEP 1 – SUPPLIER ESG DUE DILIGENCE")

    df_sup = compute_risk_score(load_suppliers())

    print("\n📊 Risk Score per Supplier (sorted by risk):")
    print(df_sup[["Supplier", "Country", "EcoVadis", "Labor Audit Score",
                  "ESG_Risk_Score", "Risk_Label"]]
          .sort_values("ESG_Risk_Score", ascending=False)
          .to_string(index=False))

    print("\n📈 Segment Summary:")
    print(summary_by_segment(df_sup).to_string(index=False))

    print("\n🚨 Top 5 Non-Compliant Suppliers:")
    print(top_non_compliant(df_sup).to_string(index=False))

    # ── STEP 2 ──────────────────────────────────────────────────────
    separator("STEP 2 – INTERNAL ESG REPORTING (STAR SCHEMA)")

    dim_time    = build_dim_time()
    dim_factory = build_dim_factory()
    dim_supplier = build_dim_supplier()
    dim_region  = build_dim_region()
    dim_product = build_dim_product()
    fact        = build_fact_table()
    kpis        = compute_kpis(fact, dim_time)

    print(f"\n📐 Star Schema Dimensions:")
    print(f"   dim_time:     {len(dim_time)} rows    (months)")
    print(f"   dim_factory:  {len(dim_factory)} rows    (production sites)")
    print(f"   dim_supplier: {len(dim_supplier)} rows   (supplier master)")
    print(f"   dim_region:   {len(dim_region)} rows    (geographic regions)")
    print(f"   dim_product:  {len(dim_product)} rows    (product lines)")
    print(f"   fact_table:   {len(fact)} rows   (monthly × factory metrics)")

    print(f"\n🌍 Annual KPIs:")
    print(f"   Total CO₂:         {kpis['total_co2_tco2']:>10,.0f} tCO₂e")
    print(f"   — Scope 1:         {kpis['total_scope1_tco2']:>10,.0f} tCO₂e  (direct)")
    print(f"   — Scope 2:         {kpis['total_scope2_tco2']:>10,.0f} tCO₂e  (energy)")
    print(f"   — Scope 3:         {kpis['total_scope3_tco2']:>10,.0f} tCO₂e  (supply chain)")
    print(f"   Total Energy:      {kpis['total_energy_mwh']:>10,.0f} MWh")
    print(f"   Avg Recycling:     {kpis['avg_waste_recycled_pct']:>10.1f} %")
    print(f"   Total Water:       {kpis['total_water_m3']:>10,.0f} m³")
    print(f"   Supplier Compliance: {supplier_compliance_rate():.1f}%")

    print("\n📅 Monthly CO₂ Trend:")
    print(kpis["monthly_trend"][["month", "co2", "energy", "waste_pct"]].to_string(index=False))

    # ── STEP 3 ──────────────────────────────────────────────────────
    separator("STEP 3 – MONITORING & DECISION INTELLIGENCE")

    em_alerts = evaluate_alerts_emissions(fact, dim_time)
    su_alerts = evaluate_supplier_alerts(df_sup)

    print("\n🚦 Traffic Light Status:")
    metrics = {
        "co2_monthly_kpi":       kpis["monthly_trend"]["co2"].mean(),
        "energy_monthly_kpi":    kpis["monthly_trend"]["energy"].mean(),
        "waste_recycled_pct":    kpis["monthly_trend"]["waste_pct"].mean(),
        "supplier_high_risk_pct": len(df_sup[df_sup["Risk_Segment"]=="high"]) / len(df_sup) * 100,
    }
    icons = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}
    for m, v in metrics.items():
        tl = traffic_light(m, v)
        print(f"   {icons[tl]} {m}: {v:.1f}  → {tl}")

    print(f"\n⚠️  Emission Alerts Triggered: {len(em_alerts)}")
    if len(em_alerts):
        print(em_alerts[["month","rule_name","severity","value","threshold"]].to_string(index=False))

    print(f"\n🔔 Supplier Alerts Triggered: {len(su_alerts)}")
    if len(su_alerts):
        print(su_alerts[["supplier","rule_name","severity","value"]].to_string(index=False))

    # ── MEMO ────────────────────────────────────────────────────────
    separator("DECISION MEMO")
    print(generate_decision_memo(df_sup, em_alerts, su_alerts, kpis))

    print("\n" + "═"*65)
    print("  💡 Launch the interactive dashboard:")
    print("     python src/dashboard.py")
    print("     → Open http://127.0.0.1:8050")
    print("═"*65 + "\n")


if __name__ == "__main__":
    main()
