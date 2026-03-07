import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import pandas as pd

from teams.team_name_normalizer import normalize_team, report_unknown

API_KEY = os.getenv("ODDS_API_KEY")

if not API_KEY:
    raise Exception("ODDS_API_KEY environment variable not set")

SPORT = "basketball_ncaab"
REGIONS = "us"
MARKETS = "spreads,totals,h2h"
ODDS_FORMAT = "american"


def get_consensus(values):
    nums = [v for v in values if v is not None]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 2)


def scrape_odds():

    print("Pulling NCAA odds from The Odds API...")

    # -----------------------------
    # LOAD TODAY'S TORVIK SCHEDULE
    # -----------------------------

    schedule = pd.read_csv("data/bart_schedule_clean.csv")

    valid_games = set()

    for _, row in schedule.iterrows():

        home = normalize_team(str(row["HOME"]).strip())
        away = normalize_team(str(row["AWAY"]).strip())

        valid_games.add((away, home))

    # -----------------------------
    # ODDS API REQUEST
    # -----------------------------

    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"

    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
    }

    resp = requests.get(url, params=params)

    if resp.status_code != 200:
        raise Exception(f"API Error: {resp.text}")

    data = resp.json()

    output = []

    # -----------------------------
    # PROCESS EVENTS
    # -----------------------------

    for event in data:

        home_raw = event["home_team"]
        away_raw = event["away_team"]

        home = normalize_team(home_raw)
        away = normalize_team(away_raw)

        spreads = []
        totals = []
        home_ml = []

        for book in event.get("bookmakers", []):

            for market in book.get("markets", []):

                # -----------------------------
                # SPREADS
                # -----------------------------

                if market["key"] == "spreads":

                    for outcome in market["outcomes"]:

                        outcome_team = normalize_team(outcome["name"])

                        if outcome_team == home:
                            spreads.append(outcome.get("point"))

                # -----------------------------
                # TOTALS
                # -----------------------------

                if market["key"] == "totals":

                    for outcome in market["outcomes"]:
                        totals.append(outcome.get("point"))

                # -----------------------------
                # MONEYLINE
                # -----------------------------

                if market["key"] == "h2h":

                    for outcome in market["outcomes"]:

                        outcome_team = normalize_team(outcome["name"])

                        if outcome_team == home:
                            home_ml.append(outcome.get("price"))

        spread_consensus = get_consensus(spreads)
        total_consensus = get_consensus(totals)
        ml_consensus = get_consensus(home_ml)

        if spread_consensus is None:
            continue

        if (away, home) not in valid_games and (home, away) not in valid_games:
            continue

        output.append({
            "HOME": home,
            "AWAY": away,
            "COMMENCE_TIME": event.get("commence_time"),
            "SPREAD": spread_consensus,
            "TOTAL": total_consensus,
            "HOME_ML": ml_consensus
        })

    # -----------------------------
    # SAVE OUTPUT
    # -----------------------------

    with open("data/market_odds.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Consensus odds saved.")
    print("Games pulled:", len(output))


if __name__ == "__main__":
    scrape_odds()
    report_unknown()
