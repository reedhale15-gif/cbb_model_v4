import pandas as pd
from projection_engine import harmonic_tempo, expected_ortg, TEMPO_INFLATION

ratings = pd.read_csv("data/efficiency_table.csv")

home = input("Home Team: ")
away = input("Away Team: ")

home_row = ratings[ratings["TEAM"] == home].iloc[0]
away_row = ratings[ratings["TEAM"] == away].iloc[0]

poss = harmonic_tempo(home_row["TEMPO"], away_row["TEMPO"])
poss *= TEMPO_INFLATION

home_adj_ortg = expected_ortg(home_row["ADJOE"], away_row["ADJDE"])
away_adj_ortg = expected_ortg(away_row["ADJOE"], home_row["ADJDE"])

home_pts = poss * home_adj_ortg / 100
away_pts = poss * away_adj_ortg / 100

spread = home_pts - away_pts
total = home_pts + away_pts

print("\n--- MODEL TEST ---")
print(f"Possessions: {poss:.2f}")
print(f"Home Adj ORtg: {home_adj_ortg:.2f}")
print(f"Away Adj ORtg: {away_adj_ortg:.2f}")
print(f"Home Points: {home_pts:.2f}")
print(f"Away Points: {away_pts:.2f}")
print(f"Spread (Home - Away): {spread:.2f}")
print(f"Total: {total:.2f}")
