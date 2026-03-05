import pandas as pd
from h2h_engine import get_h2h_stats

print("\n========== GLOBAL H2H INTEGRITY CHECK ==========\n")

df = pd.read_csv("historical_games_raw.csv")

# Count matchups
matchup_counts = {}

for _, row in df.iterrows():
    key = tuple(sorted([row["home_team"], row["away_team"]]))
    matchup_counts[key] = matchup_counts.get(key, 0) + 1

total_matchups = 0
eligible_matchups = 0
failures = []

for key, count in matchup_counts.items():

    total_matchups += 1

    if count >= 3:
        eligible_matchups += 1

        team_a, team_b = key

        result = get_h2h_stats(team_a, team_b)

        if result is None:
            failures.append((team_a, team_b, count))

print(f"Total unique matchups: {total_matchups}")
print(f"Eligible matchups (3+ games): {eligible_matchups}")
print(f"Failures detected: {len(failures)}\n")

if failures:
    print("Sample Failures:")
    for f in failures[:10]:
        print(f"{f[0]} vs {f[1]} → {f[2]} games")
else:
    print("No failures detected. System integrity verified.")

print("\n================================================\n")
