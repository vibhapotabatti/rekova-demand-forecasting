"""Load the Rekova client data and reproduce the SQL staging logic in pandas.

The raw CSVs deliberately contain six feed defects (see Project 1 README).
This module is the Python twin of sql/02_data_quality_and_staging.sql:
dedupe, drop returns from the sales frame, derive missing net_sales, trim regions.
"""
import os
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = PROJECT_ROOT / "data" / "raw"
LEGACY_RAW = PROJECT_ROOT.parent / "rekova-sales-analytics" / "data" / "raw"

TRADE = {"General Trade": 0.12, "Modern Trade": 0.10,
         "Pharmacy": 0.06, "E-commerce": 0.16}

KEY = ["month_start", "sku_id", "distributor_id", "units",
       "gross_sales", "net_sales", "promo_flag", "promo_discount_pct"]


def raw_dir() -> Path:
    env = os.environ.get("REKOVA_RAW_DIR")
    if env:
        return Path(env)
    return DEFAULT_RAW if DEFAULT_RAW.exists() else LEGACY_RAW


def load_clean() -> pd.DataFrame:
    """Return the cleaned sell-out fact joined with product + distributor dims."""
    raw = raw_dir()
    so = pd.read_csv(raw / "fact_sellout_monthly.csv")
    prod = pd.read_csv(raw / "dim_product.csv")
    dist = pd.read_csv(raw / "dim_distributor.csv")
    dist["region"] = dist["region"].str.strip()

    # DQ1: exact duplicate rows out
    so = so.drop_duplicates(subset=KEY, keep="first")
    # DQ3: returns (negative units) leave the sales fact
    so = so[so["units"] > 0].copy()

    # DQ5: orphan SKUs vanish naturally on the inner join (and are counted there)
    so = so.merge(prod[["sku_id", "brand", "category", "mrp"]],
                  on="sku_id", how="inner")
    so = so.merge(dist[["distributor_id", "distributor_name", "channel_type", "region"]],
                  on="distributor_id", how="inner")

    # DQ2: derive net_sales where the feed dropped it (mirrors the SQL CASE)
    so["promo_discount_pct"] = so["promo_discount_pct"].fillna(0.0)
    missing = so["net_sales"].isna()
    trade = so["channel_type"].map(TRADE).fillna(0.12)
    derived = (so["gross_sales"]
               * (1 - trade - so["promo_discount_pct"] / 100.0)).round(2)
    so.loc[missing, "net_sales"] = derived[missing]

    so["month"] = pd.to_datetime(so["month_start"])
    return so


def monthly_total(df: pd.DataFrame) -> pd.DataFrame:
    g = (df.groupby("month")
           .agg(net_sales=("net_sales", "sum"), units=("units", "sum")))
    promo_units = df[df["promo_flag"] == 1].groupby("month")["units"].sum()
    g["promo_share"] = (promo_units.reindex(g.index).fillna(0) / g["units"]).round(4)
    return g.reset_index().sort_values("month").reset_index(drop=True)


def monthly_by_category(df: pd.DataFrame) -> pd.DataFrame:
    out = (df.groupby(["category", "month"])["net_sales"].sum()
             .reset_index()
             .sort_values(["category", "month"]))
    return out
