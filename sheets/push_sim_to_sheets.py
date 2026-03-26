from __future__ import annotations

from datetime import datetime
from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SHEET_NAME = "CBB Sim"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SIM_DIR = DATA_DIR / "sim"
CREDS_PATH = BASE_DIR / "credentials.json"

TODAY = datetime.now().strftime("%Y-%m-%d")

# Sim threshold for edge display (per your lock)
SIM_THRESHOLD_PCT = 55.0


def _fmt_pct(x: float) -> str:
    return f"{round(float(x) * 100, 1):.1f}%"


def _fmt_spread(team: str, spread: float) -> str:
    return f"{team} {float(spread):+.1f}"


def _round_half(x: float) -> float:
    return round(float(x) * 2.0) / 2.0


def _cover_edge_points(cover_pct: float) -> float:
    p = float(cover_pct) * 100.0
    if p >= 61.0:
        return 2.0
    if p >= 59.0:
        return 1.5
    if p >= 57.0:
        return 1.0
    if p >= 55.0:
        return 0.5
    return 0.0


def _sim_edge_vs_threshold(cover_pct: float) -> float:
    return round((float(cover_pct) * 100.0) - SIM_THRESHOLD_PCT, 1)


def _model_bet(home: str, away: str, market_spread: float, model_spread: float) -> tuple[str, str]:
    # Returns (side_team, formatted_bet)
    if float(model_spread) < float(market_spread):
        return home, _fmt_spread(home, market_spread)
    return away, _fmt_spread(away, -float(market_spread))


def _sim_bet_from_pick(home: str, away: str, market_spread: float, cover_pick: str) -> tuple[str, str]:
    if cover_pick == home:
        return home, _fmt_spread(home, market_spread)
    return away, _fmt_spread(away, -float(market_spread))


def _combo_spread(model_spread: float, sim_side: str, home: str, cover_edge: float) -> float:
    # Model spread is from HOME perspective.
    # Move toward sim side by cover_edge points.
    if cover_edge <= 0:
        return float(model_spread)
    if sim_side == home:
        return float(model_spread) - float(cover_edge)
    return float(model_spread) + float(cover_edge)


def _get_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=scope)
    return gspread.authorize(creds)


def _push_dataframe(sheet, tab_name: str, df: pd.DataFrame):
    df = df.fillna("")
    try:
        ws = sheet.worksheet(tab_name)
    except Exception:
        ws = sheet.add_worksheet(title=tab_name, rows="4000", cols="40")

    rows = max(1, len(df) + 1)
    cols = max(1, len(df.columns))
    ws.resize(rows=rows, cols=cols)
    ws.clear()

    if df.empty:
        ws.update([["No rows"]], value_input_option="USER_ENTERED")
    else:
        ws.update([df.columns.tolist()] + df.values.tolist(), value_input_option="USER_ENTERED")


def _append_results(sheet, tab_name: str, new_df: pd.DataFrame):
    # Stack newest on top, preserve history.
    if new_df.empty:
        print(f"{tab_name}: no new rows")
        return

    try:
        ws = sheet.worksheet(tab_name)
        values = ws.get_all_values()
    except Exception:
        ws = sheet.add_worksheet(title=tab_name, rows="8000", cols="40")
        values = []

    if len(values) >= 2:
        headers = values[0]
        old_rows = values[1:]
        existing = pd.DataFrame(old_rows, columns=headers)
    else:
        existing = pd.DataFrame()

    # Preserve previously-entered manual W/L values when a row is repushed.
    # Keyed by Date + Home + Away.
    key_cols = [c for c in ["Date", "Home", "Away"] if c in new_df.columns]
    wl_cols = [c for c in new_df.columns if c.endswith("W/L")]
    if key_cols and wl_cols and not existing.empty and set(key_cols).issubset(existing.columns):
        existing_lookup = existing.set_index(key_cols)
        for idx, row in new_df.iterrows():
            key = tuple(str(row[c]) for c in key_cols)
            if key in existing_lookup.index:
                existing_row = existing_lookup.loc[key]
                # If duplicates exist in existing sheet, use first match.
                if isinstance(existing_row, pd.DataFrame):
                    existing_row = existing_row.iloc[0]
                for col in wl_cols:
                    if col in existing_lookup.columns and (pd.isna(row[col]) or str(row[col]).strip() == ""):
                        new_df.at[idx, col] = existing_row.get(col, "")

    combined = pd.concat([new_df, existing], ignore_index=True)
    dedupe_cols = [c for c in ["Date", "Home", "Away"] if c in combined.columns]
    if dedupe_cols:
        combined = combined.drop_duplicates(subset=dedupe_cols, keep="first")
    if "Date" in combined.columns:
        combined = combined.sort_values("Date", ascending=False)
    combined = combined.reset_index(drop=True)

    # Backfill historical Combo Edge Bet rows when new columns are introduced.
    if (
        tab_name == "Combo"
        and {"Home", "Away", "Market Spread", "Combo Edge", "Combo Edge Bet"}.issubset(combined.columns)
    ):
        ms = pd.to_numeric(combined["Market Spread"], errors="coerce")
        ce = pd.to_numeric(combined["Combo Edge"], errors="coerce")
        ceb = combined["Combo Edge Bet"].astype(str).str.strip()
        need_fill = ceb.isin(["", "nan", "None", "NaN"]) & ms.notna() & ce.notna()

        home_mask = need_fill & (ce <= -6.0)
        away_mask = need_fill & (ce >= 6.0)
        no_bet_mask = need_fill & ~(home_mask | away_mask)

        combined.loc[home_mask, "Combo Edge Bet"] = [
            _fmt_spread(h, m) for h, m in zip(combined.loc[home_mask, "Home"], ms.loc[home_mask])
        ]
        combined.loc[away_mask, "Combo Edge Bet"] = [
            _fmt_spread(a, -m) for a, m in zip(combined.loc[away_mask, "Away"], ms.loc[away_mask])
        ]
        combined.loc[no_bet_mask, "Combo Edge Bet"] = "No Bet"

    # Write all appended values as strings so Google Sheets keeps alignment consistent
    # between historical rows (read back as strings) and new rows.
    combined = combined.fillna("").astype(str)
    ws.clear()
    ws.update([combined.columns.tolist()] + combined.values.tolist(), value_input_option="USER_ENTERED")


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    spread = pd.read_csv(SIM_DIR / "spread_sim_results.csv")
    total = pd.read_csv(SIM_DIR / "total_sim_results.csv")
    engine = pd.read_csv(DATA_DIR / "engine.csv")
    return spread, total, engine


def _build_sim_games(spread_df: pd.DataFrame, total_df: pd.DataFrame) -> pd.DataFrame:
    total_keyed = total_df.copy()
    merged = spread_df.merge(total_keyed, on=["HOME", "AWAY"], how="left", suffixes=("", "_T"))

    rows = []
    for _, r in merged.iterrows():
        home = str(r["HOME"])
        away = str(r["AWAY"])
        market_spread = _round_half(float(r["MARKET_SPREAD"]))

        if float(r["R5_HOME_WIN_PCT"]) >= float(r["R5_AWAY_WIN_PCT"]):
            winner_pick = home
            win_pct = float(r["R5_HOME_WIN_PCT"])
        else:
            winner_pick = away
            win_pct = float(r["R5_AWAY_WIN_PCT"])

        if float(r["R2_HOME_COVER_PCT"]) >= float(r["R2_AWAY_COVER_PCT"]):
            cover_pick = home
            cover_pct = float(r["R2_HOME_COVER_PCT"])
            spread_pick = _fmt_spread(home, market_spread)
        else:
            cover_pick = away
            cover_pct = float(r["R2_AWAY_COVER_PCT"])
            spread_pick = _fmt_spread(away, -market_spread)

        total_pick = ""
        if pd.notna(r.get("TOTAL_PICK")) and pd.notna(r.get("MARKET_TOTAL")):
            total_pick = f"{str(r['TOTAL_PICK']).title()} {float(r['MARKET_TOTAL']):.1f}"

        rows.append(
            {
                "Date": TODAY,
                "Home": home,
                "Away": away,
                "Winner Pick": winner_pick,
                "Win %": _fmt_pct(win_pct),
                "Spread Pick": spread_pick,
                "Cover %": _fmt_pct(cover_pct),
                "Sim Edge": _sim_edge_vs_threshold(cover_pct),
                "Market Total": round(float(r["MARKET_TOTAL"]), 1) if pd.notna(r.get("MARKET_TOTAL")) else "",
                "Total Pick": total_pick,
                "Projected Total": round(float(r["PROJECTED_TOTAL"]), 1) if pd.notna(r.get("PROJECTED_TOTAL")) else "",
            }
        )
    return pd.DataFrame(rows)


def _build_sim_results(sim_games_df: pd.DataFrame) -> pd.DataFrame:
    out = sim_games_df[
        ["Date", "Home", "Away", "Winner Pick", "Win %", "Spread Pick", "Cover %", "Total Pick"]
    ].copy()
    out["Winnner W/L"] = ""
    out["Spread W/L"] = ""
    out["Total W/L"] = ""
    return out


def _build_combo(engine_df: pd.DataFrame, spread_df: pd.DataFrame) -> pd.DataFrame:
    eng = engine_df.copy()
    eng = eng.rename(
        columns={
            "Home": "HOME",
            "Away": "AWAY",
            "Spread": "MARKET_SPREAD",
            "Model Spread": "MODEL_SPREAD",
            "Spread Edge": "MODEL_EDGE",
        }
    )
    merged = eng.merge(
        spread_df[["HOME", "AWAY", "R2_HOME_COVER_PCT", "R2_AWAY_COVER_PCT", "COVER_PICK"]],
        on=["HOME", "AWAY"],
        how="left",
    )

    rows = []
    for _, r in merged.iterrows():
        home = str(r["HOME"])
        away = str(r["AWAY"])
        mkt = float(r["MARKET_SPREAD"])
        model_spread = float(r["MODEL_SPREAD"])
        model_edge = float(r["MODEL_EDGE"])

        model_side, model_bet = _model_bet(home, away, mkt, model_spread)

        if float(r["R2_HOME_COVER_PCT"]) >= float(r["R2_AWAY_COVER_PCT"]):
            cover_pct = float(r["R2_HOME_COVER_PCT"])
            sim_side, sim_bet = _sim_bet_from_pick(home, away, mkt, home)
        else:
            cover_pct = float(r["R2_AWAY_COVER_PCT"])
            sim_side, sim_bet = _sim_bet_from_pick(home, away, mkt, away)

        edge_boost = _cover_edge_points(cover_pct)
        combo_spread = _combo_spread(model_spread, sim_side, home, edge_boost)
        combo_edge = combo_spread - mkt

        combo_bet = sim_bet if model_side == sim_side else "No Bet"
        if combo_edge <= -6.0:
            combo_edge_bet = _fmt_spread(home, mkt)
        elif combo_edge >= 6.0:
            combo_edge_bet = _fmt_spread(away, -mkt)
        else:
            combo_edge_bet = "No Bet"

        rows.append(
            {
                "Date": TODAY,
                "Home": home,
                "Away": away,
                "Market Spread": round(mkt, 1),
                "Model Spread": round(model_spread, 1),
                "Model Edge": round(model_edge, 1),
                "Model Bet": model_bet,
                "Cover %": _fmt_pct(cover_pct),
                "Cover Edge": edge_boost,
                "Sim Bet": sim_bet,
                "Combo Edge": round(combo_edge, 1),
                "Combo Spread": round(combo_spread, 1),
                "Combo Bet": combo_bet,
                "Combo Edge Bet": combo_edge_bet,
            }
        )

    out = pd.DataFrame(rows)
    out["Combo W/L"] = ""
    out["Combo Edge W/L"] = ""
    return out


def push_sim_tabs():
    spread_df, total_df, engine_df = _load_inputs()
    sim_games = _build_sim_games(spread_df, total_df)
    sim_results = _build_sim_results(sim_games)
    combo = _build_combo(engine_df, spread_df)

    client = _get_client()
    sheet = client.open(SHEET_NAME)

    # Full daily slate overwrite
    _push_dataframe(sheet, "Sim Games", sim_games)

    # Rolling history tabs
    _append_results(sheet, "Sim Results", sim_results)
    _append_results(sheet, "Combo", combo)

    print("Sim tabs pushed successfully.")


if __name__ == "__main__":
    push_sim_tabs()
