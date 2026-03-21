import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from model_config import TOTAL_EDGE_MAX, TOTAL_EDGE_MIN, spread_bet_qualifies, spread_edge_band
from tournament import apply_seeds_to_dataframe

SHEET_NAME = "CBB Model v4"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CREDS_PATH = BASE_DIR / "credentials.json"

EDGE_THRESHOLD_SPREAD, MAX_SPREAD_EDGE = spread_edge_band()
EDGE_THRESHOLD_TOTAL = TOTAL_EDGE_MIN

TODAY = datetime.now().strftime("%Y-%m-%d")


def filter_today_games(df):
    df["Game Time"] = pd.to_datetime(df["Game Time"], utc=True, errors="coerce")
    df["Game Time"] = df["Game Time"].dt.tz_convert("US/Central")

    today = pd.Timestamp.now(tz="US/Central").date()
    df = df[df["Game Time"].dt.date == today].copy()

    df["Game Time"] = df["Game Time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def get_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=scope)
    return gspread.authorize(creds)


def push_dataframe(sheet, tab_name, df):
    df = df.fillna("")

    try:
        worksheet = sheet.worksheet(tab_name)
    except:
        worksheet = sheet.add_worksheet(title=tab_name, rows="3000", cols="30")

    rows = max(1, len(df) + 1)
    cols = max(1, len(df.columns))

    worksheet.resize(rows=rows, cols=cols)
    worksheet.clear()

    if df.empty:
        worksheet.update([["No bets today"]])
    else:
        worksheet.update([df.columns.tolist()] + df.values.tolist())


def build_engine_df():
    df = pd.read_csv(DATA_DIR / "engine.csv")
    df = filter_today_games(df)
    df = df[df["Spread"].notna()]
    return df


def build_games_df():
    df = build_engine_df()
    return apply_seeds_to_dataframe(df[["Home", "Away", "Spread", "Total"]])


def spread_confidence(edge):
    edge = abs(edge)
    if edge >= 12: return "A+"
    if edge >= 10: return "A-"
    if edge >= 8: return "B+"
    if edge >= 7: return "B-"
    if edge >= 6: return "C"
    return ""


def total_confidence(edge):
    edge = float(edge)
    edge_abs = abs(edge)

    if edge > 0:
        if edge_abs < 10:
            return "A"
        if edge_abs <= 12:
            return "B"
        return ""

    if edge_abs >= 10:
        return "A"
    if edge_abs >= 6:
        if edge_abs < 8:
            return "B"
        return "C"
    return ""


def build_spread_bets_df():
    df = build_engine_df()
    rows = []

    for _, row in df.iterrows():
        edge = row["Spread Edge"]

        if pd.isna(edge):
            continue

        if not spread_bet_qualifies(float(row["Spread"]), float(row["Model Spread"]), edge):
            continue

        home = row["Home"]
        away = row["Away"]
        model_spread = float(row["Model Spread"])
        market_spread = float(row["Spread"])

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

    return apply_seeds_to_dataframe(pd.DataFrame(rows), bet_columns=("Spread Bet",))


def build_total_bets_df():
    df = build_engine_df()
    rows = []

    for _, row in df.iterrows():
        edge = row["Total Edge"]

        if pd.isna(edge) or abs(edge) < EDGE_THRESHOLD_TOTAL or abs(edge) > TOTAL_EDGE_MAX:
            continue

        home = row["Home"]
        away = row["Away"]

        market_total = float(row["Total"])
        model_total = float(row["Model Total"])

        bet = f"Over {market_total:.1f}" if edge > 0 else f"Under {market_total:.1f}"

        rows.append({
            "Home": home,
            "Away": away,
            "Market Total": f"{market_total:.1f}",
            "Model Total": f"{model_total:.1f}",
            "Total Edge": f"{edge:+.2f}",
            "Total Bet": bet,
            "Total Confidence": total_confidence(edge)
        })

    return apply_seeds_to_dataframe(pd.DataFrame(rows), bet_columns=("Total Bet",))


# 🔒 SAFE RESULTS HANDLER (NO DELETE EVER)
def append_results(sheet, tab_name, new_df):

    # If no new bets → DO NOTHING (protects history)
    if new_df.empty:
        print(f"{tab_name}: No new bets — preserving existing data")
        return

    try:
        worksheet = sheet.worksheet(tab_name)
        values = worksheet.get_all_values()
    except:
        worksheet = sheet.add_worksheet(title=tab_name, rows="5000", cols="30")
        values = []

    # Convert existing sheet to DataFrame
    if len(values) >= 2:
        headers = values[0]
        rows = values[1:]
        existing_df = pd.DataFrame(rows, columns=headers)
    else:
        existing_df = pd.DataFrame()

    # Add date to new data
    new_df = new_df.copy()
    if "Date" not in new_df.columns:
        new_df.insert(0, "Date", TODAY)

    # Combine WITHOUT deleting anything
    combined_df = pd.concat([new_df, existing_df], ignore_index=True)

    # Optional: remove duplicates safely
    if all(col in combined_df.columns for col in ["Date", "Home", "Away"]):
        combined_df = combined_df.drop_duplicates(subset=["Date", "Home", "Away"], keep="first")

    # Sort safely
    if "Date" in combined_df.columns:
        combined_df = combined_df.sort_values("Date", ascending=False)

    combined_df = combined_df.reset_index(drop=True)

    # 🔒 BACKUP locally EVERY time
    combined_df.to_csv(DATA_DIR / f"{tab_name.replace(' ', '_').lower()}_backup.csv", index=False)

    # 🔒 NEVER CLEAR — just overwrite content safely
    worksheet.update([combined_df.columns.tolist()] + combined_df.values.tolist())


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


def push_all():
    client = get_client()
    sheet = client.open(SHEET_NAME)

    push_dataframe(sheet, "Games", build_games_df())
    push_dataframe(sheet, "Engine", build_engine_df())
    push_dataframe(sheet, "Spread Bets", build_spread_bets_df())
    push_dataframe(sheet, "Total Bets", build_total_bets_df())

    append_results(sheet, "Spread Results", build_spread_results_df())
    append_results(sheet, "Total Results", build_total_results_df())

    print("All tabs updated successfully.")


if __name__ == "__main__":
    push_all()
