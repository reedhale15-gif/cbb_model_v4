import pandas as pd

BETS_FILE = "data/qualified_bets.csv"
SCORES_FILE = "data/results_archive.csv"
OUTPUT_FILE = "data/model_performance.csv"


def spread_result(row):

    if pd.isna(row["HOME_SCORE"]):
        return ""

    spread = row["Spread"]
    home_score = row["HOME_SCORE"]
    away_score = row["AWAY_SCORE"]

    if home_score + spread > away_score:
        return "W"

    if home_score + spread < away_score:
        return "L"

    return "P"


def total_result(row):

    if pd.isna(row["HOME_SCORE"]):
        return ""

    total = row["Total"]
    game_total = row["HOME_SCORE"] + row["AWAY_SCORE"]

    if game_total > total:
        return "W"

    if game_total < total:
        return "L"

    return "P"


def main():

    bets = pd.read_csv(BETS_FILE)
    scores = pd.read_csv(SCORES_FILE)

    rows = []

    for _, bet in bets.iterrows():

        home = bet["Home"].lower()
        away = bet["Away"].lower()

        match = scores[
            scores["HOME"].str.lower().str.contains(home) &
            scores["AWAY"].str.lower().str.contains(away)
        ]

        if not match.empty:
            game = match.iloc[0]
            bet["HOME_SCORE"] = game["HOME_SCORE"]
            bet["AWAY_SCORE"] = game["AWAY_SCORE"]
        else:
            bet["HOME_SCORE"] = None
            bet["AWAY_SCORE"] = None

        rows.append(bet)

    merged = pd.DataFrame(rows)

    merged["SPREAD_RESULT"] = merged.apply(spread_result, axis=1)
    merged["TOTAL_RESULT"] = merged.apply(total_result, axis=1)

    merged.to_csv(OUTPUT_FILE, index=False)

    print("Model performance file created.")


if __name__ == "__main__":
    main()
