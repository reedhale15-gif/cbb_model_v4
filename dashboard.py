import streamlit as st
import pandas as pd

st.set_page_config(page_title="CBB Model v4", layout="wide")

st.title("CBB Model v4")

# =========================
# PASSWORD PROTECTION
# =========================

PASSWORD = "lockboard"

password = st.sidebar.text_input("Enter password to edit picks", type="password")

edit_mode = password == PASSWORD


# =========================
# LOAD DATA
# =========================

engine = pd.read_csv("data/engine.csv")

engine = engine[engine["Spread"].notna()].copy()

engine["Game"] = engine["Away"] + " @ " + engine["Home"]


# =========================
# CONFIDENCE FUNCTIONS
# =========================

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


def confidence_color(conf):

    colors = {
        "A+": "#16a34a",
        "A": "#22c55e",
        "A-": "#4ade80",
        "B+": "#facc15",
        "B": "#fbbf24",
        "B-": "#f59e0b",
        "C+": "#fb923c",
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

spread_bets = spread[spread["Spread Edge"].abs() >= 4].copy()
spread_bets = spread_bets.sort_values("Spread Edge", ascending=False)


totals = engine.copy()

totals["Confidence"] = totals["Total Edge"].apply(total_confidence)

totals["Bet"] = totals.apply(
    lambda r: f"Over {r['Total']}"
    if r["Total Edge"] > 0
    else f"Under {r['Total']}",
    axis=1
)

total_bets = totals[totals["Total Edge"].abs() >= 6].copy()
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

locks = []

if edit_mode:

    st.sidebar.header("🔒 Reed's Locks of the Day")

    locks = st.sidebar.multiselect(
        "Select your picks",
        pick_options
    )

else:

    st.sidebar.info("View mode")


# =========================
# CARD FUNCTION
# =========================

def render_card(title, lines, lock=False):

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

    st.markdown(
        f"""
<div style="
border:1px solid rgba(150,150,150,0.25);
border-radius:14px;
padding:18px;
margin-bottom:14px;
box-shadow:0 3px 10px rgba(0,0,0,0.08);
">

<div style="font-size:20px;font-weight:600;margin-bottom:10px;">
{title} {badge}
</div>

{lines}

</div>
""",
        unsafe_allow_html=True
    )


# =========================
# TABS
# =========================

tabs = ["Home","Games","Spread Bets","Total Bets","Engine"]

if locks:
    tabs.insert(1,"🔒 Reed's Locks")

tabs.append("Results")

tab_objects = st.tabs(tabs)


# =========================
# HOME
# =========================

with tab_objects[0]:

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🔥 Top 5 Spread Bets")

        for _, r in spread_bets.head(5).iterrows():

            lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Spread Edge']:+.2f}
"""

            render_card(r["Game"], lines)

    with col2:

        st.subheader("🔥 Top 5 Total Bets")

        for _, r in total_bets.head(5).iterrows():

            lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Total Edge']:+.2f}
"""

            render_card(r["Game"], lines)


# =========================
# LOCK TAB
# =========================

if locks:

    with tab_objects[1]:

        st.header("🔒 Reed's Locks of the Day")

        for pick in locks:

            game, bet = pick.split(" — ")

            lines = f"""
<b>Play:</b> {bet}
"""

            render_card(game, lines, lock=True)


# =========================
# GAMES
# =========================

games_tab_index = 1 if not locks else 2

with tab_objects[games_tab_index]:

    for _, r in engine.iterrows():

        lines = f"""
<b>Spread:</b> {r['Spread']}<br>
<b>Total:</b> {r['Total']}
"""

        render_card(r["Game"], lines)


# =========================
# SPREAD BETS
# =========================

spread_tab_index = games_tab_index + 1

with tab_objects[spread_tab_index]:

    for _, r in spread_bets.iterrows():

        lines = f"""
<b>Market:</b> {r['Spread']}<br>
<b>Model:</b> {r['Model Spread']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Spread Edge']:+.2f}<br>
<b>Bet:</b> {r['Bet']}
"""

        render_card(r["Game"], lines)


# =========================
# TOTAL BETS
# =========================

total_tab_index = spread_tab_index + 1

with tab_objects[total_tab_index]:

    for _, r in total_bets.iterrows():

        lines = f"""
<b>Market:</b> {r['Total']}<br>
<b>Model:</b> {r['Model Total']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Total Edge']:+.2f}<br>
<b>Bet:</b> {r['Bet']}
"""

        render_card(r["Game"], lines)


# =========================
# ENGINE
# =========================

engine_tab_index = total_tab_index + 1

with tab_objects[engine_tab_index]:

    st.dataframe(engine, use_container_width=True)


# =========================
# RESULTS
# =========================

with tab_objects[-1]:

    st.write("Results tracking coming soon.")
