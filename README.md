# GreenChain Electronics – Sustainability Intelligence System

A Business Intelligence and Sustainability Analytics platform developed in Python that simulates ESG governance, supplier due diligence, internal sustainability reporting, and decision intelligence for a global electronics manufacturer.

The project demonstrates how Business Intelligence can support sustainability initiatives by combining ESG reporting, supplier risk analysis, monitoring systems, and automated decision support.
<img width="1916" height="735" alt="image" src="https://github.com/user-attachments/assets/f7c07f05-4b66-4410-8e15-ca21db47a384" />

---

# Project Overview

## Business Scenario

GreenChain Electronics is a mid-sized global electronics manufacturer producing laptops, tablets, and smart devices.

The company faces increasing pressure from:

- EU sustainability regulations and due diligence requirements
- Investor ESG expectations
- Internal commitment to achieve net-zero emissions by 2040

Current challenges include:

- Fragmented supplier data management
- Manual ESG reporting processes
- Lack of real-time monitoring capabilities
- Limited visibility into supplier sustainability risks

This project develops a complete Sustainability Intelligence System covering:

- Supplier Due Diligence
- Internal ESG Reporting
- Monitoring & Decision Intelligence

---

# Project Structure

```text
greenchain/

├── data/
│   ├── Suppliers.xlsx
│   └── Sustainability.xlsx
│
├── src/
│   ├── step1_supplier_risk.py
│   ├── step2_esg_reporting.py
│   ├── step3_monitoring.py
│   └── dashboard.py
│
├── main.py
├── requirements.txt
└── README.md
```

---

# Installation & Execution

## Install dependencies

```bash
pip install -r requirements.txt
```

## Run complete analysis

```bash
python main.py
```

## Launch Dashboard

```bash
python src/dashboard.py
```

Dashboard URL:

```text
http://127.0.0.1:8050
```

---

# Step 1 – Supplier ESG Due Diligence

## Objective

Identify supplier sustainability risks and automate supplier due diligence.

## ESG Risk Scoring Model

```text
ESG Risk Score

= 100
− 0.30 × EcoVadis Score
− 0.20 × Labor Audit Score
− 0.20 × Geography Score
− 0.10 × Industry Score
− 0.10 × Certification Score
+ Incident Penalty
```

Where:

- Higher score = higher risk
- Each incident increases risk
- Geography acts as a regulatory risk proxy

## Risk Segmentation

| Segment | Score Range |
|--------|--------|
| Low Risk | <25 |
| Medium Risk | 25–44 |
| High Risk | ≥45 |

## Supplier Risk Results

### Segment Summary

| Segment | Suppliers | Average Risk | Average EcoVadis | Total Incidents |
|-------|------|------|------|------|
| High Risk | 13 | 54.4 | 50.9 | 32 |
| Medium Risk | 7 | 31.9 | 70.7 | 7 |
| Low Risk | 14 | 18.1 | 83.3 | 2 |

### Key Findings

- 38.2% of suppliers are classified as High Risk
- Most high-risk suppliers are concentrated in higher-risk sourcing regions
- Incident frequency strongly correlates with elevated risk scores
- Supplier sustainability performance is highly uneven

### Top 5 Non-Compliant Suppliers

| Supplier | Risk Score | Country | Incidents |
|------|------|------|------|
| AAC Technologies | 60.6 | China | 2 |
| Compal Electronics | 59.9 | Taiwan | 3 |
| Goertek | 59.4 | China | 3 |
| Pegatron | 59.3 | Taiwan | 4 |
| Flextronics China Plant | 58.9 | China | 3 |

Deliverables:

- Supplier Risk Heatmap
- Supplier segmentation
- Due diligence scoring engine
- High-risk supplier identification

---

# Step 2 – Internal ESG Reporting

## Objective

Create a centralized ESG reporting model using Business Intelligence principles.

## Star Schema Design

### Fact Table

### fact_sustainability_metrics

Contains:

- Scope 1 emissions
- Scope 2 emissions
- Scope 3 emissions
- Energy consumption
- Water consumption
- Recycling metrics
- Production units

### Dimensions

| Table | Rows |
|------|------|
| dim_time | 12 |
| dim_factory | 3 |
| dim_supplier | 34 |
| dim_region | 5 |
| dim_product | 4 |

## Sustainability KPIs

### Annual Results

| KPI | Value |
|------|------|
| Total CO₂ | 347,225 tCO₂e |
| Scope 1 | 28,471 tCO₂e |
| Scope 2 | 55,919 tCO₂e |
| Scope 3 | 262,835 tCO₂e |
| Energy Consumption | 135,874 MWh |
| Average Recycling Rate | 66.4% |
| Water Usage | 377,697 m³ |
| Supplier Compliance Rate | 38.2% |

## Key Insights

### Emissions Structure

- Scope 3 emissions represent approximately 76% of total emissions
- Supply chain activities are the dominant sustainability challenge

### Recycling Performance

- Average recycling performance remains below the 70% target
- Gradual improvement observed throughout the year

### Supplier Compliance

- Supplier compliance remains relatively low
- High-risk suppliers significantly impact ESG performance

Dashboard Components:

- KPI Tiles
- Scope Trend Charts
- Factory Comparison Charts
- Regional Analysis
- Sustainability Monitoring

---

# Step 3 – Monitoring & Decision Intelligence

## Objective

Create a monitoring system capable of generating automated sustainability alerts.

## Alert Rules

| Rule | Trigger | Severity |
|------|------|------|
| Monthly CO₂ > 15,000 | RED |
| Rolling CO₂ Average >110% | AMBER |
| Supplier Risk >50 | RED |
| Incidents >2 | AMBER |
| Energy >7,000 MWh | AMBER |
| Recycling <60% | AMBER |
| Water Usage >20,000 m³ | RED |

## Traffic Light Status

| Metric | Status |
|------|------|
| CO₂ KPI | RED |
| Energy KPI | GREEN |
| Recycling KPI | AMBER |
| Supplier Risk KPI | RED |

## Monitoring Results

- Emission alerts triggered: 35
- Supplier risk alerts triggered: 15
- RED alerts generated: 23

Major issues identified:

- CO₂ thresholds exceeded every month
- Water consumption consistently exceeds limits
- Multiple suppliers exceed acceptable ESG risk levels
- Recycling performance remains below target

---

# Decision Intelligence Memo

## Suspend for Review

- AAC Technologies
- Compal Electronics
- Goertek

Recommended actions:

- Emergency ESG audit
- Freeze new purchase orders
- Conduct corrective action assessment

## Watchlist Suppliers

- Lenovo
- Flex Ltd
- TSMC

## Production Optimisation Recommendations

### Kyiv Plant

- Highest carbon contributor
- Transition toward renewable energy purchasing

### Warsaw Plant

- Most efficient facility
- Expand production capacity

### Tallinn Operations

- Maintain current renewable practices

## Net-Zero Pathway

Required reduction:

```text
~6.25% annual emissions reduction
```

Recommended actions:

- Renewable energy transition
- Supplier engagement programs
- Science-Based Targets adoption
- Carbon offsetting for residual emissions

---

# Dashboard Application

Interactive dashboard built using Dash.

Contains five sections:

1. Overview
2. Supplier Risk
3. ESG Reporting
4. Monitoring
5. Decision Memo

Dashboard features:

- KPI cards
- Heatmaps
- Traffic light indicators
- Alert engine
- Trend visualizations
- Strategic recommendations

---

# Technologies Used

- Python
- Pandas
- NumPy
- Plotly
- Dash
- Business Intelligence Concepts
- Star Schema Modelling

---

# Project Conclusions

The Sustainability Intelligence System demonstrates how Business Intelligence can transform ESG reporting from static compliance activities into continuous decision support.

Key conclusions:

- Supply chain emissions dominate environmental impact
- Supplier risk management is the largest ESG challenge
- Real-time monitoring improves visibility significantly
- Automated alerts enable faster interventions
- Data-driven sustainability governance supports compliance and net-zero objectives

The project provides a complete BI-driven sustainability workflow from data collection to decision-making.
