"""Backtested monthly demand forecasting.

Design choices that matter in interviews:
- 6-month holdout at the END of the series (never shuffle time series).
- Three models: seasonal naive baseline, OLS trend + month dummies, RandomForest.
- The winner is chosen by holdout MAPE, then used for the next 3 months.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression


def design_matrix(months: pd.Series) -> pd.DataFrame:
    """t (trend) + twelve month dummies — enough structure for 24 monthly points."""
    X = pd.DataFrame({"t": np.arange(1, len(months) + 1)})
    for m in range(1, 13):
        X[f"m_{m}"] = (months.dt.month.to_numpy() == m).astype(float)
    return X


def _metrics(actual: np.ndarray, pred: np.ndarray) -> dict:
    actual = np.asarray(actual, dtype=float)
    pred = np.asarray(pred, dtype=float)
    mape = float(np.mean(np.abs((actual - pred) / actual)) * 100)
    rmse = float(np.sqrt(np.mean((actual - pred) ** 2)))
    bias = float(np.mean((pred - actual) / actual) * 100)
    return {"MAPE_pct": round(mape, 1),
            "RMSE_Cr": round(rmse / 1e7, 2),
            "Bias_pct": round(bias, 1)}


def backtest_forecast(monthly: pd.DataFrame, horizon: int = 6):
    """monthly: columns [month (datetime64), net_sales]. Returns metrics, holdout, forecast."""
    monthly = monthly.sort_values("month").reset_index(drop=True)
    y = monthly["net_sales"].astype(float).reset_index(drop=True)
    months = monthly["month"]
    n = len(y)
    if n < 12 + horizon:
        raise ValueError("Need at least 18 months of history")

    X = design_matrix(months)
    train_X, test_X = X.iloc[: n - horizon], X.iloc[n - horizon:]
    train_y = y.iloc[: n - horizon]

    # 1) Seasonal naive — the same month one year earlier
    naive_pred = pd.Series([y.iloc[i - 12] for i in range(n - horizon, n)])

    # 2) OLS: linear trend + month dummies
    lr = LinearRegression().fit(train_X, train_y)
    lr_pred = pd.Series(lr.predict(test_X))

    # 3) RandomForest — same features; trees cannot extrapolate a trend beyond training range
    rf = RandomForestRegressor(n_estimators=500, min_samples_leaf=2,
                               random_state=42, n_jobs=-1)
    rf.fit(train_X, train_y)
    rf_pred = pd.Series(rf.predict(test_X))

    preds = {"Seasonal naive": naive_pred,
             "Linear trend + seasonality": lr_pred,
             "Random forest": rf_pred}

    rows = [{"model": name, **_metrics(y.iloc[n - horizon:].to_numpy(), p.to_numpy())}
            for name, p in preds.items()]
    metrics = pd.DataFrame(rows).sort_values("MAPE_pct").reset_index(drop=True)
    best = metrics.loc[0, "model"]

    # ---------------- 3-month ahead forecast with the winning model ----------------
    future_months = pd.date_range(months.iloc[-1] + pd.offsets.MonthBegin(1),
                                  periods=3, freq="MS")
    fut = pd.DataFrame({"t": np.arange(n + 1, n + 4)})
    for m in range(1, 13):
        fut[f"m_{m}"] = (future_months.month.to_numpy() == m).astype(float)
    fut = fut[X.columns]

    y_by_month = pd.Series(y.to_numpy(), index=months.dt.strftime("%Y-%m"))
    if best == "Seasonal naive":
        fut_vals = np.array([
            y_by_month[(fm - pd.DateOffset(months=12)).strftime("%Y-%m")]
            for fm in future_months], dtype=float)
    elif best == "Linear trend + seasonality":
        fut_vals = lr.predict(fut)
    else:
        fut_vals = rf.predict(fut)

    resid_std = float(np.std(y.iloc[n - horizon:].to_numpy()
                             - preds[best].to_numpy(), ddof=1))
    fc = pd.DataFrame({
        "month": future_months,
        "forecast_net_sales": np.round(fut_vals, 0),
        "lower": np.round(np.maximum(fut_vals - 1.96 * resid_std, 0), 0),
        "upper": np.round(fut_vals + 1.96 * resid_std, 0),
        "model": best,
    })
    holdout = pd.DataFrame({
        "month": months.iloc[n - horizon:].to_numpy(),
        "actual": y.iloc[n - horizon:].to_numpy(),
        "predicted": preds[best].to_numpy(),
    })
    return metrics, holdout, fc
