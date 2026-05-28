"""
Step 2 – Internal ESG Reporting Model (Star Schema)
GreenChain Electronics – Sustainability Intelligence System

Star Schema:
  FACT:  fact_sustainability_metrics
  DIMS:  dim_time, dim_factory, dim_supplier, dim_region, dim_product
"""

import pandas as pd
import numpy as np
from datetime import date

# ─────────────────────────────────────────────
# DIMENSION TABLES
# ─────────────────────────────────────────────

def build_dim_time() -> pd.DataFrame:
    months = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    quarters = ["Q1","Q1","Q1","Q2","Q2","Q2",
                "Q3","Q3","Q3","Q4","Q4","Q4"]
    return pd.DataFrame({
        "time_id":   range(1, 13),
        "month":     months,
        "month_num": range(1, 13),
        "quarter":   quarters,
        "year":      2024,
        "half":      ["H1"]*6 + ["H2"]*6,
    })


def build_dim_factory() -> pd.DataFrame:
    return pd.DataFrame({
        "factory_id": [1, 2, 3],
        "factory_name": ["Kyiv Assembly Plant", "Warsaw Component Hub", "Tallinn R&D Facility"],
        "country":      ["Ukraine", "Poland", "Estonia"],
        "region":       ["Eastern Europe", "Eastern Europe", "Northern Europe"],
        "capacity_units_per_month": [12000, 8000, 3000],
        "energy_source": ["Mixed Grid", "Renewable 40%", "Renewable 80%"],
    })


def build_dim_supplier(path: str = "data/Suppliers.xlsx") -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Sheet1")
    df.columns = df.columns.str.strip()
    return df[["#", "Supplier", "Country", "Industry", "EcoVadis",
               "Certification Status", "Incident History"]].rename(
        columns={"#": "supplier_id", "Supplier": "supplier_name",
                 "Country": "country", "Industry": "industry",
                 "EcoVadis": "ecovadis_score",
                 "Certification Status": "certification",
                 "Incident History": "incident_count"}
    )


def build_dim_region() -> pd.DataFrame:
    return pd.DataFrame({
        "region_id": [1, 2, 3, 4, 5],
        "region":    ["Eastern Europe", "Northern Europe", "Asia", "North America", "Western Europe"],
        "climate_zone": ["Continental", "Sub-arctic", "Mixed", "Temperate", "Temperate"],
        "regulatory_framework": ["CSDDD+Local", "CSDDD+Nordic", "Local", "SEC/FTC", "CSDDD"],
    })


def build_dim_product() -> pd.DataFrame:
    return pd.DataFrame({
        "product_id":   [1, 2, 3, 4],
        "product_name": ["Laptop Pro", "GreenTab", "SmartHub", "AccessoryKit"],
        "category":     ["Laptop", "Tablet", "Smart Device", "Accessory"],
        "avg_weight_kg":[1.8, 0.6, 0.3, 0.2],
        "repairability_score": [7.2, 6.5, 5.0, 8.0],  # out of 10
    })


# ─────────────────────────────────────────────
# FACT TABLE
# ─────────────────────────────────────────────

def build_fact_table(sust_path: str = "data/Sustainability.xlsx",
                     supp_path: str = "data/Suppliers.xlsx") -> pd.DataFrame:
    """
    Build the central fact table, enriched with computed KPIs.
    One row per (month × factory) combination.
    """
    sust = pd.read_excel(sust_path, sheet_name="Sheet1")
    sust.columns = sust.columns.str.strip()

    months = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    time_ids = {m: i+1 for i, m in enumerate(months)}

    # Replicate across 3 factories with slight variation per factory
    rows = []
    np.random.seed(42)
    factory_multipliers = {1: 1.0, 2: 0.65, 3: 0.25}  # relative size

    for _, r in sust.iterrows():
        for fid, mult in factory_multipliers.items():
            noise = np.random.uniform(0.97, 1.03)
            rows.append({
                "fact_id":         len(rows) + 1,
                "time_id":         time_ids[r["Month"]],
                "factory_id":      fid,
                "region_id":       1 if fid in [1, 2] else (3 if fid == 3 else 2),
                "product_id":      None,   # rolled up across products
                # Scope emissions
                "scope1_tco2":     round(r["Scope1_tCO2"] * mult * noise, 1),
                "scope2_tco2":     round(r["Scope2_tCO2"] * mult * noise, 1),
                "scope3_tco2":     round(r["Scope3_tCO2"] * mult * noise, 1),
                # Operations
                "energy_mwh":      round(r["Energy_MWh"] * mult * noise, 1),
                "waste_recycled_pct": round(min(100, r["Waste_Recycled_%"] * noise), 1),
                "water_usage_m3":  round((r["Water_Usage_m3"] or 18000) * mult * noise, 0),
                "units_produced":  round(factory_multipliers[fid] * 5000 * noise),
            })

    fact = pd.DataFrame(rows)

    # Derived KPIs
    fact["total_co2"] = fact["scope1_tco2"] + fact["scope2_tco2"] + fact["scope3_tco2"]
    fact["co2_per_unit"] = (fact["total_co2"] / fact["units_produced"].replace(0, np.nan)).round(3)
    fact["energy_per_unit"] = (fact["energy_mwh"] / fact["units_produced"].replace(0, np.nan)).round(4)
    fact["water_per_unit"] = (fact["water_usage_m3"] / fact["units_produced"].replace(0, np.nan)).round(2)

    return fact


# ─────────────────────────────────────────────
# KPI COMPUTATIONS
# ─────────────────────────────────────────────

def compute_kpis(fact: pd.DataFrame, dim_time: pd.DataFrame) -> dict:
    f = fact.merge(dim_time, on="time_id")

    kpis = {}

    # Totals for the year
    kpis["total_scope1_tco2"] = fact["scope1_tco2"].sum().round(0)
    kpis["total_scope2_tco2"] = fact["scope2_tco2"].sum().round(0)
    kpis["total_scope3_tco2"] = fact["scope3_tco2"].sum().round(0)
    kpis["total_co2_tco2"]    = fact["total_co2"].sum().round(0)
    kpis["total_energy_mwh"]  = fact["energy_mwh"].sum().round(0)
    kpis["avg_waste_recycled_pct"] = fact["waste_recycled_pct"].mean().round(1)
    kpis["total_water_m3"]    = fact["water_usage_m3"].sum().round(0)

    # Monthly trend (company-wide)
    monthly = (
        f.groupby(["month_num", "month"])
         .agg(co2=("total_co2", "sum"),
              energy=("energy_mwh", "sum"),
              waste_pct=("waste_recycled_pct", "mean"))
         .reset_index()
         .sort_values("month_num")
    )
    kpis["monthly_trend"] = monthly

    # Factory breakdown
    kpis["factory_breakdown"] = (
        fact.groupby("factory_id")
            .agg(co2=("total_co2","sum"),
                 energy=("energy_mwh","sum"),
                 waste=("waste_recycled_pct","mean"),
                 water=("water_usage_m3","sum"))
            .round(1).reset_index()
    )

    # YoY comparison placeholder (assume -5% as target)
    kpis["co2_reduction_vs_target_pct"] = round(
        (kpis["total_co2_tco2"] - kpis["total_co2_tco2"] * 0.95)
        / (kpis["total_co2_tco2"] * 0.95) * 100, 1
    )

    return kpis


def supplier_compliance_rate(supp_path: str = "data/Suppliers.xlsx") -> float:
    """% of suppliers with EcoVadis ≥ 60 and zero incidents."""
    df = pd.read_excel(supp_path, sheet_name="Sheet1")
    df.columns = df.columns.str.strip()
    compliant = df[(df["EcoVadis"] >= 60) & (df["Incident History"] == 0)]
    return round(len(compliant) / len(df) * 100, 1)


# ─────────────────────────────────────────────
if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))

    print("Building Star Schema dimensions…")
    dim_time     = build_dim_time()
    dim_factory  = build_dim_factory()
    dim_supplier = build_dim_supplier()
    dim_region   = build_dim_region()
    dim_product  = build_dim_product()
    fact         = build_fact_table()

    print(f"  dim_time:      {len(dim_time)} rows")
    print(f"  dim_factory:   {len(dim_factory)} rows")
    print(f"  dim_supplier:  {len(dim_supplier)} rows")
    print(f"  dim_region:    {len(dim_region)} rows")
    print(f"  dim_product:   {len(dim_product)} rows")
    print(f"  fact_table:    {len(fact)} rows")

    kpis = compute_kpis(fact, dim_time)
    print("\nAnnual KPIs:")
    for k, v in kpis.items():
        if not isinstance(v, pd.DataFrame):
            print(f"  {k}: {v}")

    print(f"\nSupplier compliance rate: {supplier_compliance_rate()}%")
