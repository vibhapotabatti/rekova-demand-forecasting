"""Promo effectiveness, discount response, and SQL-vs-Python reconciliation."""
import numpy as np
import pandas as pd


def _last_months(df: pd.DataFrame, n_months: int = 12) -> pd.DataFrame:
    cutoff = df["month"].max() - pd.DateOffset(months=n_months - 1)
    return df[df["month"] >= cutoff]


def promo_uplift(df: pd.DataFrame, last_n_months: int = 12) -> pd.DataFrame:
    """Average units per SKU-distributor row: promo months vs base months, per brand/channel.

    Descriptive only — promos are selected by the business, not randomized, so this is
    NOT a causal uplift. Say that before an interviewer does.
    """
    d = _last_months(df, last_n_months)
    rows = []
    for (brand, channel), g in d.groupby(["brand", "channel_type"]):
        promo = g.loc[g["promo_flag"] == 1, "units"]
        base = g.loc[g["promo_flag"] == 0, "units"]
        if len(promo) < 5 or len(base) < 20:
            continue
        rows.append({
            "brand": brand,
            "channel": channel,
            "promo_avg_units": int(round(float(promo.mean()))),
            "base_avg_units": int(round(float(base.mean()))),
            "uplift_pct": round(float((promo.mean() / base.mean() - 1) * 100), 1),
            "promo_rows": int(len(promo)),
            "base_rows": int(len(base)),
        })
    return (pd.DataFrame(rows)
            .sort_values("uplift_pct", ascending=False)
            .reset_index(drop=True))


def discount_response(df: pd.DataFrame, last_n_months: int = 12) -> dict:
    """Log-log slope of units vs (1+discount%) across promo brand-months.

    A rough elasticity proxy; not comparable to price elasticity from a controlled test.
    """
    d = _last_months(df, last_n_months)
    d = d[d["promo_flag"] == 1]
    agg = (d.groupby(["brand", "month"])
             .agg(units=("units", "sum"), disc=("promo_discount_pct", "mean"))
             .reset_index())
    agg = agg[agg["disc"] > 0]
    if len(agg) < 10:
        return {"discount_response_loglog_slope": None, "n_obs": int(len(agg))}
    x = np.log1p(agg["disc"].to_numpy(dtype=float))
    y = np.log(agg["units"].to_numpy(dtype=float))
    slope = float(np.polyfit(x, y, 1)[0])
    return {"discount_response_loglog_slope": round(slope, 2),
            "n_obs": int(len(agg))}


def reconciliation(df: pd.DataFrame) -> dict:
    """Headline KPIs that must equal the SQL project's outputs (03 B2/B3/B4)."""
    latest = df["month"].max()
    month = df[df["month"] == latest]
    ltm = df[df["month"] >= latest - pd.DateOffset(months=11)]
    by_sku = ltm.groupby("sku_id")["net_sales"].sum().sort_values(ascending=False)
    top5_share = float(by_sku.head(5).sum() / by_sku.sum() * 100)
    ecomm_share = float(month.loc[month["channel_type"] == "E-commerce",
                                  "net_sales"].sum()
                        / month["net_sales"].sum() * 100)
    return {
        "latest_month": latest.strftime("%b %Y"),
        "latest_month_net_sales_cr": round(float(month["net_sales"].sum()) / 1e7, 2),
        "ltm_net_sales_cr": round(float(ltm["net_sales"].sum()) / 1e7, 2),
        "top5_sku_share_pct": round(top5_share, 1),
        "ecomm_share_latest_pct": round(ecomm_share, 1),
        "rows_used": int(len(df)),
    }
