import pandas as pd
import json
from team_normalizer import team_key

print("\n--- PROJECTION KEYS ---\n")

proj = pd.read_csv("data/projections.csv")

for _,r in proj.iterrows():
    if r["HOME"] in ["George Washington","Saint Louis"] or r["AWAY"] in ["St. Bonaventure","Loyola Chicago"]:
        print(r["HOME"], "->", team_key(r["HOME"]))
        print(r["AWAY"], "->", team_key(r["AWAY"]))
        print()

print("\n--- ODDS KEYS ---\n")

with open("data/market_odds.json") as f:
    odds=json.load(f)

for g in odds:
    if g["HOME"] in ["George Washington","Saint Louis","Saint Bonaventure","Loyola Chicago"] or g["AWAY"] in ["George Washington","Saint Louis","Saint Bonaventure","Loyola Chicago"]:
        print(g["HOME"], "->", team_key(g["HOME"]))
        print(g["AWAY"], "->", team_key(g["AWAY"]))
        print()
