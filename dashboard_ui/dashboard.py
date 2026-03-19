import streamlit as st
import pandas as pd
import json
import os
import sys
import gspread
from google.oauth2.service_account import Credentials

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_config import TOTAL_EDGE_MAX, TOTAL_EDGE_MIN, spread_bet_is_favorite, spread_bet_qualifies, spread_edge_band
from tournament import apply_seeds_to_dataframe

EDGE_THRESHOLD_SPREAD, MAX_SPREAD_EDGE = spread_edge_band()
EDGE_THRESHOLD_TOTAL = TOTAL_EDGE_MIN

st.set_page_config(page_title="CBB Model v4", layout="wide")

engine_path = "data/engine.csv"

if "last_engine_update" not in st.session_state:
    st.session_state.last_engine_update = os.path.getmtime(engine_path)

current_update = os.path.getmtime(engine_path)

if current_update != st.session_state.last_engine_update:
    st.session_state.last_engine_update = current_update
    st.rerun()

st.title("CBB Model v4")

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

engine["Game Time"] = pd.to_datetime(engine["Game Time"], errors="coerce")
engine["Game Time"] = (
    engine["Game Time"]
    .dt.tz_convert("US/Central")
    .dt.strftime("%-I:%M %p")
)

engine = apply_seeds_to_dataframe(engine)
engine["Game"] = engine["Away"] + " @ " + engine["Home"]

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
    sheet = client.open("CBB Model v4")

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
    (totals["Total Edge"].abs() >= EDGE_THRESHOLD_TOTAL)
    & (totals["Total Edge"].abs() <= TOTAL_EDGE_MAX)
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
        "time": r["Game Time"],
        "game": r["Game"],
        "bet_type": "Spread",
        "edge": r["Spread Edge"],
        "bet": r["Bet"],
        "confidence": confidence,
    }

for _, r in totals.iterrows():
    option = f"{r['Game']} — {r['Bet']}"
    confidence = r["Confidence"] if pd.notna(r["Confidence"]) and r["Confidence"] else "No Grade"
    lock_card_lookup[option] = {
        "time": r["Game Time"],
        "game": r["Game"],
        "bet_type": "Total",
        "edge": r["Total Edge"],
        "bet": r["Bet"],
        "confidence": confidence,
    }

# =========================
# REED'S LOCKS
# =========================

LOCK_FILE = "data/locks.json"

try:
    with open(LOCK_FILE, "r") as f:
        locks = json.load(f)
except:
    locks = []

valid_locks = [lock for lock in locks if lock in pick_options]

if admin_mode:

    st.sidebar.header("🔒 Reed's Locks of the Day")

    selected_locks = st.sidebar.multiselect(
        "Select your picks",
        pick_options,
        default=valid_locks
    )

    if selected_locks != valid_locks:
        with open(LOCK_FILE, "w") as f:
            json.dump(selected_locks, f)

    locks = selected_locks


# =========================
# CARD RENDERER
# =========================

def render_card(time, game, lines, conf=None, glow=None):

    border = "1px solid rgba(150,150,150,0.25)"
    shadow = "0 4px 12px rgba(0,0,0,0.08)"
    background = "transparent"

    if glow == "green":
        border = "2px solid #16a34a"
        shadow = "0 0 15px rgba(34,197,94,0.8)"
        background = "rgba(34,197,94,0.08)"

    if glow == "red":
        border = "2px solid #ef4444"
        shadow = "0 0 15px rgba(239,68,68,0.6)"
        background = "rgba(239,68,68,0.08)"

    conf_badge = ""

    if conf:
        conf_badge = f"""
<span style="
background:{confidence_color(conf)};
color:white;
padding:4px 10px;
border-radius:8px;
font-size:12px;
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
padding:18px;
margin-bottom:16px;
box-shadow:{shadow};
background:{background};
">

<div style="font-size:13px;color:#6b7280;margin-bottom:6px;">
{time}
</div>

<div style="font-size:20px;font-weight:600;margin-bottom:10px;">
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

        for _, r in spread_bets.head(5).iterrows():

            lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Spread Edge']:+.2f}
"""

            render_card(r["Game Time"], r["Game"], lines, r["Confidence"], glow="green")

    with col2:

        st.subheader("🔥 Top Total Bets")

        for _, r in total_bets.head(5).iterrows():

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

        for lock in locks:

            lock_data = lock_card_lookup.get(lock)

            if not lock_data:
                continue

            lines = f"""
<b>{lock_data['bet_type']}: {lock_data['bet']}</b><br>
<b>Edge: {lock_data['edge']:+.2f}</b><br>
<b>Bet: {lock_data['bet']}</b><br>
<b>Confidence Grade: {lock_data['confidence']}</b>
"""

            render_card(
                f"<b>{lock_data['time']}</b>",
                lock_data["game"],
                lines,
                lock_data["confidence"],
                glow="red"
            )


# =========================
# GAMES TAB
# =========================

with tab_objects[1 if not locks else 2]:

    st.header("Games")

    for _, r in engine.iterrows():

        lines = f"""
Spread: {r['Spread']}<br>
Total: {r['Total']}
"""

        render_card(r["Game Time"], r["Game"], lines)


# =========================
# SPREAD BETS
# =========================

with tab_objects[2 if not locks else 3]:

    st.header("Spread Bets")

    for _, r in spread_bets.iterrows():

        lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Spread Edge']:+.2f}
"""

        render_card(r["Game Time"], r["Game"], lines, r["Confidence"], glow="green")


# =========================
# TOTAL BETS
# =========================

with tab_objects[3 if not locks else 4]:

    st.header("Total Bets")

    for _, r in total_bets.iterrows():

        lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Total Edge']:+.2f}
"""

        render_card(r["Game Time"], r["Game"], lines, r["Confidence"], glow="green")


# =========================
# ENGINE TAB
# =========================

with tab_objects[4 if not locks else 5]:

    st.header("Engine")

    def highlight_edges(val, col):
        if col == "Spread Edge" and abs(val) >= 10:
            return "background-color: rgba(34,197,94,0.6)"
        if col == "Total Edge" and abs(val) >= 6 and abs(val) <= 12:
            return "background-color: rgba(34,197,94,0.6)"
        return ""

    styled = engine.style.applymap(
        lambda v: highlight_edges(v, "Spread Edge"),
        subset=["Spread Edge"]
    ).applymap(
        lambda v: highlight_edges(v, "Total Edge"),
        subset=["Total Edge"]
    )

    st.dataframe(styled, use_container_width=True)


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
