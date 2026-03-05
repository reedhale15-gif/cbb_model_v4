import pandas as pd
import numpy as np
from projection_engine import harmonic_tempo, expected_ortg, logistic_win_prob
from projection_engine import LEAGUE_AVG, BASE_HOME_COURT, RECENCY_WEIGHT, MAX_RECENCY_IMPACT
from h2h_engine import get_h2h_stats

EDGE_THRESHOLD_SPREAD = 2.0
H2H_WEIGHT = 0.07
USE_H2H = True
LOGISTIC_K = 0.18


def compute_recency_adjustment(home_wab, away_wab, ratings):

    wab_std = ratings["WAB"].std()
    if wab_std == 0:
        return 0

    wab_diff = home_wab - away_wab
    normalized = wab_diff / wab_std

    adjustment = normalized * RECENCY_WEIGHT * 4
    return np.clip(adjustment, -MAX_RECENCY_IMPACT, MAX_RECENCY_IMPACT)


def run_backtest():

    ratings = pd.read_csv("data/historical_efficiency_3yr.csv")
    games = pd.read_csv("historical_games_raw.csv")

    # Keep only 3 seasons
    games = games[games["date"].str.contains("2022|2023|2024")]

    games["date"] = pd.to_datetime(games["date"])
    games["SEASON"] = games["date"].dt.year.astype(str)

    results = []

    for _, game in games.iterrows():

        home = game["home_team"]
        away = game["away_team"]
        season_year = str(game["date"].year)

        season_map = {
            "2023": "2022-23",
            "2024": "2023-24",
            "2025": "2024-25"
        }

        if season_year not in season_map:
            continue

        season = season_map[season_year]

        season_ratings = ratings[ratings["SEASON"] == season]

        home_row = season_ratings[season_ratings["TEAM"].str.lower() == home.lower()]
        away_row = season_ratings[season_ratings["TEAM"].str.lower() == away.lower()]

        if home_row.empty or away_row.empty:
            continue

        home_row = home_row.iloc[0]
        away_row = away_row.iloc[0]

        poss = harmonic_tempo(home_row["TEMPO"], away_row["TEMPO"])

        home_adj_ortg = expected_ortg(home_row["ADJOE"], away_row["ADJDE"])
        away_adj_ortg = expected_ortg(away_row["ADJOE"], home_row["ADJDE"])

        home_pts = poss * home_adj_ortg / 100
        away_pts = poss * away_adj_ortg / 100

        spread = (home_pts - away_pts) + BASE_HOME_COURT

        recency_adj = compute_recency_adjustment(
            home_row["WAB"],
            away_row["WAB"],
            season_ratings
        )

        spread += recency_adj

        if USE_H2H:
            h2h_stats = get_h2h_stats(home, away)
            if h2h_stats:
                spread += H2H_WEIGHT * h2h_stats["avg_margin_team_a"]

        actual_margin = game["home_score"] - game["away_score"]

        edge = spread - actual_margin

        if abs(edge) >= EDGE_THRESHOLD_SPREAD:

            if (spread > 0 and actual_margin > 0) or (spread < 0 and actual_margin < 0):
                result = 1
            else:
                result = -1

            results.append({
                "DATE": game["date"],
                "HOME": home,
                "AWAY": away,
                "MODEL_SPREAD": round(spread, 2),
                "ACTUAL_MARGIN": actual_margin,
                "RESULT": result
            })

    df = pd.DataFrame(results)

    total_bets = len(df)
    wins = (df["RESULT"] == 1).sum()
    losses = (df["RESULT"] == -1).sum()

    win_pct = wins / total_bets if total_bets > 0 else 0

    print("\n===== V4 BACKTEST RESULTS =====")
    print(f"Total Bets: {total_bets}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Win %: {round(win_pct * 100, 2)}%")

    df.to_csv("data/v4_backtest_results.csv", index=False)
    print("\nSaved to data/v4_backtest_results.csv")


if __name__ == "__main__":
    run_backtest()
