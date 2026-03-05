import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path.home() / "Documents" / "CBB_Model"

TEAM_STATS_FILE = BASE_DIR / "engine_inputs" / "engine_team_stats_full_2016.csv"
GAMES_FILE = BASE_DIR / "ingestion" / "ncaab_game_scores_1g.csv"
TEAM_MASTER_FILE = BASE_DIR / "ingestion" / "team_master.csv"

LEAGUE_AVG = 100
BASE_HOME_COURT = 3.0
EDGE_THRESHOLD = 6.5
STAKE = 100
MIN_TRAIN = 400   # minimum games before starting walk-forward

ratings = pd.read_csv(TEAM_STATS_FILE)

games_raw = pd.read_csv(
    GAMES_FILE,
    sep=",",
    skiprows=1,
    names=["season","date","away_team","away_score","home_team","home_score","line","over_under"]
)

games_raw = games_raw[games_raw["season"] != "season"].reset_index(drop=True)
games_raw["away_score"] = games_raw["away_score"].astype(float)
games_raw["home_score"] = games_raw["home_score"].astype(float)
games_raw["line"] = games_raw["line"].astype(float)
games_raw["date"] = pd.to_datetime(games_raw["date"])

KAGGLE_MAP = {
"AAMU":"Alabama A&M","AFA":"Air Force","AKR":"Akron","ALA":"Alabama",
"ALBY":"Albany (NY)","ALCN":"Alcorn State","ALST":"Alabama State",
"AMER":"American","APP":"Appalachian State","ARIZ":"Arizona",
"ARK":"Arkansas","ARPB":"Arkansas-Pine Bluff","ARST":"Arkansas State",
"ASU":"Arizona State","AUB":"Auburn","BALL":"Ball State","BAY":"Baylor",
"BC":"Boston College","BEL":"Belmont","BGSU":"Bowling Green State",
"BING":"Binghamton","BRAD":"Bradley","BRWN":"Brown","BRY":"Bryant",
"BSU":"Boise State","BU":"Boston University","BUCK":"Bucknell",
"BUFF":"Buffalo","BUT":"Butler","BYU":"BYU","CAL":"California",
"CAMP":"Campbell","CAN":"Canisius","CARK":"Central Arkansas",
"CCAR":"Coastal Carolina","CCSU":"Central Connecticut",
"CHAR":"Charlotte","CHAT":"Chattanooga","CIN":"Cincinnati",
"CLEM":"Clemson","CLEV":"Cleveland State","CLMB":"Columbia",
"CMU":"Central Michigan","COLO":"Colorado","CONN":"Connecticut",
"COR":"Cornell","CREI":"Creighton","DAV":"Davidson","DAY":"Dayton",
"DEP":"DePaul","DET":"Detroit Mercy","DUKE":"Duke","DUQ":"Duquesne",
"ECU":"East Carolina","EIU":"Eastern Illinois","ELON":"Elon",
"EMU":"Eastern Michigan","FAU":"Florida Atlantic",
"FGCU":"Florida Gulf Coast","FIU":"Florida International",
"FLA":"Florida","FRES":"Fresno State","FSU":"Florida State",
"GEO":"Georgetown","GONZ":"Gonzaga","GT":"Georgia Tech",
"GTWN":"Georgetown","HALL":"Seton Hall","HARV":"Harvard",
"HOU":"Houston","ILL":"Illinois","IND":"Indiana","IONA":"Iona",
"ISU":"Iowa State","JMU":"James Madison","KAN":"Kansas",
"KENT":"Kent State","KU":"Kansas","KY":"Kentucky","LSU":"LSU",
"LOU":"Louisville","MARQ":"Marquette","MD":"Maryland",
"MIA":"Miami (FL)","MICH":"Michigan","MSU":"Michigan State",
"MIZZ":"Missouri","MINN":"Minnesota","MISS":"Ole Miss",
"NC":"North Carolina","NCST":"NC State","NEB":"Nebraska",
"NEV":"Nevada","NMSU":"New Mexico State","ND":"Notre Dame",
"NW":"Northwestern","OKLA":"Oklahoma","OKST":"Oklahoma State",
"ORE":"Oregon","OSU":"Ohio State","PSU":"Penn State",
"PUR":"Purdue","RUTG":"Rutgers","SCAR":"South Carolina",
"STAN":"Stanford","SYR":"Syracuse","TAMU":"Texas A&M",
"TCU":"TCU","TENN":"Tennessee","TEX":"Texas","TTU":"Texas Tech",
"UCLA":"UCLA","UNC":"North Carolina","USC":"USC","UTAH":"Utah",
"VAN":"Vanderbilt","VILL":"Villanova","UVA":"Virginia",
"VT":"Virginia Tech","WASH":"Washington","WISC":"Wisconsin",
"WVU":"West Virginia","XAV":"Xavier"
}

games_raw["HOME_NAME"] = games_raw["home_team"].map(KAGGLE_MAP)
games_raw["AWAY_NAME"] = games_raw["away_team"].map(KAGGLE_MAP)
games_raw = games_raw.dropna(subset=["HOME_NAME","AWAY_NAME"])

team_master = pd.read_csv(TEAM_MASTER_FILE)
name_to_id = dict(zip(team_master["DISPLAY_NAME"], team_master["TEAM_ID"]))

games_raw["HOME_ID"] = games_raw["HOME_NAME"].map(name_to_id)
games_raw["AWAY_ID"] = games_raw["AWAY_NAME"].map(name_to_id)
games_raw = games_raw.dropna(subset=["HOME_ID","AWAY_ID"])

games = games_raw.merge(
    ratings.add_prefix("HOME_"),
    left_on="HOME_ID",
    right_on="HOME_TEAM_ID",
    how="inner"
)

games = games.merge(
    ratings.add_prefix("AWAY_"),
    left_on="AWAY_ID",
    right_on="AWAY_TEAM_ID",
    how="inner"
)

games = games.sort_values("date").reset_index(drop=True)

def harmonic_tempo(t1, t2):
    return 2 * (t1 * t2) / (t1 + t2)

def expected_ortg(off, opp_def):
    return off + (LEAGUE_AVG - opp_def)

games["POSSESSIONS"] = harmonic_tempo(
    games["HOME_ADJ_TEMPO"],
    games["AWAY_ADJ_TEMPO"]
)

games["HOME_ADJ_OR"] = expected_ortg(
    games["HOME_ADJ_OE"],
    games["AWAY_ADJ_DE"]
)

games["AWAY_ADJ_OR"] = expected_ortg(
    games["AWAY_ADJ_OE"],
    games["HOME_ADJ_DE"]
)

games["HOME_PROJ"] = games["POSSESSIONS"] * games["HOME_ADJ_OR"] / 100
games["AWAY_PROJ"] = games["POSSESSIONS"] * games["AWAY_ADJ_OR"] / 100

base_spread = games["HOME_PROJ"] - games["AWAY_PROJ"] + BASE_HOME_COURT
net_gap = games["HOME_NET_RTG"] - games["AWAY_NET_RTG"]

X_all = np.vstack([base_spread, net_gap]).T
y_all = games["home_score"] - games["away_score"]

preds = []
edges = []
results = []

for i in range(MIN_TRAIN, len(games)):
    X_train = X_all[:i]
    y_train = y_all[:i]
    X_test = X_all[i]

    beta = np.linalg.lstsq(X_train, y_train, rcond=None)[0]
    pred = beta[0] * X_test[0] + beta[1] * X_test[1]

    market = -games.loc[i, "line"]
    edge = pred - market

    preds.append(pred)
    edges.append(edge)

    if abs(edge) > EDGE_THRESHOLD:
        if edge > 0:
            result = 1 if y_all[i] > -games.loc[i, "line"] else -1
        else:
            result = 1 if y_all[i] < -games.loc[i, "line"] else -1
        results.append(result)

print("\n===== WALK-FORWARD TEST =====")
print("Correlation vs Actual:",
      round(np.corrcoef(preds, y_all[MIN_TRAIN:])[0,1],4))

if results:
    wins = results.count(1)
    losses = results.count(-1)
    win_pct = wins / (wins + losses)
    profit = wins * (STAKE * 100/110) - losses * STAKE
    roi = profit / ((wins + losses) * STAKE)

    print("\n===== WALK-FORWARD ATS =====")
    print("Total Bets:", wins + losses)
    print("Win %:", round(win_pct * 100,2))
    print("ROI %:", round(roi * 100,2))
else:
    print("No bets triggered.")
