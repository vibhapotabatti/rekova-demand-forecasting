# Rekova — Demand Forecasting & Promo Analytics (Project 2)
### Companion to [`rekova-sales-analytics`](https://github.com/vibhapotabatti/rekova-sales-analytics) — same simulated CPG client, Python modelling on top

[![GitHub](https://img.shields.io/badge/GitHub-vibhapotabatti%2Frekova--demand--forecasting-181717?logo=github)](https://github.com/vibhapotabatti/rekova-demand-forecasting)

> **Engineering flagship:** the [Airflow + dbt + DuckDB data platform](https://github.com/vibhapotabatti/rekova-data-platform)
> runs the same data through a scheduled, tested production pipeline.

> Honest framing (same rules as Project 1): this is a **simulated case study** for the
> fictional client *Rekova Consumer Care*. It is modeled on the hygiene-FMCG domain you
> support at Infosys — present it as domain-driven portfolio work, not as real client delivery.

## What this project answers (the business questions)

1. **"Where will the next quarter land?"** — 3-month net-sales forecast, built honestly:
   a 6-month backtest vs two baselines, before any number is trusted.
2. **"Is our model actually better than a naive forecast?"** — seasonal-naive baseline vs
   OLS trend+seasonality vs RandomForest. Whoever wins on MAPE goes into production;
   trees that can't extrapolate lose, and saying *why* is the senior answer.
3. **"Which promos actually move units?"** — promo-month uplift by brand × channel, plus a
   discount-response slope (descriptive — explicitly **not** causal).
4. **"Where is growth coming from?"** — e-commerce share of monthly net sales.

## Structure

```
rekova-demand-forecasting/
├── src/
│   ├── data_prep.py          <- cleans raw feeds exactly like the SQL staging (02)
│   ├── forecast.py           <- backtest + model comparison + 3-month forecast
│   ├── promo_analysis.py     <- promo uplift, discount response, SQL reconciliation
│   └── run_all.py            <- one command: metrics + charts + auto-written report
├── outputs/                  <- generated: CSVs, charts/*.png, insight_summary.md
└── docs/
    └── interview_notes.md    <- 60-second story, defense Q&A, resume bullets
```

## Quickstart

```powershell
# 1) install deps
pip install -r requirements.txt

# 2) generate the simulated client data (seeded, reproducible)
python scripts\generate_data.py

# 3) run the full analysis
python src\run_all.py
```

The generator writes `data/raw/*.csv`. Override with the `REKOVA_RAW_DIR`
environment variable if you keep the data elsewhere (the companion SQL/Power BI
project's `data/raw` also works).

## What you get (all auto-generated, every run)

| Output | What it proves |
|---|---|
| `outputs/forecast_backtest_metrics.csv` | you validate before forecasting |
| `outputs/forecast_next_3_months.csv` | forecast + approximate 95% band |
| `outputs/promo_uplift.csv` | promo effectiveness by brand × channel |
| `outputs/category_forecast_accuracy.csv` | per-category model quality |
| `outputs/reconciliation.csv` | Python vs SQL numbers must agree (cross-project QA) |
| `outputs/charts/*.png` | trend+forecast, promo uplift, e-commerce share |
| `outputs/insight_summary.md` | the 1-pager ready to paste into your portfolio/LinkedIn |

## Methodology notes (say these in interviews)

- **Backtest first:** train on the first 18 months, hold out the last 6, compare MAPE/RMSE/bias.
  With 24 months of data this is the maximum honest split — more would overfit.
- **Baseline discipline:** seasonal-naive is the bar. If an ML model can't beat it, it hasn't
  learned anything useful — common at this data volume, and worth stating.
- **RandomForest lesson:** tree models cannot extrapolate beyond the training target range —
  visible when the trend grows outside the trained window. (The script shows the comparison.)
- **Why the winning MAPE looks unusually low:** this is synthetic data with a clean
  deterministic trend + seasonality, and monthly aggregation averages out noise. Real client
  feeds are messier — say this before someone asks you to defend a 1% MAPE.
- **Promo uplift is descriptive:** promos are chosen by sales teams, not randomized — no
  holdout means no causal claim. The report says this out loud; interviewers respect it.
- **Cross-validation:** `reconciliation.csv` recomputes headline KPIs in Python that the SQL
  project already produced (latest-month net sales, top-5 SKU share, e-comm share) — they must
  match. That is pipeline QA, not decoration.

## Next in the ladder

Project 3 is the engineering flagship: turn this logic into a scheduled pipeline
(ingest → dbt transforms → Airflow → warehouse → dashboard) with data-quality tests + CI —
which upgrades your positioning from "analyst who writes Python" to "analyst who ships".
