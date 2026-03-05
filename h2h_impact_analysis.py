import pandas as pd

print("\n========== H2H IMPACT ANALYSIS ==========\n")

base = pd.read_csv("data/projections_base_clean.csv")
h2h = pd.read_csv("data/projections_h2h_weighted.csv")

merged = base.merge(
    h2h,
    on=["HOME", "AWAY"],
    suffixes=("_BASE", "_H2H")
)

merged["SPREAD_MOVE"] = abs(
    merged["SPREAD_PROJ_H2H"] - merged["SPREAD_PROJ_BASE"]
)

merged["TOTAL_MOVE"] = abs(
    merged["TOTAL_PROJ_H2H"] - merged["TOTAL_PROJ_BASE"]
)

total_games = len(merged)

spread_moves = merged["SPREAD_MOVE"]
total_moves = merged["TOTAL_MOVE"]

h2h_applied = merged["H2H_USED_H2H"].sum()

print(f"Total games analyzed: {total_games}\n")

print("--- Spread Impact ---")
print(f"Average movement: {spread_moves.mean():.3f}")
print(f"Max movement: {spread_moves.max():.3f}")
print(f"> 0.5 pts moved: {(spread_moves > 0.5).sum()} "
      f"({(spread_moves > 0.5).mean()*100:.2f}%)")
print(f"> 1.0 pts moved: {(spread_moves > 1.0).sum()} "
      f"({(spread_moves > 1.0).mean()*100:.2f}%)\n")

print("--- Total Impact ---")
print(f"Average movement: {total_moves.mean():.3f}")
print(f"Max movement: {total_moves.max():.3f}")
print(f"> 0.5 pts moved: {(total_moves > 0.5).sum()} "
      f"({(total_moves > 0.5).mean()*100:.2f}%)")
print(f"> 1.0 pts moved: {(total_moves > 1.0).sum()} "
      f"({(total_moves > 1.0).mean()*100:.2f}%)\n")

print(f"H2H applied to {int(h2h_applied)} games "
      f"({h2h_applied/total_games*100:.2f}% of slate)")

print("\n==========================================\n")
