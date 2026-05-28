"""
Step 1 – Supplier ESG Risk Scoring & Due Diligence
GreenChain Electronics – Sustainability Intelligence System
"""

import pandas as pd
import numpy as np

# ─────────────────────────────────────────────
# WEIGHTS (must sum to 1.0)
# ─────────────────────────────────────────────
WEIGHTS = {
    "ecovadis":      0.30,   # ESG performance (higher = better)
    "labor":         0.20,   # Labor audit (higher = better)
    "location":      0.20,   # Geography risk (higher score_location = lower risk)
    "industry":      0.10,   # Industry ESG intensity
    "certification": 0.10,   # Certification status
    "incidents":     0.10,   # Incident history (higher = worse)
}

# Certification score mapping
CERT_SCORES = {
    "ISO 14001, SA8000":   100,
    "ISO 14001, ISO 45001": 100,
    "ISO 14001":            70,
    "ISO 45001":            60,
    "SA8000":               60,
    "Partial":              30,
    "None":                 0,
}

SEGMENT_LABELS = {
    "low":    "🟢 Low",
    "medium": "🟡 Medium",
    "high":   "🔴 High",
}

# ─────────────────────────────────────────────
def load_suppliers(path: str = "data/Suppliers.xlsx") -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Sheet1")
    df.columns = df.columns.str.strip()
    return df


def score_certification(cert_str) -> float:
    if pd.isna(cert_str):
        return 0.0
    cert_str = str(cert_str).strip()
    return float(CERT_SCORES.get(cert_str, 30))


def compute_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    ESG Risk Score (0–100, HIGHER = MORE RISKY).

    Formula:
        risk = 100
              - W_ecovadis   * EcoVadis           (0–100, higher=better → lowers risk)
              - W_labor      * LaborAudit          (0–100)
              - W_location   * Score_location      (0–100 normalised)
              - W_industry   * Industry_score      (0–100 normalised)
              - W_cert       * CertScore           (0–100)
              + W_incidents  * IncidentPenalty     (each incident adds penalty)
    Then clamp to [0, 100].
    """
    df = df.copy()

    # Normalise location score to 0–100
    df["loc_norm"] = df["Score_location"].fillna(0) / df["Score_location"].max() * 100

    # Normalise industry score to 0–100
    df["ind_norm"] = df["Industry.1"].fillna(0) / df["Industry.1"].max() * 100

    # Certification score
    df["cert_score"] = df["Certification Status"].apply(score_certification)

    # Incident penalty: each incident = 10 pts risk added (cap at 40)
    df["inc_penalty"] = (df["Incident History"].fillna(0) * 10).clip(upper=40)

    # Composite risk score
    df["ESG_Risk_Score"] = (
        100
        - WEIGHTS["ecovadis"]      * df["EcoVadis"].fillna(0)
        - WEIGHTS["labor"]         * df["Labor Audit Score"].fillna(0)
        - WEIGHTS["location"]      * df["loc_norm"]
        - WEIGHTS["industry"]      * df["ind_norm"]
        - WEIGHTS["certification"] * df["cert_score"]
        + WEIGHTS["incidents"]     * df["inc_penalty"]
    ).clip(0, 100).round(1)

    # Segment
    def segment(score):
        if score < 25:
            return "low"
        elif score < 45:
            return "medium"
        else:
            return "high"

    df["Risk_Segment"] = df["ESG_Risk_Score"].apply(segment)
    df["Risk_Label"] = df["Risk_Segment"].map(SEGMENT_LABELS)
    return df


def top_non_compliant(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Non-compliance = high ESG risk + incidents > 1 + no full certification.
    Returns top-N sorted by risk score descending.
    """
    non_comp = df[
        (df["Risk_Segment"] == "high") |
        (df["Incident History"] >= 2) |
        (df["cert_score"] < 50)
    ].copy()
    return non_comp.nlargest(n, "ESG_Risk_Score")[
        ["Supplier", "Country", "ESG_Risk_Score", "Risk_Label",
         "EcoVadis", "Labor Audit Score", "Certification Status",
         "Incident History"]
    ]


def summary_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("Risk_Segment")
          .agg(
              Count=("Supplier", "count"),
              Avg_ESG_Risk=("ESG_Risk_Score", "mean"),
              Avg_EcoVadis=("EcoVadis", "mean"),
              Total_Incidents=("Incident History", "sum"),
          )
          .round(1)
          .reset_index()
    )


# ─────────────────────────────────────────────
if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))

    df = load_suppliers()
    df = compute_risk_score(df)

    print("=" * 60)
    print("SUPPLIER ESG RISK SCORES")
    print("=" * 60)
    print(df[["Supplier", "Country", "EcoVadis", "ESG_Risk_Score", "Risk_Label"]]
          .sort_values("ESG_Risk_Score", ascending=False)
          .to_string(index=False))

    print("\n" + "=" * 60)
    print("SEGMENT SUMMARY")
    print("=" * 60)
    print(summary_by_segment(df).to_string(index=False))

    print("\n" + "=" * 60)
    print("TOP 5 NON-COMPLIANT SUPPLIERS")
    print("=" * 60)
    print(top_non_compliant(df).to_string(index=False))
