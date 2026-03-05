import pandas as pd
import numpy as np

LEAGUE_AVG = 109.55
BASE_HOME_COURT = 3.0
TEMPO_INFLATION = 1.03

def harmonic_tempo(t1, t2):
    return 2 * (t1 * t2) / (t1 + t2)

def expected_ortg(off, opp_def):
    return off + (LEAGUE_AVG - opp_def)

def run_calibration():

    ratings = pd.read_csv("data/efficiency_table.csv")
    games = pd.read_csv("historical_games_raw.csv")

    games = games[games["neutral_site"] == False]

    games["home_team"] = games["home_team"].str.strip()
    games["away_team"] = games["away_team"].str.strip()

    ratings["TEAM"] = ratings["TEAM"].str.strip()

    merged = games.merge(
        ratings.add_prefix("HOME_"),
        left_on="home_team",
        right_on="HOME_TEAM",
        how="inner"
    )

    merged = merged.merge(
        ratings.add_prefix("AWAY_"),
        left_on="away_team",
        right_on="AWAY_TEAM",
        how="inner"
    )

    # TEMPO
    merged["POSSESSIONS"] = harmonic_tempo(
        merged["HOME_TEMPO"],
        merged["AWAY_TEMPO"]
    ) * TEMPO_INFLATION

    # MATCHUP
    merged["HOME_ADJ_OR"] = expected_ortg(
        merged["HOME_ADJOE"],
        merged["AWAY_ADJDE"]
    )

    merged["AWAY_ADJ_OR"] = expected_ortg(
        merged["AWAY_ADJOE"],
        merged["HOME_ADJDE"]
    )

    merged["HOME_PROJ"] = merged["POSSESSIONS"] * merged["HOME_ADJ_OR"] / 100
    merged["AWAY_PROJ"] = merged["POSSESSIONS"] * merged["AWAY_ADJ_OR"] / 100

    base_spread = merged["HOME_PROJ"] - merged["AWAY_PROJ"] + BASE_HOME_COURT

    home_net = merged["HOME_ADJOE"] - merged["HOME_ADJDE"]
    away_net = merged["AWAY_ADJOE"] - merged["AWAY_ADJDE"]
    net_gap = home_net - away_net

    X = np.vstack([base_spread, net_gap]).T
    y = merged["home_score"] - merged["away_score"]

    beta = np.linalg.lstsq(X, y, rcond=None)[0]

    print("\n===== OPTIMAL WEIGHTS =====")
    print("BETA_BASE =", round(beta[0], 4))
    print("BETA_NET  =", round(beta[1], 4))
    print("\nSample Size:", len(merged))

if __name__ == "__main__":
    run_calibration()
