import pandas as pd
import numpy as np

STAKE = 100
TOTAL_EDGE_FLOOR = 4.0

TEMPO_INFLATION = 1.03  # structural test (max 3% allowed)


def calculate_profit(result):
    if result == 1:
        return STAKE * (100 / 110)
    elif result == -1:
        return -STAKE
    else:
        return 0


def summarize(results, label):

    total_bets = len(results)
    wins = results.count(1)
    losses = results.count(-1)

    if total_bets == 0:
        print(f"\n===== {label} =====")
        print("No bets")
        return

    win_pct = wins / (wins + losses)
    profit = sum(calculate_profit(r) for r in results)
    roi = profit / (total_bets * STAKE)

    print(f"\n===== {label} =====")
    print(f"Bets: {total_bets}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Win %: {round(win_pct*100,2)}%")
    print(f"ROI: {round(roi*100,2)}%")


def run_v4_backtest():

    df = pd.read_csv(
        "/Users/reedhale/Documents/CBB_Model/engine_inputs/backtest_results_2016.csv"
    )

    # =========================
    # STRUCTURAL TOTAL TEST
    # =========================

    df["MODEL_TOTAL_RAW"] = df["HOME_PROJ_POINTS"] + df["AWAY_PROJ_POINTS"]

    # simulate tempo lift
    df["MODEL_TOTAL"] = df["MODEL_TOTAL_RAW"] * TEMPO_INFLATION

    print("\n==============================")
    print("TOTALS DIAGNOSTICS (3% Lift)")
    print("==============================")

    print("Model Total Mean:", df["MODEL_TOTAL"].mean())
    print("Market Total Mean:", df["over_under"].mean())
    print("Correlation vs Market:",
          np.corrcoef(df["MODEL_TOTAL"], df["over_under"])[0,1])
    print("Correlation vs Actual:",
          np.corrcoef(
              df["MODEL_TOTAL"],
              df["home.score"] + df["away.score"]
          )[0,1])

    df["TOTAL_EDGE"] = df["MODEL_TOTAL"] - df["over_under"]

    overs = []
    unders = []

    for _, row in df.iterrows():

        total_edge = row["TOTAL_EDGE"]
        actual_total = row["home.score"] + row["away.score"]
        market_total = row["over_under"]

        if abs(total_edge) >= TOTAL_EDGE_FLOOR:

            bet_over = total_edge > 0

            if bet_over:
                result = 1 if actual_total > market_total else -1
                overs.append(result)
            else:
                result = 1 if actual_total < market_total else -1
                unders.append(result)

    print("\n==============================")
    print("TOTAL RESULTS")
    print("==============================")

    summarize(overs, "OVERS")
    summarize(unders, "UNDERS")


if __name__ == "__main__":
    run_v4_backtest()
