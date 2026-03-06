import streamlit as st
import pandas as pd
import json
import os
from streamlit_autorefresh import st_autorefresh
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CBB Model v4", layout="wide")

# =========================
# AUTO REFRESH
# =========================

st_autorefresh(interval=60000, key="datarefresh")

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

engine["Game"] = engine["Away"] + " @ " + engine["Home"]

engine["Game Time"] = pd.to_datetime(engine["Game Time"], errors="coerce")
engine["Game Time"] = (
    engine["Game Time"]
    .dt.tz_convert("US/Central")
    .dt.strftime("%-I:%M %p")
)

# =========================
# LOAD PERFORMANCE DATA
# =========================

def get_performance_data():

    import os
    import json

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # Load credentials from Render environment variable
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=scope
    )

    client = gspread.authorize(creds)
    sheet = client.open("CBB Model v4")

    spread_tab = sheet.worksheet("Spread Performance")
    total_tab = sheet.worksheet("Total Performance")

    spread_data = {
        "bets": spread_tab.acell("B5").value,
        "winpct": spread_tab.acell("B6").value
    }

    total_data = {
        "overall_bets": total_tab.acell("B5").value,
        "overall_pct": total_tab.acell("B6").value,
        "over_bets": total_tab.acell("E5").value,
        "over_pct": total_tab.acell("E6").value,
        "under_bets": total_tab.acell("H5").value,
        "under_pct": total_tab.acell("H6").value
    }

    return spread_data, total_data


spread_perf, total_perf = get_performance_data()

# =========================
# CONFIDENCE FUNCTIONS
# =========================

def spread_confidence(edge):
    edge = abs(edge)
    if edge >= 12: return "A+"
    if edge >= 10: return "A-"
    if edge >= 8: return "B+"
    if edge >= 7: return "B-"
    if edge >= 6: return "C"
    return ""


def total_confidence(edge):
    edge = abs(edge)
    if edge >= 15: return "A"
    if edge >= 10: return "B"
    if edge >= 6: return "C"
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
spread["Confidence"] = spread["Spread Edge"].apply(spread_confidence)

spread["Bet"] = spread.apply(
    lambda r: f"{r['Home']} {r['Spread']:+.1f}"
    if r["Model Spread"] < r["Spread"]
    else f"{r['Away']} {-r['Spread']:+.1f}",
    axis=1
)

spread_bets = spread[spread["Spread Edge"].abs() >= 6].copy()
spread_bets = spread_bets.sort_values("Spread Edge", ascending=False)


totals = engine.copy()
totals["Confidence"] = totals["Total Edge"].apply(total_confidence)

totals["Bet"] = totals.apply(
    lambda r: f"Over {r['Total']}"
    if r["Total Edge"] > 0
    else f"Under {r['Total']}",
    axis=1
)

total_bets = totals[(totals["Total Edge"].abs() >= 6) & (totals["Total Edge"].abs() < 20)].copy()
total_bets = total_bets.sort_values("Total Edge", ascending=False)

# =========================
# BUILD PICK OPTIONS
# =========================

spread_options = (spread_bets["Game"] + " — " + spread_bets["Bet"]).tolist()
total_options = (total_bets["Game"] + " — " + total_bets["Bet"]).tolist()

pick_options = spread_options + total_options

# =========================
# REED'S LOCKS
# =========================

LOCK_FILE = "data/locks.json"

try:
    with open(LOCK_FILE, "r") as f:
        locks = json.load(f)
except:
    locks = []

if admin_mode:

    st.sidebar.header("🔒 Reed's Locks of the Day")

    selected_locks = st.sidebar.multiselect(
        "Select your picks",
        pick_options,
        default=locks
    )

    if selected_locks != locks:
        with open(LOCK_FILE, "w") as f:
            json.dump(selected_locks, f)

    locks = selected_locks


# =========================
# CARD RENDERER
# =========================

def render_card(time, game, lines, conf=None, lock=False):

    badge = ""

    if lock:
        badge = """
<span style="
background:#ef4444;
color:white;
padding:4px 10px;
border-radius:8px;
font-size:12px;
font-weight:600;
margin-left:6px;
">
🔒 LOCK
</span>
"""

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

    border = "2px solid #ef4444" if lock else "1px solid rgba(150,150,150,0.25)"
    shadow = "0 0 15px rgba(239,68,68,0.6)" if lock else "0 4px 12px rgba(0,0,0,0.08)"
    background = "rgba(239,68,68,0.08)" if lock else "transparent"

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
{game} {badge}
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

            render_card(r["Game Time"], r["Game"], lines, r["Confidence"])

    with col2:

        st.subheader("🔥 Top Total Bets")

        for _, r in total_bets.head(5).iterrows():

            lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Total Edge']:+.2f}
"""

            render_card(r["Game Time"], r["Game"], lines, r["Confidence"])


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
