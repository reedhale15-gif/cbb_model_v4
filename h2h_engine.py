import pandas as pd
import numpy as np
from datetime import datetime

MIN_GAMES_REQUIRED = 3
LAMBDA = 0.5  # exponential decay strength

# =========================
# NORMALIZE (MUST MATCH PULL SCRIPT)
# =========================

def normalize(name):
    name = name.lower()
    name = name.replace(".", "")
    name = name.replace("&", "and")
    name = name.replace("-", " ")
    name = name.replace(" state", "")
    name = name.replace(" st", "")
    name = name.replace(" university", "")
    name = name.replace(" a&m", "")
    return name.strip()

# =========================
# LOAD DATA
# =========================

df = pd.read_csv("historical_games_raw.csv")

# Convert date
df["date"] = pd.to_datetime(df["date"])
current_year = df["date"].dt.year.max()

# =========================
# BUILD MATCHUP INDEX
# =========================

matchups = {}

for _, row in df.iterrows():

    team_a = normalize(row["home_team"])
    team_b = normalize(row["away_team"])

    key = tuple(sorted([team_a, team_b]))

    margin = row["home_score"] - row["away_score"]
    total = row["home_score"] + row["away_score"]

    game_year = row["date"].year
    years_ago = current_year - game_year

    weight = np.exp(-LAMBDA * years_ago)

    if key not in matchups:
        matchups[key] = []

    matchups[key].append({
        "team_a": team_a,
        "team_b": team_b,
        "margin": margin,
        "total": total,
        "weight": weight
    })

# =========================
# GET H2H STATS (WEIGHTED)
# =========================

def get_h2h_stats(team_a, team_b):

    team_a = normalize(team_a)
    team_b = normalize(team_b)

    key = tuple(sorted([team_a, team_b]))

    if key not in matchups:
        return None

    data = matchups[key]

    if len(data) < MIN_GAMES_REQUIRED:
        return None

    weighted_margins = []
    weighted_totals = []
    weights = []

    for game in data:

        if game["team_a"] == team_a:
            margin = game["margin"]
        else:
            margin = -game["margin"]

        weighted_margins.append(margin * game["weight"])
        weighted_totals.append(game["total"] * game["weight"])
        weights.append(game["weight"])

    total_weight = sum(weights)

    if total_weight == 0:
        return None

    avg_margin = sum(weighted_margins) / total_weight
    avg_total = sum(weighted_totals) / total_weight

    return {
        "games_played": len(data),
        "avg_margin_team_a": avg_margin,
        "avg_total": avg_total
    }
