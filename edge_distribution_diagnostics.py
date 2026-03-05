import pandas as pd
import json

from edge_engine import normalize_name, american_to_implied_prob


# ----------------------------
# LOAD DATA
# ----------------------------

projections = pd.read_csv("data/projections.csv")

with open("data/market_odds.json") as f:
    market = json.load(f)

market_df = pd.DataFrame(market)


# ----------------------------
# NORMALIZE (PRODUCTION LOGIC)
# ----------------------------

projections["HOME_NORM"] = projections["HOME"].apply(normalize_name)
projections["AWAY_NORM"] = projections["AWAY"].apply(normalize_name)

market_df["HOME_NORM"] = market_df["HOME"].apply(normalize_name)
market_df["AWAY_NORM"] = market_df["AWAY"].apply(normalize_name)

market_df = market_df[[
    "HOME",
    "AWAY",
    "HOME_NORM",
    "AWAY_NORM",
    "SPREAD",
    "TOTAL",
    "HOME_ML"
]]


# ----------------------------
# MERGE
# ----------------------------

merged = projections.merge(
    market_df,
    on=["HOME_NORM", "AWAY_NORM"],
    how="inner"
)

print("\nMatched Games:", len(merged))


# ----------------------------
# COMPUTE EDGES
# ----------------------------

merged["SPREAD_EDGE"] = merged["SPREAD_PROJ"] - merged["SPREAD"]
merged["TOTAL_EDGE"] = merged["TOTAL_PROJ"] - merged["TOTAL"]

merged["MARKET_HOME_PROB"] = merged["HOME_ML"].apply(american_to_implied_prob)
merged["ML_EDGE"] = merged["HOME_WIN_PROB"] - merged["MARKET_HOME_PROB"]


# ----------------------------
# DISTRIBUTIONS
# ----------------------------

def bucket_counts(series, thresholds):
    results = {}
    abs_series = series.abs()
    for t in thresholds:
        results[f">= {t}"] = int((abs_series >= t).sum())
    return results


spread_thresholds = [1, 1.5, 2, 2.5, 3, 4]
total_thresholds = [2, 3, 4, 5, 6, 8]
ml_thresholds = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07]

print("\n--- SPREAD EDGE DISTRIBUTION ---")
print(bucket_counts(merged["SPREAD_EDGE"], spread_thresholds))

print("\n--- TOTAL EDGE DISTRIBUTION ---")
print(bucket_counts(merged["TOTAL_EDGE"], total_thresholds))

print("\n--- ML EDGE DISTRIBUTION ---")
print(bucket_counts(merged["ML_EDGE"], ml_thresholds))


# ----------------------------
# AVERAGES
# ----------------------------

print("\n--- AVERAGES ---")
print("Avg Spread Edge:", round(merged["SPREAD_EDGE"].mean(), 3))
print("Avg Total Edge:", round(merged["TOTAL_EDGE"].mean(), 3))
print("Avg ML Edge:", round(merged["ML_EDGE"].mean(), 4))


# ----------------------------
# SCALE CHECK
# ----------------------------

print("\n--- SCALE CHECK ---")
print("Mean Model Spread:", round(merged["SPREAD_PROJ"].mean(), 3))
print("Mean Market Spread:", round(merged["SPREAD"].mean(), 3))


# ----------------------------
# SAMPLE ROWS
# ----------------------------

print("\n--- SAMPLE MATCHED ROWS ---")
print(
    merged[
        ["HOME_x", "AWAY_x", "SPREAD_PROJ", "SPREAD", "SPREAD_EDGE"]
    ].head(10)
)
