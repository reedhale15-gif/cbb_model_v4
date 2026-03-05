import pandas as pd
import numpy as np
from scipy.optimize import minimize

# =========================
# LOAD HISTORICAL DATA
# =========================

games = pd.read_csv("historical_games_raw.csv")

# Compute margin and win flag
games["MARGIN"] = games["home_score"] - games["away_score"]
games["HOME_WIN"] = (games["MARGIN"] > 0).astype(int)

games = games.dropna(subset=["MARGIN", "HOME_WIN"])

# =========================
# LOGISTIC MODEL
# =========================

def logistic_prob(spread, k):
    return 1 / (1 + np.exp(-k * spread))

def negative_log_likelihood(k):
    k = k[0]
    probs = logistic_prob(games["MARGIN"], k)

    probs = np.clip(probs, 1e-9, 1 - 1e-9)

    log_likelihood = (
        games["HOME_WIN"] * np.log(probs) +
        (1 - games["HOME_WIN"]) * np.log(1 - probs)
    )

    return -np.sum(log_likelihood)

# =========================
# OPTIMIZE K
# =========================

result = minimize(
    negative_log_likelihood,
    x0=[0.1],
    bounds=[(0.01, 0.5)]
)

optimal_k = result.x[0]

print("\nOptimal Logistic K:", round(optimal_k, 4))
