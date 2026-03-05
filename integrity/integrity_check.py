import json
import pandas as pd

print("\n==============================")
print("MODEL INTEGRITY CHECK")
print("==============================\n")

# Load data
odds = pd.DataFrame(json.load(open("data/market_odds.json")))
ratings = pd.read_csv("data/efficiency_table.csv")
projections = pd.read_csv("data/projections.csv")

print("Odds Games Pulled:", len(odds))
print("Projected Games:", len(projections))

# -----------------------------
# Check for missing projections
# -----------------------------

odds_games = set(zip(odds.HOME, odds.AWAY))
proj_games = set(zip(projections.HOME, projections.AWAY))

missing_games = odds_games - proj_games
extra_games = proj_games - odds_games

print("\nMissing From Projections:", len(missing_games))
if missing_games:
    for g in missing_games:
        print("   ", g)

print("\nExtra In Projections:", len(extra_games))
if extra_games:
    for g in extra_games:
        print("   ", g)

# -----------------------------
# Check team matching
# -----------------------------

rating_teams = set(ratings["TEAM"])

missing_teams = set()

for _, g in odds.iterrows():
    if g["HOME"] not in rating_teams:
        missing_teams.add(g["HOME"])
    if g["AWAY"] not in rating_teams:
        missing_teams.add(g["AWAY"])

print("\nTeams Missing From Efficiency Table:", len(missing_teams))

if missing_teams:
    print("\nMissing Team Names:")
    for t in sorted(missing_teams):
        print("   ", t)

# -----------------------------
# Totals sanity check
# -----------------------------

print("\nTotals Range:")
print("Lowest:", projections["TOTAL_PROJ"].min())
print("Highest:", projections["TOTAL_PROJ"].max())
print("Average:", projections["TOTAL_PROJ"].mean())

print("\nSpread Range:")
print("Largest Favorite:", projections["SPREAD_PROJ"].min())
print("Largest Underdog:", projections["SPREAD_PROJ"].max())

print("\n==============================")
print("CHECK COMPLETE")
print("==============================\n")
