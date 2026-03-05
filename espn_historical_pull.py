import requests
import csv
import time
import pandas as pd

TEAM_FILE = "data/d1_team_ids.csv"
OUTPUT_FILE = "historical_games_raw.csv"

SEASONS = [2021, 2022, 2023, 2024, 2025]

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{team_id}/schedule"


def load_team_ids():
    df = pd.read_csv(TEAM_FILE)
    return df["team_id"].astype(str).tolist()


def fetch_team_schedule(team_id, season):
    url = BASE_URL.format(team_id=team_id)

    params = {
        "season": season
    }

    response = requests.get(url, params=params)
    return response.json()


def extract_completed_games(schedule_json):
    games = []

    if "events" not in schedule_json:
        return games

    for event in schedule_json["events"]:
        comp = event["competitions"][0]
        status = comp["status"]["type"]["completed"]

        if not status:
            continue

        competitors = comp["competitors"]

        home = None
        away = None
        home_score = None
        away_score = None

        for team in competitors:
            name = team["team"]["displayName"]
            score = int(float(team["score"]["value"]))
            if team["homeAway"] == "home":
                home = name
                home_score = score
            else:
                away = name
                away_score = score

        games.append({
            "game_id": event["id"],
            "date": event["date"],
            "home_team": home,
            "away_team": away,
            "home_score": home_score,
            "away_score": away_score,
            "neutral_site": comp.get("neutralSite", False)
        })

    return games


def run_pull():
    team_ids = load_team_ids()

    all_games = []
    seen_games = set()

    for season in SEASONS:
        print(f"\n========== SEASON {season} ==========\n")

        for idx, team_id in enumerate(team_ids):
            print(f"Team {idx+1}/{len(team_ids)} — Season {season}")

            try:
                data = fetch_team_schedule(team_id, season)
                games = extract_completed_games(data)

                for game in games:
                    if game["game_id"] not in seen_games:
                        seen_games.add(game["game_id"])
                        all_games.append(game)

                time.sleep(0.3)

            except Exception as e:
                print(f"Error for team {team_id}: {e}")
                continue

    print(f"\nTotal unique games collected: {len(all_games)}")

    df = pd.DataFrame(all_games)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved full dataset to {OUTPUT_FILE}")


if __name__ == "__main__":
    run_pull()
