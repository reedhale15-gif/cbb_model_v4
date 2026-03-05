import pandas as pd
from pathlib import Path
import numpy as np

# =========================
# PATHS
# =========================

BASE_DIR = Path.home() / "Documents" / "CBB_Model"

TEAM_STATS_FILE = BASE_DIR / "engine_inputs" / "engine_team_stats_full_2016.csv"
GAMES_FILE = BASE_DIR / "ingestion" / "ncaab_game_scores_1g.csv"
TEAM_MASTER_FILE = BASE_DIR / "ingestion" / "team_master.csv"

LEAGUE_AVG = 100
HOME_COURT = 1.5
EDGE_THRESHOLD = 2.0
STAKE = 100
SPREAD_SCALE = 1.0   # REMOVE artificial scaling completely

# =========================
# LOAD DATA
# =========================

team_stats = pd.read_csv(TEAM_STATS_FILE)

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

# =========================
# KAGGLE MAP
# =========================

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
    team_stats.add_prefix("HOME_"),
    left_on="HOME_ID",
    right_on="HOME_TEAM_ID",
    how="inner"
)

games = games.merge(
    team_stats.add_prefix("AWAY_"),
    left_on="AWAY_ID",
    right_on="AWAY_TEAM_ID",
    how="inner"
)

# =========================
# PROJECTION (CLEAN)
# =========================

games["EXPECTED_POSSESSIONS"] = (
    2 * (games["HOME_ADJ_TEMPO"] * games["AWAY_ADJ_TEMPO"]) /
    (games["HOME_ADJ_TEMPO"] + games["AWAY_ADJ_TEMPO"])
)

games["HOME_PROJ_OFF_RTG"] = (
    games["HOME_ADJ_OE"] + (LEAGUE_AVG - games["AWAY_ADJ_DE"])
)

games["AWAY_PROJ_OFF_RTG"] = (
    games["AWAY_ADJ_OE"] + (LEAGUE_AVG - games["HOME_ADJ_DE"])
)

games["HOME_PROJ_POINTS"] = (
    games["HOME_PROJ_OFF_RTG"] * (games["EXPECTED_POSSESSIONS"] / 100)
) + HOME_COURT

games["AWAY_PROJ_POINTS"] = (
    games["AWAY_PROJ_OFF_RTG"] * (games["EXPECTED_POSSESSIONS"] / 100)
)

# Home margin orientation (same as actual margin)
games["MODEL_SPREAD"] = games["HOME_PROJ_POINTS"] - games["AWAY_PROJ_POINTS"]

# Market converted to same orientation
games["MARKET_SPREAD"] = -games["line"]

# Remove bias ONLY (no scale distortion)
bias = games["MODEL_SPREAD"].mean() - games["MARKET_SPREAD"].mean()
games["MODEL_SPREAD"] -= bias

games["EDGE"] = games["MODEL_SPREAD"] - games["MARKET_SPREAD"]

actual_margin = games["home_score"] - games["away_score"]

print("Raw Corr vs Actual:",
      round(np.corrcoef(games["MODEL_SPREAD"], actual_margin)[0,1],4))

print("Corr vs Market:",
      round(np.corrcoef(games["MODEL_SPREAD"], games["MARKET_SPREAD"])[0,1],4))

print("Corr vs Actual:",
      round(np.corrcoef(games["MODEL_SPREAD"], actual_margin)[0,1],4))

# =========================
# ATS
# =========================

games["HOME_MARGIN"] = actual_margin
games["BET_HOME"] = games["EDGE"] > 0

def grade(row):
    if abs(row["EDGE"]) < EDGE_THRESHOLD:
        return None
    if row["BET_HOME"]:
        return 1 if row["HOME_MARGIN"] > row["line"] else -1
    else:
        return 1 if row["HOME_MARGIN"] < row["line"] else -1

games["RESULT"] = games.apply(grade, axis=1)
games = games.dropna(subset=["RESULT"])

wins = (games["RESULT"] == 1).sum()
losses = (games["RESULT"] == -1).sum()

win_pct = wins / (wins + losses)
profit = wins * (STAKE * 100/110) - losses * STAKE
roi = profit / ((wins + losses) * STAKE)

print("\n===== FULL 2015 BACKTEST =====")
print("Total Bets:", wins + losses)
print("Win %:", round(win_pct * 100,2))
print("ROI %:", round(roi * 100,2))
