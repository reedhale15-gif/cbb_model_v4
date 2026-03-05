import requests
import os
import json
import pandas as pd
from team_normalizer import team_key

API_KEY = os.getenv("ODDS_API_KEY")

if not API_KEY:
    raise Exception("ODDS_API_KEY environment variable not set")

SPORT = "basketball_ncaab"
REGIONS = "us"
MARKETS = "spreads,totals,h2h"
ODDS_FORMAT = "american"


def load_projection_teams():
    df = pd.read_csv("data/efficiency_table.csv")
    df["KEY"] = df["TEAM"].apply(team_key)
    return df.set_index("KEY")["TEAM"].to_dict()


def clean_api_name(raw_name, team_map):

    parts = raw_name.split()

    key = team_key(raw_name)
    if key in team_map:
        return team_map[key]

    if len(parts) > 1:
        trimmed = " ".join(parts[:-1])
        key = team_key(trimmed)
        if key in team_map:
            return team_map[key]

    if len(parts) > 2:
        trimmed = " ".join(parts[:-2])
        key = team_key(trimmed)
        if key in team_map:
            return team_map[key]

    return None


def get_consensus(values):
    nums = [v for v in values if v is not None]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 2)


def scrape_odds():

    print("Pulling NCAA odds from The Odds API...")

    team_map = load_projection_teams()

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

    for event in data:

        home_raw = event["home_team"]
        away_raw = event["away_team"]

        home = clean_api_name(home_raw, team_map)
        away = clean_api_name(away_raw, team_map)

        if not home or not away:
            continue

        spreads = []
        totals = []
        home_ml = []

        for book in event.get("bookmakers", []):
            for market in book.get("markets", []):

                if market["key"] == "spreads":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == home_raw:
                            spreads.append(outcome.get("point"))

                if market["key"] == "totals":
                    for outcome in market["outcomes"]:
                        totals.append(outcome.get("point"))

                if market["key"] == "h2h":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == home_raw:
                            home_ml.append(outcome.get("price"))

        spread_consensus = get_consensus(spreads)
        total_consensus = get_consensus(totals)
        ml_consensus = get_consensus(home_ml)

        if spread_consensus is None:
            continue

        commence_time = event.get("commence_time")

        output.append({
            "HOME": home,
            "AWAY": away,
            "COMMENCE_TIME": commence_time,
            "SPREAD": spread_consensus,
            "TOTAL": total_consensus,
            "HOME_ML": ml_consensus
        })

    with open("data/market_odds.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Consensus odds saved.")
    print(f"Games pulled: {len(output)}")


if __name__ == "__main__":
    scrape_odds()
