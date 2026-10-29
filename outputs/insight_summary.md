# Rekova — Demand & Promo Analytics
*Auto-generated on 29 Oct 2026 · data: `C:\Users\rahul\OneDrive - MarksMan Healthcare Communications Pvt. Ltd\Documents\Certara_2\rekova-demand-forecasting\data\raw`*
*Simulated client case study — not real client work.*

## 1. What the data says
- Sep 2026 net sales: **Rs 23.42 Cr**
- Last 12 months: **Rs 249.32 Cr**
- Top-5 SKUs = **75.0%** of LTM net sales
- E-commerce share in Sep 2026: **32.1%**

## 2. Forecast — backtest before believing anything
| model | MAPE_pct | RMSE_Cr | Bias_pct |
|---|---|---|---|
| Linear trend + seasonality | 1.3 | 0.35 | 0.8 |
| Seasonal naive | 8.3 | 1.79 | -8.3 |
| Random forest | 11.8 | 2.98 | -8.4 |

Winner on the 6-month holdout: **Linear trend + seasonality**, MAPE **1.3%**.

> The bar is seasonal-naive. An ML model that loses to it has learned nothing useful —
> with 24 months of data that happens, and reporting it honestly is the point.
> (RandomForest cannot extrapolate a trend beyond the training range; watch it lose.)

### Category-level accuracy (best model per category)
| category | model | MAPE_pct |
|---|---|---|
| Antiseptics | Linear trend + seasonality | 1.7 |
| Fabric Care | Linear trend + seasonality | 3.1 |
| Toilet Care | Linear trend + seasonality | 3.1 |
| Cough & Throat | Seasonal naive | 3.6 |
| Disinfectants | Linear trend + seasonality | 4.6 |
| Air Care | Linear trend + seasonality | 6.9 |

### Next 3 months — best model
| Month | Forecast (Rs Cr) | Lower (Rs Cr) | Upper (Rs Cr) |
|---|---|---|---|
| Oct 2026 | 23.83 | 23.17 | 24.49 |
| Nov 2026 | 22.15 | 21.49 | 22.81 |
| Dec 2026 | 21.21 | 20.55 | 21.87 |

## 3. Promo effectiveness (descriptive, NOT causal)
| brand | channel | uplift_pct | promo_rows | base_rows |
|---|---|---|---|---|
| Stainex | E-commerce | 57.8 | 18 | 54 |
| PureGerm | General Trade | 52 | 24 | 262 |
| AirPure | E-commerce | 42.6 | 9 | 27 |
| Stainex | Modern Trade | 38.1 | 36 | 108 |
| PureGerm | E-commerce | 37.5 | 12 | 60 |
| AirPure | Modern Trade | 37.2 | 12 | 60 |

Discount-response slope: log(units) vs log(1+discount%) at brand-month level:
**0.86** (n=25).
Promos are chosen by sales teams, not randomized — so this is correlation.
Say that out loud before the interviewer does.

## 4. Where the growth is
E-commerce share of monthly net sales is charted in `outputs/charts/ecomm_share.png`
(latest month: 32.1%).

## 5. Reconciliation with the SQL project
Python recomputed the same headline KPIs as `sql/03_kpi_analysis.sql`:
| latest_month | latest_month_net_sales_cr | ltm_net_sales_cr | top5_sku_share_pct | ecomm_share_latest_pct | rows_used |
|---|---|---|---|---|---|
| Sep 2026 | 23.42 | 249.32 | 75 | 32.1 | 7042 |

They must agree within rounding — if they don't, stop and fix the pipeline before
publishing anything. This is the cross-project QA story.

## 6. Caveats
- 24 months of history → 18 train / 6 holdout; results are indicative, not production-grade.
- No promo cost or margin data → uplift is units and sales, not ROI.
- Monthly grain; daily data would allow far stronger seasonality estimates.
- Synthetic data has a clean deterministic trend + seasonality, so the winning MAPE is
  optimistic versus what real client feeds would show. Say it before you're asked.

## 7. Next step (Project 3)
Productionise this logic into a scheduled pipeline (ingest → dbt → Airflow → warehouse →
dashboard) with data-quality tests and CI. That is the analyst-to-data-engineer bridge.
