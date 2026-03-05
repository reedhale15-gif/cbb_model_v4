import pandas as pd

df = pd.read_csv("data/projections.csv")

teams = set()

for _,row in df.iterrows():
    teams.add(row["HOME"])
    teams.add(row["AWAY"])

teams = sorted(list(teams))

for t in teams:
    print(t)
