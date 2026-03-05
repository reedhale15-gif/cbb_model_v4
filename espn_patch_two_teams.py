import requests
import pandas as pd
import time

TEAM_IDS = ["2464", "2501"]  # Northern Arizona, Portland
SEASONS = [2021, 2022, 2023, 2024, 2025]

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{team_id}/schedule"

HISTORICAL_FILE = "historical_games_raw.csv"


def fetch_team_schedule(team_id, season):
    url = BASE_URL.format(team_id=team_id)
    params = {"season": season}
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


def run_patch():
    print("Loading existing dataset...")
    existing_df = pd.read_csv(HISTORICAL_FILE)
    existing_ids = set(existing_df["game_id"].astype(str))

    new_games = []

    for team_id in TEAM_IDS:
        for season in SEASONS:
            print(f"Pulling team {team_id} — season {season}")

            try:
                data = fetch_team_schedule(team_id, season)
                games = extract_completed_games(data)

                for game in games:
                    if game["game_id"] not in existing_ids:
                        new_games.append(game)

                time.sleep(0.3)

            except Exception as e:
                print(f"Error for team {team_id}: {e}")
                continue

    print(f"\nNew games found: {len(new_games)}")

    if new_games:
        patch_df = pd.DataFrame(new_games)
        updated_df = pd.concat([existing_df, patch_df], ignore_index=True)
        updated_df.to_csv(HISTORICAL_FILE, index=False)
        print("Dataset updated successfully.")
    else:
        print("No missing games to add.")


if __name__ == "__main__":
    run_patch()
