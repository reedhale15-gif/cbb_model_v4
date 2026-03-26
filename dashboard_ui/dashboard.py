import streamlit as st
import pandas as pd
import json
import os
import sys
import gspread
from google.oauth2.service_account import Credentials
from uuid import uuid4

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_config import spread_bet_is_favorite, spread_bet_qualifies, spread_edge_band, total_bet_qualifies
from tournament import apply_seeds_to_dataframe
from dashboard_ui.lock_storage import build_locks_rows, make_lock_uid, parse_locks_values

EDGE_THRESHOLD_SPREAD, MAX_SPREAD_EDGE = spread_edge_band()

st.set_page_config(page_title="The LineLab", layout="wide")

engine_path = "data/engine.csv"

if "last_engine_update" not in st.session_state:
    st.session_state.last_engine_update = os.path.getmtime(engine_path)

current_update = os.path.getmtime(engine_path)

if current_update != st.session_state.last_engine_update:
    st.session_state.last_engine_update = current_update
    st.rerun()

st.markdown(
    """
<div style="
text-align:center;
margin: 6px 0 22px 0;
font-family: Inter, Arial, sans-serif;
letter-spacing: 0.04em;
">
  <div style="
    font-size: 2.25rem;
    font-weight: 800;
    color: #3b82f6;
    line-height: 1.05;
    text-shadow: 0 0 18px rgba(59, 130, 246, 0.18);
  ">The LineLab</div>
  <div style="
    margin-top: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.18em;
  ">College Basketball Model Dashboard</div>
</div>
""",
    unsafe_allow_html=True
)

SHEET_NAME = "CBB Model v4"
LOCKS_TAB_NAME = "App Locks"

# =========================
# ADMIN MODE
# =========================

query = st.query_params
admin_mode = False

if "admin" in query and query["admin"] == "1":
    admin_mode = True

# =========================
# LOAD DATA
# =========================

engine = pd.read_csv("data/engine.csv")
engine = engine[engine["Spread"].notna()].copy()

engine["Game Time Sort"] = pd.to_datetime(engine["Game Time"], errors="coerce")
engine["Game Time"] = (
    engine["Game Time Sort"]
    .dt.tz_convert("US/Central")
    .dt.strftime("%-I:%M %p")
)

engine = apply_seeds_to_dataframe(engine)
engine["Game"] = engine["Away"] + " @ " + engine["Home"]
engine = engine.sort_values("Game Time Sort").reset_index(drop=True)

# =========================
# LOAD PERFORMANCE DATA
# =========================

def get_performance_data():

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=scope
    )

    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME)

    spread_tab = sheet.worksheet("Spread Performance")
    total_tab = sheet.worksheet("Total Performance")
    spread_values = spread_tab.batch_get(["B5:B6"])
    total_values = total_tab.batch_get(["B5:B6", "E5:E6", "H5:H6"])

    def get_range_value(ranges, range_idx, row_idx):
        values = ranges[range_idx]
        if row_idx >= len(values) or not values[row_idx]:
            return ""
        return values[row_idx][0]

    spread_data = {
        "bets": get_range_value(spread_values, 0, 0),
        "winpct": get_range_value(spread_values, 0, 1)
    }

    total_data = {
        "overall_bets": get_range_value(total_values, 0, 0),
        "overall_pct": get_range_value(total_values, 0, 1),
        "over_bets": get_range_value(total_values, 1, 0),
        "over_pct": get_range_value(total_values, 1, 1),
        "under_bets": get_range_value(total_values, 2, 0),
        "under_pct": get_range_value(total_values, 2, 1)
    }

    return spread_data, total_data


def get_sheet():

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=scope
    )

    client = gspread.authorize(creds)
    return client.open(SHEET_NAME)


def load_locks():

    try:
        sheet = get_sheet()
        worksheet = sheet.worksheet(LOCKS_TAB_NAME)
        values = worksheet.get_all_values()

        return parse_locks_values(values)
    except:
        return []


def save_locks(locks):

    sheet = get_sheet()

    try:
        worksheet = sheet.worksheet(LOCKS_TAB_NAME)
    except:
        worksheet = sheet.add_worksheet(title=LOCKS_TAB_NAME, rows="200", cols="1")

    rows = build_locks_rows(locks)

    worksheet.clear()
    worksheet.update(rows)


spread_perf, total_perf = get_performance_data()

# =========================
# CONFIDENCE FUNCTIONS
# =========================

def spread_confidence(market_spread, model_spread, edge):
    edge = abs(edge)

    if spread_bet_is_favorite(market_spread, model_spread):
        if edge >= 8:
            return "B"
        if edge >= 6:
            return "A"
        return ""

    if edge >= 7:
        return "B"
    if edge >= 6:
        return "A"
    return ""


def total_confidence(edge):
    edge = float(edge)
    edge_abs = abs(edge)

    if edge > 0:
        if edge_abs <= 8:
            return "A"
        if edge_abs <= 12:
            return "B"
        return ""

    if edge_abs >= 10 and edge_abs <= 12:
        return "A"
    if edge_abs >= 6 and edge_abs < 10:
        return "B"
    return ""


def confidence_color(conf):
    colors = {
        "A+": "#16a34a",
        "A": "#22c55e",
        "A-": "#4ade80",
        "B+": "#eab308",
        "B": "#facc15",
        "B-": "#f59e0b",
        "C": "#f97316"
    }
    return colors.get(conf, "#9ca3af")


def confidence_rank(conf):
    order = {
        "A+": 5,
        "A": 4,
        "A-": 3,
        "B+": 2,
        "B": 1,
        "B-": 0,
        "C": -1
    }
    return order.get(conf, -2)

# =========================
# BUILD BET DATA
# =========================

spread = engine.copy()
spread["Confidence"] = spread.apply(
    lambda r: spread_confidence(r["Spread"], r["Model Spread"], r["Spread Edge"]),
    axis=1
)

spread["Bet"] = spread.apply(
    lambda r: f"{r['Home']} {r['Spread']:+.1f}"
    if r["Model Spread"] < r["Spread"]
    else f"{r['Away']} {-r['Spread']:+.1f}",
    axis=1
)

# SPREAD FILTER UPDATED
spread_bets = spread[
    spread.apply(
        lambda r: spread_bet_qualifies(r["Spread"], r["Model Spread"], r["Spread Edge"]),
        axis=1
    )
].copy()
spread_bets = spread_bets.sort_values("Spread Edge", ascending=False)
spread_bets = apply_seeds_to_dataframe(spread_bets)


totals = engine.copy()
totals["Confidence"] = totals["Total Edge"].apply(total_confidence)

totals["Bet"] = totals.apply(
    lambda r: f"Over {r['Total']}"
    if r["Total Edge"] > 0
    else f"Under {r['Total']}",
    axis=1
)

# TOTAL FILTER UPDATED
total_bets = totals[
    totals["Total Edge"].apply(total_bet_qualifies)
].copy()
total_bets = total_bets.sort_values(
    by="Total Edge",
    key=lambda s: s.abs(),
    ascending=False
)
total_bets = apply_seeds_to_dataframe(total_bets)

# =========================
# BUILD PICK OPTIONS
# =========================

spread_options = (spread["Game"] + " — " + spread["Bet"]).tolist()
total_options = (totals["Game"] + " — " + totals["Bet"]).tolist()

pick_options = spread_options + total_options
lock_card_lookup = {}

for _, r in spread.iterrows():
    option = f"{r['Game']} — {r['Bet']}"
    confidence = r["Confidence"] if pd.notna(r["Confidence"]) and r["Confidence"] else "No Grade"
    lock_card_lookup[option] = {
        "uid": make_lock_uid({
            "source": "auto",
            "option": option,
            "time": r["Game Time"],
            "game": r["Game"],
            "bet_type": "Spread",
            "bet": r["Bet"],
            "edge": r["Spread Edge"],
            "confidence": confidence,
            "market_line": f"{float(r['Spread']):+.1f}",
        }),
        "source": "auto",
        "option": option,
        "time": r["Game Time"],
        "game": r["Game"],
        "bet_type": "Spread",
        "edge": r["Spread Edge"],
        "bet": r["Bet"],
        "confidence": confidence,
        "market_line": f"{float(r['Spread']):+.1f}",
    }

for _, r in totals.iterrows():
    option = f"{r['Game']} — {r['Bet']}"
    confidence = r["Confidence"] if pd.notna(r["Confidence"]) and r["Confidence"] else "No Grade"
    lock_card_lookup[option] = {
        "uid": make_lock_uid({
            "source": "auto",
            "option": option,
            "time": r["Game Time"],
            "game": r["Game"],
            "bet_type": "Total",
            "bet": r["Bet"],
            "edge": r["Total Edge"],
            "confidence": confidence,
            "market_line": f"{float(r['Total']):.1f}",
        }),
        "source": "auto",
        "option": option,
        "time": r["Game Time"],
        "game": r["Game"],
        "bet_type": "Total",
        "edge": r["Total Edge"],
        "bet": r["Bet"],
        "confidence": confidence,
        "market_line": f"{float(r['Total']):.1f}",
    }

# =========================
# REED'S LOCKS
# =========================

saved_locks = load_locks()
manual_locks = [lock for lock in saved_locks if lock.get("source") == "manual"]
saved_auto_options = [
    lock.get("option")
    for lock in saved_locks
    if lock.get("source") == "auto" and lock.get("option") in pick_options
]
locks = manual_locks + [lock_card_lookup[option] for option in saved_auto_options]

if admin_mode:

    st.sidebar.header("🔒 Reed's Locks of the Day")

    selected_locks = st.sidebar.multiselect(
        "Select your picks",
        pick_options,
        default=saved_auto_options
    )

    with st.sidebar.expander("Add Custom Lock", expanded=False):
        with st.form("custom_lock_form", clear_on_submit=True):
            custom_time = st.text_input("Time", placeholder="7:30 PM")
            custom_away = st.text_input("Away Team", placeholder="Duke")
            custom_home = st.text_input("Home Team", placeholder="North Carolina")
            custom_bet_type = st.selectbox("Bet Type", ["Spread", "Total", "ML"])
            custom_market_line = st.text_input("Market Line", placeholder="-7.5 / +7.5 / 142.5 / -150")
            custom_pick = st.text_input("Pick (optional)", placeholder="If used, shown exactly as entered")
            custom_edge = st.number_input("Edge", value=0.0, step=0.1, format="%.1f")
            custom_confidence = st.selectbox("Confidence Grade", ["", "A", "B", "C"])
            custom_submit = st.form_submit_button("Add Custom Lock")

            if custom_submit:
                entered_market_line = str(custom_market_line).strip()
                entered_pick = str(custom_pick).strip()
                custom_bet_display = entered_pick if entered_pick else entered_market_line

                if not custom_bet_display:
                    st.warning("Enter a Market Line (or Pick) before adding a custom lock.")
                    st.stop()

                custom_game = " @ ".join([x for x in [custom_away, custom_home] if x])
                custom_lock = {
                    "source": "manual",
                    "uid": uuid4().hex[:12],
                    "option": f"{custom_game} — {custom_bet_display}",
                    "time": custom_time,
                    "game": custom_game,
                    "bet_type": custom_bet_type,
                    "bet": custom_bet_display,
                    "edge": custom_edge,
                    "confidence": custom_confidence,
                    "market_line": entered_market_line,
                }

                combined = manual_locks + [lock_card_lookup[option] for option in selected_locks] + [custom_lock]
                save_locks(combined)
                st.rerun()

    selected_auto_locks = [lock_card_lookup[option] for option in selected_locks]

    if selected_locks != saved_auto_options:
        save_locks(manual_locks + selected_auto_locks)

    locks = manual_locks + selected_auto_locks


# =========================
# CARD RENDERER
# =========================

def render_card(time, game, lines, conf=None, glow=None, compact=False):

    border = "1px solid rgba(150,150,150,0.25)"
    shadow = "0 4px 12px rgba(0,0,0,0.08)"
    background = "transparent"
    time_size = "13px"
    game_size = "20px"
    pad = "18px"
    game_margin = "10px"
    badge_size = "12px"

    if glow == "green":
        border = "2px solid #16a34a"
        shadow = "0 0 15px rgba(34,197,94,0.8)"
        background = "rgba(34,197,94,0.08)"

    if glow == "red":
        border = "2px solid #ef4444"
        shadow = "0 0 15px rgba(239,68,68,0.6)"
        background = "rgba(239,68,68,0.08)"

    if compact:
        time_size = "11px"
        game_size = "16px"
        pad = "13px"
        game_margin = "7px"
        badge_size = "11px"

    conf_badge = ""

    if conf:
        conf_badge = f"""
<span style="
background:{confidence_color(conf)};
color:white;
padding:4px 10px;
border-radius:8px;
font-size:{badge_size};
font-weight:600;
margin-top:8px;
display:inline-block;
">
{conf}
</span>
"""

    st.markdown(
        f"""
<div style="
border:{border};
border-radius:14px;
padding:{pad};
margin-bottom:12px;
box-shadow:{shadow};
background:{background};
">

<div style="font-size:{time_size};color:#6b7280;margin-bottom:6px;">
{time}
</div>

<div style="font-size:{game_size};font-weight:600;margin-bottom:{game_margin};">
{game}
</div>

{lines}

{conf_badge}

</div>
""",
        unsafe_allow_html=True
    )


# =========================
# TABS
# =========================

tabs = ["Home"]

if locks:
    tabs.append("🔒 Reed's Locks")

tabs += ["Games", "Spread Bets", "Total Bets", "Engine", "🔥 Performance"]

tab_objects = st.tabs(tabs)

# =========================
# HOME
# =========================

with tab_objects[0]:

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🔥 Top Spread Bets")

        top_spreads = (
            spread_bets.assign(conf_rank=spread_bets["Confidence"].apply(confidence_rank))
            .sort_values(
                by=["conf_rank", "Spread Edge"],
                ascending=[False, True],
                key=lambda s: s.abs() if s.name == "Spread Edge" else s
            )
            .head(3)
        )

        for _, r in top_spreads.iterrows():

            lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Spread Edge']:+.2f}
"""

            render_card(r["Game Time"], r["Game"], lines, r["Confidence"], glow="green")

    with col2:

        st.subheader("🔥 Top Total Bets")

        top_totals = (
            total_bets.assign(conf_rank=total_bets["Confidence"].apply(confidence_rank))
            .sort_values(
                by=["conf_rank", "Total Edge"],
                ascending=[False, True],
                key=lambda s: s.abs() if s.name == "Total Edge" else s
            )
            .head(3)
        )

        for _, r in top_totals.iterrows():

            lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Total Edge']:+.2f}
"""

            render_card(r["Game Time"], r["Game"], lines, r["Confidence"], glow="green")


# =========================
# LOCKS TAB
# =========================

if locks:

    with tab_objects[1]:

        st.header("🔒 Reed's Locks")

        def render_lock_card(lock_data):
            line_value = str(lock_data.get("market_line", "")).strip() or str(lock_data.get("bet", "")).strip()
            bet_value = str(lock_data.get("bet", "")).strip() or line_value
            lines = f"""
<b>{lock_data['bet_type']}: {line_value}</b><br>
<b>Edge: {float(lock_data['edge']):+.2f}</b><br>
<b>Bet: {bet_value}</b><br>
<b>Confidence Grade: {lock_data['confidence']}</b>
"""

            render_card(
                f"<b>{lock_data['time']}</b>",
                lock_data["game"],
                lines,
                lock_data["confidence"],
                glow="red"
            )

            if admin_mode and lock_data.get("source") == "manual":
                if st.button("Remove", key=f"remove_{lock_data.get('uid', make_lock_uid(lock_data))}"):
                    remaining = [
                        lock for lock in saved_locks
                        if lock.get("uid") != lock_data.get("uid")
                    ]
                    save_locks(remaining)
                    st.rerun()

        for i in range(0, len(locks), 2):
            left, right = st.columns(2)

            with left:
                render_lock_card(locks[i])

            if i + 1 < len(locks):
                with right:
                    render_lock_card(locks[i + 1])


# =========================
# GAMES TAB
# =========================

with tab_objects[1 if not locks else 2]:

    st.header("Games")

    st.markdown(
        """
<style>
.games-shell {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.games-head,
.game-strip {
    display: grid;
    grid-template-columns: 84px 12px minmax(180px, 1fr) 12px 72px 72px;
    align-items: center;
    gap: 0;
}
.games-head {
    padding: 0 12px 4px 12px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #64748b;
}
.game-strip {
    min-height: 38px;
    padding: 10px 12px;
    border: 1px solid rgba(148,163,184,0.24);
    border-radius: 14px;
    background: #ffffff;
    font-size: 12px;
    box-shadow: 0 6px 16px rgba(15,23,42,0.05);
    color: #111111;
}
.games-list .game-strip:nth-child(even) {
    background: #f7f7f7;
}
.game-strip:hover {
    filter: brightness(1.03);
}
.game-time {
    color: #6b7280;
    font-weight: 500;
    white-space: nowrap;
}
.game-matchup {
    font-weight: 700;
    letter-spacing: 0.02em;
    white-space: nowrap;
}
.game-num {
    text-align: center;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
@media (prefers-color-scheme: dark) {
    .games-head {
        color: #94a3b8;
    }
    .game-strip {
        border-color: #334155;
        color: #e5e7eb;
        background: #0f172a;
        box-shadow: 0 8px 20px rgba(15,23,42,0.18);
    }
    .game-time {
        color: #94a3b8;
    }
    .games-list .game-strip:nth-child(even) {
        background: #1e293b;
    }
}
</style>
""",
        unsafe_allow_html=True
    )

    rows_html = []

    rows_html.append(
        """
<div class="games-head">
    <div>Time</div>
    <div></div>
    <div>Game</div>
    <div></div>
    <div>Spread</div>
    <div>Total</div>
</div>
"""
    )

    for _, r in engine.iterrows():
        rows_html.append(
            f"""
<div class="game-strip">
    <div class="game-time">{r['Game Time']}</div>
    <div></div>
    <div class="game-matchup">{r['Game']}</div>
    <div></div>
    <div class="game-num">{r['Spread']:+.1f}</div>
    <div class="game-num">{r['Total']:.1f}</div>
</div>
"""
        )

    st.markdown(
        f"""
<div class="games-list">
{''.join(rows_html)}
</div>
""",
        unsafe_allow_html=True
    )


# =========================
# SPREAD BETS
# =========================

with tab_objects[2 if not locks else 3]:

    st.header("Spread Bets")

    spread_rows = spread_bets.reset_index(drop=True)

    for i in range(0, len(spread_rows), 2):
        cols = st.columns(2)
        for col, (_, r) in zip(cols, spread_rows.iloc[i:i + 2].iterrows()):
            with col:
                lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Spread Edge']:+.2f}
"""
                render_card(r["Game Time"], r["Game"], lines, r["Confidence"], glow="green", compact=True)


# =========================
# TOTAL BETS
# =========================

with tab_objects[3 if not locks else 4]:

    st.header("Total Bets")

    total_rows = total_bets.reset_index(drop=True)

    for i in range(0, len(total_rows), 2):
        cols = st.columns(2)
        for col, (_, r) in zip(cols, total_rows.iloc[i:i + 2].iterrows()):
            with col:
                lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Total Edge']:+.2f}
"""
                render_card(r["Game Time"], r["Game"], lines, r["Confidence"], glow="green", compact=True)


# =========================
# ENGINE TAB
# =========================

with tab_objects[4 if not locks else 5]:

    st.header("Engine")

    def edge_color(edge):
        if edge > 0:
            return "#16a34a"
        if edge < 0:
            return "#dc2626"
        return "#6b7280"

    def render_engine_card(row):
        with st.container(border=True):
            top = st.columns([1, 4])
            with top[0]:
                st.caption("Game Time")
                st.write(row["Game Time"])
            with top[1]:
                st.markdown(f"**{row['Game']}**")

            spread_cols = st.columns([1, 1, 1])
            with spread_cols[0]:
                st.caption("Spread")
                st.write(f"{row['Spread']:+.1f}")
            with spread_cols[1]:
                st.caption("Model")
                st.write(f"{row['Model Spread']:+.1f}")
            with spread_cols[2]:
                st.caption("Edge")
                st.write(f"{row['Spread Edge']:+.1f}")

            st.markdown("")

            total_cols = st.columns([1, 1, 1])
            with total_cols[0]:
                st.caption("Total")
                st.write(f"{row['Total']:.1f}")
            with total_cols[1]:
                st.caption("Model")
                st.write(f"{row['Model Total']:.1f}")
            with total_cols[2]:
                st.caption("Edge")
                st.write(f"{row['Total Edge']:+.1f}")

    for i in range(0, len(engine), 2):
        cols = st.columns(2)
        for col, (_, row) in zip(cols, engine.iloc[i:i + 2].iterrows()):
            with col:
                render_engine_card(row)


# =========================
# PERFORMANCE
# =========================

with tab_objects[-1]:

    st.header("🔥 Model Performance")

    left, right = st.columns(2)

    with left:

        st.markdown("### 🔥 Spread Performance")

        st.markdown(f"""
<div style="
border:2px solid #16a34a;
border-radius:14px;
padding:20px;
margin-bottom:16px;
box-shadow:0 0 15px rgba(34,197,94,0.8);
background:rgba(34,197,94,0.08);
">

<b>Overall Spread Bets:</b> {spread_perf["bets"]}<br>
<b>Overall Win %:</b> {spread_perf["winpct"]}

</div>
""", unsafe_allow_html=True)

    with right:

        st.markdown("### 🔥 Totals Performance")

        st.markdown(f"""
<div style="
border:2px solid #16a34a;
border-radius:14px;
padding:20px;
margin-bottom:16px;
box-shadow:0 0 15px rgba(34,197,94,0.8);
background:rgba(34,197,94,0.08);
">

<b>Overall Total Bets:</b> {total_perf["overall_bets"]}<br>
<b>Overall Win %:</b> {total_perf["overall_pct"]}<br><br>

<b>Total Over Bets:</b> {total_perf["over_bets"]}<br>
<b>Over Win %:</b> {total_perf["over_pct"]}<br><br>

<b>Total Under Bets:</b> {total_perf["under_bets"]}<br>
<b>Under Win %:</b> {total_perf["under_pct"]}

</div>
""", unsafe_allow_html=True)
