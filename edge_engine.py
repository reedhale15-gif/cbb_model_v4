import pandas as pd
import json
from team_normalizer import team_key

EDGE_THRESHOLD_SPREAD = 4.0
EDGE_THRESHOLD_TOTAL = 6.0


def round_half(x):
    return round(float(x) * 2) / 2


def load_market_odds():
    with open("data/market_odds.json", "r") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def run_edge_engine():

    projections = pd.read_csv("data/projections.csv")
    efficiency = pd.read_csv("data/efficiency_table.csv")
    market = load_market_odds()

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
            market_spread = float("nan")
            market_total = float("nan")
            spread_edge = float("nan")
            total_edge = float("nan")
            oe_diff = float("nan")
            de_diff = float("nan")

        else:

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

        engine_rows.append({
            "Home": proj["HOME"],
            "Away": proj["AWAY"],
            "Spread": market_spread,
            "Total": market_total,
            "OE Diff": oe_diff,
            "DE Diff": de_diff,
            "Spread Edge": spread_edge,
            "Model Spread": proj["SPREAD_PROJ"],
            "Total Edge": total_edge,
            "Model Total": proj["TOTAL_PROJ"]
        })

        spread_ok = not pd.isna(spread_edge) and abs(spread_edge) >= EDGE_THRESHOLD_SPREAD
        total_ok = not pd.isna(total_edge) and abs(total_edge) >= EDGE_THRESHOLD_TOTAL

        if spread_ok or total_ok:
            qualified_rows.append({
                "Home": proj["HOME"],
                "Away": proj["AWAY"],
                "Spread": market_spread,
                "Model Spread": proj["SPREAD_PROJ"],
                "Spread Edge": spread_edge,
                "Total": market_total,
                "Model Total": proj["TOTAL_PROJ"],
                "Total Edge": total_edge
            })

    pd.DataFrame(engine_rows).to_csv("data/engine.csv", index=False)
    pd.DataFrame(qualified_rows).to_csv("data/qualified_bets.csv", index=False)

    print("Engine slate saved.")
    print("Qualified bets saved.")


if __name__ == "__main__":
    run_edge_engine()
