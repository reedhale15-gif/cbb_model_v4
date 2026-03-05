import pandas as pd
import json
from team_normalizer import team_key

projections = pd.read_csv("data/projections.csv")

with open("data/market_odds.json","r") as f:
    odds = pd.DataFrame(json.load(f))

projections["HOME_KEY"] = projections["HOME"].apply(team_key)
projections["AWAY_KEY"] = projections["AWAY"].apply(team_key)

odds["HOME_KEY"] = odds["HOME"].apply(team_key)
odds["AWAY_KEY"] = odds["AWAY"].apply(team_key)

market_games = set(zip(odds.HOME_KEY, odds.AWAY_KEY))

missing = []

for _,row in projections.iterrows():

    h=row["HOME_KEY"]
    a=row["AWAY_KEY"]

    if (h,a) not in market_games and (a,h) not in market_games:
        missing.append((row["HOME"],row["AWAY"]))

print("\nUNMATCHED GAMES:\n")

for g in missing:
    print(g)

print("\nTotal unmatched:",len(missing))
