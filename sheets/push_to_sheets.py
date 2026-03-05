import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

SHEET_NAME = "CBB Model v4"

EDGE_THRESHOLD_SPREAD = 6.0
EDGE_THRESHOLD_TOTAL = 6.0

TODAY = datetime.now().strftime("%Y-%m-%d")


# ============================================================
# GOOGLE SHEETS CONNECTION
# ============================================================

def get_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=scope
    )

    return gspread.authorize(creds)


# ============================================================
# SIMPLE OVERWRITE PUSH
# ============================================================

def push_dataframe(sheet, tab_name, df):

    df = df.fillna("")

    try:
        worksheet = sheet.worksheet(tab_name)
    except:
        worksheet = sheet.add_worksheet(title=tab_name, rows="3000", cols="30")

    worksheet.clear()

    if not df.empty:
        worksheet.update([df.columns.tolist()] + df.values.tolist())


# ============================================================
# BUILD GAMES TAB
# ============================================================

def build_games_df():
    df = pd.read_csv("data/engine.csv")

    # Remove games without market spreads
    df = df[df["Spread"].notna()]

    return df[["Home", "Away", "Spread", "Total"]]


# ============================================================
# BUILD ENGINE TAB
# ============================================================

def build_engine_df():
    df = pd.read_csv("data/engine.csv")

    # Remove games without market spreads
    df = df[df["Spread"].notna()]

    return df


# ============================================================
# CONFIDENCE FUNCTIONS
# ============================================================

def spread_confidence(edge):
    edge = abs(edge)
    if edge >= 12: return "A+"
    if edge >= 10: return "A"
    if edge >= 8: return "A-"
    if edge >= 6: return "B"
    if edge >= 5: return "C+"
    if edge >= 4: return "C"
    return ""


def total_confidence(edge):
    edge = abs(edge)
    if edge >= 20: return "A+"
    if edge >= 15: return "A"
    if edge >= 12: return "A-"
    if edge >= 10: return "B+"
    if edge >= 8: return "B"
    if edge >= 6: return "B-"
    if edge >= 4: return "C+"
    return ""


# ============================================================
# BUILD SPREAD BETS TAB
# ============================================================

def build_spread_bets_df():

    df = pd.read_csv("data/engine.csv")
    rows = []

    for _, row in df.iterrows():

        edge = row["Spread Edge"]

        if pd.isna(edge) or abs(edge) < EDGE_THRESHOLD_SPREAD:
            continue

        home = row["Home"]
        away = row["Away"]
        market_spread = float(row["Spread"])
        model_spread = float(row["Model Spread"])

        if model_spread < market_spread:
            bet = f"{home} {market_spread:+.1f}"
        else:
            bet = f"{away} {-market_spread:+.1f}"

        rows.append({
            "Home": home,
            "Away": away,
            "Market Spread": f"{market_spread:+.1f}",
            "Model Spread": f"{model_spread:+.1f}",
            "Spread Edge": f"{edge:+.2f}",
            "Spread Bet": bet,
            "Spread Confidence": spread_confidence(edge)
        })

    return pd.DataFrame(rows)


# ============================================================
# BUILD TOTAL BETS TAB
# ============================================================

def build_total_bets_df():

    df = pd.read_csv("data/engine.csv")
    rows = []

    for _, row in df.iterrows():

        edge = row["Total Edge"]

        if pd.isna(edge) or abs(edge) < EDGE_THRESHOLD_TOTAL:
            continue

        home = row["Home"]
        away = row["Away"]
        market_total = float(row["Total"])
        model_total = float(row["Model Total"])

        if edge > 0:
            bet = f"Over {market_total:.1f}"
        else:
            bet = f"Under {market_total:.1f}"

        rows.append({
            "Home": home,
            "Away": away,
            "Market Total": f"{market_total:.1f}",
            "Model Total": f"{model_total:.1f}",
            "Total Edge": f"{edge:+.2f}",
            "Total Bet": bet,
            "Total Confidence": total_confidence(edge)
        })

    return pd.DataFrame(rows)


# ============================================================
# APPEND RESULTS (NEW ROWS ON TOP)
# ============================================================

def append_results(sheet, tab_name, new_df):

    try:
        worksheet = sheet.worksheet(tab_name)
        existing_data = worksheet.get_all_records()
        existing_df = pd.DataFrame(existing_data)
    except:
        worksheet = sheet.add_worksheet(title=tab_name, rows="5000", cols="30")
        existing_df = pd.DataFrame()

    if existing_df.empty or "Date" not in existing_df.columns:
        combined_df = new_df.copy()
    else:
        key_cols = ["Date", "Home", "Away"]

        existing_keys = existing_df[key_cols]

        merged = new_df.merge(
            existing_keys,
            on=key_cols,
            how="left",
            indicator=True
        )

        new_rows = merged[merged["_merge"] == "left_only"]
        new_rows = new_rows[new_df.columns]

        combined_df = pd.concat([new_rows, existing_df], ignore_index=True)

    combined_df = combined_df.sort_values("Date", ascending=False)
    combined_df = combined_df.reset_index(drop=True)

    worksheet.clear()
    worksheet.update([combined_df.columns.tolist()] + combined_df.values.tolist())


# ============================================================
# BUILD RESULTS DATA
# ============================================================

def build_spread_results_df():
    df = build_spread_bets_df()
    if df.empty:
        return df

    df.insert(0, "Date", TODAY)
    df["Spread W/L"] = ""
    return df


def build_total_results_df():
    df = build_total_bets_df()
    if df.empty:
        return df

    df.insert(0, "Date", TODAY)
    df["Total W/L"] = ""
    return df


# ============================================================
# MAIN
# ============================================================

def push_all():

    client = get_client()
    sheet = client.open(SHEET_NAME)

    # Overwrite tabs
    push_dataframe(sheet, "Games", build_games_df())
    push_dataframe(sheet, "Engine", build_engine_df())
    push_dataframe(sheet, "Spread Bets", build_spread_bets_df())
    push_dataframe(sheet, "Total Bets", build_total_bets_df())

    # Append results
    append_results(sheet, "Spread Results", build_spread_results_df())
    append_results(sheet, "Total Results", build_total_results_df())

    print("All tabs updated successfully.")


if __name__ == "__main__":
    push_all()
