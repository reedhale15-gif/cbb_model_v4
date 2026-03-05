import pandas as pd
import numpy as np
import json

# =========================
# MODEL CONSTANTS
# =========================

LEAGUE_AVG = 109.55
BASE_HOME_COURT = 3.0
LOGISTIC_K = 0.18

RECENCY_WEIGHT = 0.18
MAX_RECENCY_IMPACT = 2.0

# FINAL WEIGHT ADJUSTMENT
BETA_BASE = 0.72
BETA_NET  = 0.18

TEMPO_INFLATION = 1.01


# =========================
# CORE FUNCTIONS
# =========================

def harmonic_tempo(t1, t2):
    return 2 * (t1 * t2) / (t1 + t2)


def expected_ortg(off_rating, opp_def_rating):
    defensive_adjustment = LEAGUE_AVG - opp_def_rating
    return off_rating + defensive_adjustment


def logistic_win_prob(home_margin):
    return 1 / (1 + np.exp(-LOGISTIC_K * home_margin))


def compute_recency_adjustment(home_wab, away_wab, ratings):
    wab_std = ratings["WAB"].std()
    if wab_std == 0:
        return 0

    wab_diff = home_wab - away_wab
    normalized = wab_diff / wab_std
    adjustment = normalized * RECENCY_WEIGHT * 4

    return np.clip(adjustment, -MAX_RECENCY_IMPACT, MAX_RECENCY_IMPACT)


def load_market_data():
    try:
        with open("data/market_odds.json", "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        return df["TOTAL"].mean()
    except:
        return None


# =========================
# PROJECTION ENGINE
# =========================

def run_projection():

    ratings = pd.read_csv("data/efficiency_table.csv")

    # ❗ CHANGE 1: load games from odds instead of Bart schedule
    with open("data/market_odds.json") as f:
        schedule = pd.DataFrame(json.load(f))

    results = []
    raw_spreads = []
    raw_totals = []

    for _, game in schedule.iterrows():

        home = game["HOME"]
        away = game["AWAY"]

        home_row = ratings[ratings["TEAM"] == home]
        away_row = ratings[ratings["TEAM"] == away]

        if home_row.empty or away_row.empty:
            continue

        home_row = home_row.iloc[0]
        away_row = away_row.iloc[0]

        poss = harmonic_tempo(home_row["TEMPO"], away_row["TEMPO"])
        poss *= TEMPO_INFLATION

        home_adj_ortg = expected_ortg(home_row["ADJOE"], away_row["ADJDE"])
        away_adj_ortg = expected_ortg(away_row["ADJOE"], home_row["ADJDE"])

        home_pts = poss * home_adj_ortg / 100
        away_pts = poss * away_adj_ortg / 100

        total = home_pts + away_pts
        base_spread = home_pts - away_pts

        shooting_edge = home_row["EFG"] - away_row["EFGD"]
        turnover_edge = away_row["TORD"] - home_row["TOR"]
        rebound_edge  = home_row["ORB"] - away_row["DRB"]

        factor_edge = (
            0.35 * shooting_edge +
            0.30 * turnover_edge +
            0.25 * rebound_edge
        )

        home_net = home_row["ADJOE"] - home_row["ADJDE"]
        away_net = away_row["ADJOE"] - away_row["ADJDE"]
        net_gap = home_net - away_net

        home_margin = (
            (BETA_BASE * base_spread)
            + (BETA_NET * net_gap)
            + factor_edge
            + BASE_HOME_COURT
        )

        recency_adj = compute_recency_adjustment(
            home_row["WAB"],
            away_row["WAB"],
            ratings
        )

        home_margin += recency_adj

        vegas_spread = -home_margin

        raw_spreads.append(vegas_spread)
        raw_totals.append(total)

        results.append({
            "HOME": home,
            "AWAY": away,
            "SPREAD_RAW": vegas_spread,
            "TOTAL_RAW": total
        })

    df = pd.DataFrame(results)

    spread_bias = np.mean(raw_spreads)
    df["SPREAD_PROJ"] = df["SPREAD_RAW"] - spread_bias

    market_total_mean = load_market_data()
    model_total_mean = np.mean(raw_totals)

    if market_total_mean is not None:
        total_bias = model_total_mean - market_total_mean
        df["TOTAL_PROJ"] = df["TOTAL_RAW"] - total_bias
    else:
        df["TOTAL_PROJ"] = df["TOTAL_RAW"]

    home_margin_proj = -df["SPREAD_PROJ"]
    df["HOME_WIN_PROB"] = home_margin_proj.apply(logistic_win_prob)

    df["SPREAD_PROJ"] = df["SPREAD_PROJ"].round(1)
    df["TOTAL_PROJ"] = df["TOTAL_PROJ"].round(1)
    df["HOME_WIN_PROB"] = df["HOME_WIN_PROB"].round(3)

    df.to_csv("data/projections.csv", index=False)
    print("Saved to data/projections.csv")


if __name__ == "__main__":
    run_projection()
