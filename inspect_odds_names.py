import json

with open("data/market_odds.json","r") as f:
    data=json.load(f)

teams=set()

for g in data:
    teams.add(g["HOME"])
    teams.add(g["AWAY"])

teams=sorted(list(teams))

for t in teams:
    print(t)
