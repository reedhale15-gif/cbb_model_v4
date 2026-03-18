import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import json
from model_config import TOTAL_EDGE_MAX, TOTAL_EDGE_MIN, active_mode_label, spread_bet_qualifies, spread_edge_band
from teams.team_normalizer import team_key
from teams.team_name_normalizer import normalize_team

EDGE_THRESHOLD_TOTAL = TOTAL_EDGE_MIN
MAX_TOTAL_EDGE = TOTAL_EDGE_MAX


def round_half(x):
    return round(float(x) * 2) / 2


def load_market_odds():
    with open("data/market_odds.json", "r") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def run_edge_engine():
    min_spread_edge, max_spread_edge = spread_edge_band()

    projections = pd.read_csv("data/projections.csv")
    efficiency = pd.read_csv("data/efficiency_table.csv")
    market = load_market_odds()

    # NORMALIZE MARKET TEAM NAMES
    market["HOME"] = market["HOME"].apply(normalize_team)
    market["AWAY"] = market["AWAY"].apply(normalize_team)

    projections["HOME_KEY"] = projections["HOME"].apply(team_key)
    projections["AWAY_KEY"] = projections["AWAY"].apply(team_key)

    market["HOME_KEY"] = market["HOME"].apply(team_key)
    market["AWAY_KEY"] = market["AWAY"].apply(team_key)

    engine_rows = []
    qualified_rows = []

    for _, proj in projections.iterrows():

        home_key = proj["HOME_KEY"]
        away_key = proj["AWAY_KEY"]

        game = market[
            ((market["HOME_KEY"] == home_key) &
             (market["AWAY_KEY"] == away_key)) |
            ((market["HOME_KEY"] == away_key) &
             (market["AWAY_KEY"] == home_key))
        ]

        if game.empty:
            continue

        game = game.iloc[0]

        market_spread = round_half(game["SPREAD"])
        market_total = round_half(game["TOTAL"])

        model_spread = proj["SPREAD_PROJ"]
        model_total = proj["TOTAL_PROJ"]

        spread_edge = model_spread - market_spread
        total_edge = model_total - market_total

        home_eff = efficiency[efficiency["TEAM"] == proj["HOME"]].iloc[0]
        away_eff = efficiency[efficiency["TEAM"] == proj["AWAY"]].iloc[0]

        oe_diff = home_eff["ADJOE"] - away_eff["ADJOE"]
        de_diff = away_eff["ADJDE"] - home_eff["ADJDE"]

        # ---------------------------
        # ENGINE OUTPUT
        # ---------------------------

        engine_rows.append({
            "Game Time": game.get("COMMENCE_TIME"),
            "Home": proj["HOME"],
            "Away": proj["AWAY"],
            "Spread": market_spread,
            "Total": market_total,
            "OE Diff": oe_diff,
            "DE Diff": de_diff,
            "Spread Edge": spread_edge,
            "Model Spread": model_spread,
            "Total Edge": total_edge,
            "Model Total": model_total
        })

        # ---------------------------
        # QUALIFICATION LOGIC
        # ---------------------------

        spread_ok = spread_bet_qualifies(
            market_spread,
            model_spread,
            spread_edge
        )

        total_ok = (
            abs(total_edge) >= EDGE_THRESHOLD_TOTAL
            and abs(total_edge) <= MAX_TOTAL_EDGE
        )

        if spread_ok or total_ok:

            qualified_rows.append({
                "Home": proj["HOME"],
                "Away": proj["AWAY"],
                "Spread": market_spread,
                "Model Spread": model_spread,
                "Spread Edge": spread_edge,
                "Total": market_total,
                "Model Total": model_total,
                "Total Edge": total_edge
            })

    pd.DataFrame(engine_rows).to_csv("data/engine.csv", index=False)
    pd.DataFrame(qualified_rows).to_csv("data/qualified_bets.csv", index=False)

    print(
        f"Edge mode: {active_mode_label()} "
        f"(spread band {min_spread_edge}-{max_spread_edge})"
    )
    print("Engine slate saved.")
    print("Qualified bets saved.")


if __name__ == "__main__":
    run_edge_engine()
