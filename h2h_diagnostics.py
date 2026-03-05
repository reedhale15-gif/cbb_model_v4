import csv
from collections import defaultdict
from statistics import mean, stdev

HISTORICAL_FILE = "historical_games_raw.csv"


def normalize(name):
    return (
        name.lower()
        .replace(".", "")
        .replace("-", " ")
        .replace("&", "and")
        .strip()
    )


def load_games():
    games = []

    with open(HISTORICAL_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            home = normalize(row["home_team"])
            away = normalize(row["away_team"])

            try:
                home_score = int(row["home_score"])
                away_score = int(row["away_score"])
            except:
                continue

            games.append({
                "home": home,
                "away": away,
                "home_score": home_score,
                "away_score": away_score
            })

    return games


def build_matchups(games):
    matchup_data = defaultdict(list)

    for game in games:
        home = game["home"]
        away = game["away"]

        key = tuple(sorted([home, away]))

        margin = game["home_score"] - game["away_score"]
        total = game["home_score"] + game["away_score"]

        matchup_data[key].append({
            "margin": margin,
            "total": total,
            "home": home,
            "away": away
        })

    return matchup_data


def run_diagnostics():
    games = load_games()
    matchups = build_matchups(games)

    print("\n========== H2H DIAGNOSTICS ==========\n")

    total_matchups = len(matchups)
    print(f"Total unique matchups: {total_matchups}")

    games_per_matchup = [len(v) for v in matchups.values()]

    over_3 = sum(1 for g in games_per_matchup if g >= 3)
    over_5 = sum(1 for g in games_per_matchup if g >= 5)
    over_7 = sum(1 for g in games_per_matchup if g >= 7)

    print(f"Matchups with 3+ games: {over_3} ({over_3/total_matchups:.2%})")
    print(f"Matchups with 5+ games: {over_5} ({over_5/total_matchups:.2%})")
    print(f"Matchups with 7+ games: {over_7} ({over_7/total_matchups:.2%})")

    avg_games = mean(games_per_matchup)
    print(f"\nAverage games per matchup: {avg_games:.2f}")

    # Margin and total distributions
    all_margins = []
    all_totals = []

    for matchup in matchups.values():
        margins = []
        totals = []

        for g in matchup:
            margins.append(g["margin"])
            totals.append(g["total"])

        if len(margins) >= 3:
            all_margins.append(mean(margins))
            all_totals.append(mean(totals))

    print(f"\nEligible matchups (3+ games): {len(all_margins)}")

    if all_margins:
        print(f"Avg H2H margin mean: {mean(all_margins):.2f}")
        print(f"Avg H2H margin std dev: {stdev(all_margins):.2f}")
        print(f"Max H2H margin bias: {max(all_margins):.2f}")
        print(f"Min H2H margin bias: {min(all_margins):.2f}")

    if all_totals:
        print(f"\nAvg H2H total mean: {mean(all_totals):.2f}")
        print(f"Avg H2H total std dev: {stdev(all_totals):.2f}")
        print(f"Max H2H total bias: {max(all_totals):.2f}")
        print(f"Min H2H total bias: {min(all_totals):.2f}")

    print("\n=====================================\n")


if __name__ == "__main__":
    run_diagnostics()
