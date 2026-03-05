import pandas as pd

ratings = pd.read_csv("data/efficiency_table.csv")

home = input("Home Team: ")
away = input("Away Team: ")

home_row = ratings[ratings["TEAM"] == home].iloc[0]
away_row = ratings[ratings["TEAM"] == away].iloc[0]

shooting_edge = home_row["EFG"] - away_row["EFGD"]
turnover_edge = away_row["TORD"] - home_row["TOR"]
rebound_edge = home_row["ORB"] - away_row["DRB"]

factor_edge = (
    0.35 * shooting_edge +
    0.30 * turnover_edge +
    0.25 * rebound_edge
)

print("\n--- FOUR FACTOR TEST ---")
print("Shooting Edge:", round(shooting_edge,3))
print("Turnover Edge:", round(turnover_edge,3))
print("Rebound Edge:", round(rebound_edge,3))
print("Factor Adjustment:", round(factor_edge,3))
