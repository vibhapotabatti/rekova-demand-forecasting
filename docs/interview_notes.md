# Project 2 — Interview Notes & Resume Framing

> Same honesty rules as Project 1: the client, brands and data are fictional. Present it as a
> simulated case study grounded in the FMCG domain you support at Infosys. Never claim it was
> delivered to a real client, and never use real client data.

## The 60-second walkthrough (memorize the shape, not the words)

> "I picked up the same simulated CPG dataset as my SQL/Power BI project and asked: can I
> forecast next-quarter sales and tell which promotions actually move units? I trained on the
> first 18 months and held out the last 6 — never shuffled. I compared a seasonal-naive
> baseline, a trend+seasonality regression, and a RandomForest. The regression won at ~X%
> MAPE; the forest lost because trees can't extrapolate a growing trend — a good reminder why
> baselines matter. For promos I measured unit uplift per brand-channel and was explicit that
> it's descriptive, not causal, because promotions aren't randomized. Finally I reconciled my
> Python KPIs against the SQL pipeline — latest-month net sales, top-5 SKU share, e-comm share
> all matched, which is my pipeline QA gate."

## Defense Q&A

1. **Why a 6-month holdout?** With 24 monthly points, training on 18 and testing on 6 is the
   maximum honest split; more test months starve the model, fewer make the test noise.
2. **Why MAPE and not R²?** Business readers think in % error; MAPE makes "we're within X%"
   actionable at the executive review. Report bias too, so over/under-forecasting is visible.
3. **Why does RandomForest lose?** Trees predict within the range of training targets; a
   growing trend beyond that range cannot be extrapolated — the forecast flattens.
4. **Why not ARIMA/Prophet?** At 24 points, any seasonal ARIMA is estimating 12+ parameters
   from 18 observations. Simplicity wins; note that with 3+ years you would revisit.
5. **Is the promo uplift causal?** No. Sales teams place promotions where they expect demand;
   without randomization or a holdout market, it's correlation. An A/B or geo-test design is
   the next step.
6. **What would you productionize first?** Not the model — the data pipeline and backtest
   automation. Retrain monthly, store predictions vs actuals, alarm when MAPE drifts.
7. **How does this connect to your current support job?** Same instincts: baseline the
   incident, validate against known-good, reconcile numbers before declaring success,
   document the failure modes.
8. **What would break this in production?** Missing monthly extracts (the dataset has one!),
   promo calendar arriving late, new SKU launches outside history, distributor churn.

## Resume bullets (pick 2–3, never all)

> **Demand Forecasting (Python, scikit-learn, pandas)** — Built a backtested 3-month
> net-sales forecast for a simulated hygiene-FMCG client; compared seasonal-naive, OLS
> trend+seasonality and RandomForest on a 6-month holdout, selecting the model by MAPE and
> reporting bias explicitly.

> **Promo Effectiveness Analytics** — Quantified promo-month unit uplift by brand × channel
> and estimated a discount-response slope, framing results as descriptive (no causal claim)
> and recommending a geo-holdout test design.

> **Cross-Pipeline QA** — Reconciled Python-computed KPIs (net sales, SKU Pareto, e-commerce
> share) against the SQL pipeline to within rounding, used as a release gate before
> publishing dashboards.

## LinkedIn angle

Don't post charts without a lesson. One post per finding:
- "My RandomForest lost to a one-line seasonal-naive baseline — and that's the most useful
  thing I learned this week" (attracts senior engagement)
- "Our top 5 SKUs carry ~X% of revenue. The Pareto asks a hard question about field effort."
- "Reconciled SQL vs Python before trusting either number — here's why that's a habit, not
  a checkbox."
