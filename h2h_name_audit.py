import pandas as pd
from h2h_engine import get_h2h_stats, normalize

print("\n========== H2H NAME AUDIT ==========\n")

schedule = pd.read_csv("data/bart_schedule_clean.csv")

df_hist = pd.read_csv("historical_games_raw.csv")

# Build matchup count table
matchup_counts = {}

for _, row in df_hist.iterrows():
    key = tuple(sorted([row["home_team"], row["away_team"]]))
    matchup_counts[key] = matchup_counts.get(key, 0) + 1

problem_games = []

for _, game in schedule.iterrows():

    home = game["HOME"]
    away = game["AWAY"]

    norm_home = normalize(home)
    norm_away = normalize(away)

    key = tuple(sorted([norm_home, norm_away]))

    historical_count = matchup_counts.get(key, 0)
    h2h_result = get_h2h_stats(home, away)

    if historical_count >= 3 and h2h_result is None:
        problem_games.append({
            "HOME": home,
            "AWAY": away,
            "Historical_Games": historical_count
        })

print(f"Total games on slate: {len(schedule)}")
print(f"Problem games found: {len(problem_games)}\n")

for game in problem_games:
    print(f"{game['HOME']} vs {game['AWAY']} → "
          f"{game['Historical_Games']} historical games but H2H not triggering")

print("\n=====================================\n")
