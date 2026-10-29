"""Rekova Project 2 — one-command analytics run.

Usage:
    python src/run_all.py

Reads the Project 1 raw CSVs, cleans them (SQL staging twin), backtests three
forecast models, forecasts 3 months, analyses promo uplift, reconciles KPIs,
and writes CSVs + charts + an auto-generated 1-page insight summary.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_prep import load_clean, monthly_total, monthly_by_category, raw_dir  # noqa: E402
from forecast import backtest_forecast  # noqa: E402
from promo_analysis import promo_uplift, discount_response, reconciliation  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
CHARTS = OUT / "charts"


def md_table(df: pd.DataFrame) -> str:
    def fmt(v):
        if isinstance(v, (float, np.floating)):
            s = f"{v:,.2f}".rstrip("0").rstrip(".")
            return s if s else "0"
        return str(v)

    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |",
             "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(fmt(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def _style():
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except Exception:
        plt.style.use("ggplot")


def plot_forecast(monthly, holdout, fc, metrics):
    _style()
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(monthly["month"], monthly["net_sales"] / 1e7,
            color="#1f3b4d", lw=2, label="Actual net sales")
    ax.plot(holdout["month"], holdout["predicted"] / 1e7,
            color="#d97706", lw=2, ls="--", marker="s", ms=4, label="Holdout prediction")
    ax.plot(fc["month"], fc["forecast_net_sales"] / 1e7,
            color="#0f7b6c", lw=2, marker="D", ms=5, label="3-month forecast")
    ax.fill_between(fc["month"],
                    fc["lower"] / 1e7, fc["upper"] / 1e7,
                    color="#0f7b6c", alpha=0.15, label="Approx. 95% band")
    ax.axvline(holdout["month"].iloc[0], color="grey", ls=":", lw=1)
    best = metrics.iloc[0]
    ax.annotate(f"Best on holdout: {best['model']} (MAPE {best['MAPE_pct']}%)",
                xy=(0.01, 0.95), xycoords="axes fraction", fontsize=9)
    ax.set_title("Rekova — monthly net sales: 6-month backtest & 3-month forecast")
    ax.set_ylabel("Net sales (Rs Cr)")
    ax.legend(loc="lower right", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(CHARTS / "forecast_chart.png", dpi=150)
    plt.close(fig)


def plot_promo(promo: pd.DataFrame):
    if promo.empty:
        return
    _style()
    top = promo.sort_values("uplift_pct", ascending=False).head(10).iloc[::-1]
    labels = top["brand"] + " / " + top["channel"]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.barh(labels, top["uplift_pct"], color="#0f7b6c")
    for i, v in enumerate(top["uplift_pct"]):
        ax.text(v + 0.5, i, f"{v:.0f}%", va="center", fontsize=8)
    ax.set_xlabel("Average unit uplift in promo months vs base months (%)")
    ax.set_title("Promo uplift by brand & channel (last 12 months)")
    fig.tight_layout()
    fig.savefig(CHARTS / "promo_uplift.png", dpi=150)
    plt.close(fig)


def ecomm_share(df: pd.DataFrame) -> pd.Series:
    piv = df.pivot_table(index="month", columns="channel_type",
                         values="net_sales", aggfunc="sum", fill_value=0)
    return (piv["E-commerce"] / piv.sum(axis=1) * 100).round(2)


def plot_ecomm(share: pd.Series):
    _style()
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.plot(share.index, share.values, color="#b45309", lw=2, marker="o", ms=3)
    ax.fill_between(share.index, share.values, color="#b45309", alpha=0.10)
    ax.set_title("E-commerce share of monthly net sales")
    ax.set_ylabel("Share of net sales (%)")
    fig.tight_layout()
    fig.savefig(CHARTS / "ecomm_share.png", dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    CHARTS.mkdir(exist_ok=True)

    print(f"Reading raw data from: {raw_dir()}")
    df = load_clean()
    monthly = monthly_total(df)
    print(f"Clean rows: {len(df):,} | months: {len(monthly)} | "
          f"{monthly['month'].min():%b %Y} to {monthly['month'].max():%b %Y}")

    metrics, holdout, fc = backtest_forecast(monthly, horizon=6)
    metrics.to_csv(OUT / "forecast_backtest_metrics.csv", index=False)
    holdout.to_csv(OUT / "forecast_holdout.csv", index=False)
    fc.to_csv(OUT / "forecast_next_3_months.csv", index=False)
    print("\n== Backtest (6-month holdout) ==")
    print(metrics.to_string(index=False))

    cat_rows = []
    cat_month = monthly_by_category(df)
    for cat, g in cat_month.groupby("category"):
        m_cat, _, _ = backtest_forecast(g, horizon=6)
        best_cat = m_cat.iloc[0]
        cat_rows.append({"category": cat,
                         "best_model": best_cat["model"],
                         "MAPE_pct": float(best_cat["MAPE_pct"])})
    cat_df = (pd.DataFrame(cat_rows)
                .sort_values("MAPE_pct").reset_index(drop=True))
    cat_df.to_csv(OUT / "category_forecast_accuracy.csv", index=False)

    promo = promo_uplift(df, last_n_months=12)
    promo.to_csv(OUT / "promo_uplift.csv", index=False)
    disc = discount_response(df, last_n_months=12)

    recon = reconciliation(df)
    pd.DataFrame([recon]).to_csv(OUT / "reconciliation.csv", index=False)

    share = ecomm_share(df)
    plot_forecast(monthly, holdout, fc, metrics)
    plot_promo(promo)
    plot_ecomm(share)

    best = metrics.iloc[0]
    fc_rows = pd.DataFrame({
        "Month": fc["month"].dt.strftime("%b %Y"),
        "Forecast (Rs Cr)": (fc["forecast_net_sales"] / 1e7).round(2),
        "Lower (Rs Cr)": (fc["lower"] / 1e7).round(2),
        "Upper (Rs Cr)": (fc["upper"] / 1e7).round(2),
    })
    promo_view = promo.head(6)[["brand", "channel", "uplift_pct",
                                 "promo_rows", "base_rows"]]
    cat_view = cat_df.rename(columns={"best_model": "model"})

    report = f"""# Rekova — Demand & Promo Analytics
*Auto-generated on {pd.Timestamp.now():%d %b %Y} · data: `{raw_dir()}`*
*Simulated client case study — not real client work.*

## 1. What the data says
- {recon['latest_month']} net sales: **Rs {recon['latest_month_net_sales_cr']} Cr**
- Last 12 months: **Rs {recon['ltm_net_sales_cr']} Cr**
- Top-5 SKUs = **{recon['top5_sku_share_pct']}%** of LTM net sales
- E-commerce share in {recon['latest_month']}: **{recon['ecomm_share_latest_pct']}%**

## 2. Forecast — backtest before believing anything
{md_table(metrics)}

Winner on the 6-month holdout: **{best['model']}**, MAPE **{best['MAPE_pct']}%**.

> The bar is seasonal-naive. An ML model that loses to it has learned nothing useful —
> with 24 months of data that happens, and reporting it honestly is the point.
> (RandomForest cannot extrapolate a trend beyond the training range; watch it lose.)

### Category-level accuracy (best model per category)
{md_table(cat_view)}

### Next 3 months — best model
{md_table(fc_rows)}

## 3. Promo effectiveness (descriptive, NOT causal)
{md_table(promo_view)}

Discount-response slope: log(units) vs log(1+discount%) at brand-month level:
**{disc.get('discount_response_loglog_slope')}** (n={disc.get('n_obs')}).
Promos are chosen by sales teams, not randomized — so this is correlation.
Say that out loud before the interviewer does.

## 4. Where the growth is
E-commerce share of monthly net sales is charted in `outputs/charts/ecomm_share.png`
(latest month: {recon['ecomm_share_latest_pct']}%).

## 5. Reconciliation with the SQL project
Python recomputed the same headline KPIs as `sql/03_kpi_analysis.sql`:
{md_table(pd.DataFrame([recon]))}

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
"""
    (OUT / "insight_summary.md").write_text(report, encoding="utf-8")

    print("\n== Promo uplift (top 6) ==")
    print(promo_view.to_string(index=False))
    print("\n== Reconciliation (must match SQL project) ==")
    for k, v in recon.items():
        print(f"  {k}: {v}")
    print("\nOutputs written to:", OUT)
    print("Charts:", CHARTS)
    print("Report:", OUT / "insight_summary.md")


if __name__ == "__main__":
    main()
