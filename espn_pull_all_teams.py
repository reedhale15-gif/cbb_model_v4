import requests
import pandas as pd
import time

# =========================
# SETTINGS
# =========================

SEASONS = [2021, 2022, 2023, 2024, 2025]
BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"

# =========================
# NORMALIZE (ROOT LEVEL)
# =========================

def normalize(name):
    name = name.lower()
    name = name.replace(".", "")
    name = name.replace("&", "and")
    name = name.replace("-", " ")
    name = name.replace(" state", "")
    name = name.replace(" st", "")
    name = name.replace(" university", "")
    name = name.replace(" a&m", "")
    return name.strip()

# =========================
# LOAD TEAM IDS
# =========================

teams_df = pd.read_csv("data/d1_team_ids.csv")

all_games = []

print("Starting FULL clean rebuild...\n")

for _, row in teams_df.iterrows():

    team_id = row["team_id"]

    for season in SEASONS:

        print(f"Pulling team {team_id} — season {season}")

        try:
            url = f"{BASE_URL}/teams/{team_id}/schedule?season={season}"
            response = requests.get(url, timeout=10)
            data = response.json()

            events = data.get("events", [])

            for event in events:

                comp = event["competitions"][0]

                # Only completed games
                if comp["status"]["type"]["completed"] is not True:
                    continue

                competitors = comp["competitors"]

                home = None
                away = None
                home_score = None
                away_score = None

                for c in competitors:

                    location = c["team"]["location"]

                    if c["homeAway"] == "home":
                        home = normalize(location)
                        home_score = int(float(c["score"]["value"]))
                    else:
                        away = normalize(location)
                        away_score = int(float(c["score"]["value"]))

                if home and away:

                    all_games.append({
                        "game_id": event["id"],
                        "date": event["date"],
                        "home_team": home,
                        "away_team": away,
                        "home_score": home_score,
                        "away_score": away_score,
                        "neutral_site": comp.get("neutralSite", False)
                    })

            time.sleep(0.2)

        except Exception as e:
            print(f"Error for team {team_id}: {e}")

# =========================
# DEDUPE + SAVE
# =========================

df = pd.DataFrame(all_games)

df = df.drop_duplicates(subset="game_id")

print(f"\nTotal unique games collected: {len(df)}")

df.to_csv("historical_games_raw.csv", index=False)

print("Saved full dataset to historical_games_raw.csv")
