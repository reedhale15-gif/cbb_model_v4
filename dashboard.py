import streamlit as st
import pandas as pd

st.set_page_config(page_title="CBB Model v4", layout="wide")

st.title("CBB Model v4")

# =========================
# ADMIN MODE (PRIVATE LINK)
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
# ADMIN MODE (PRIVATE LINK)
# =========================

query = st.query_params

admin_mode = False

if "admin" in query and query["admin"] == "1":
    admin_mode = True


# =========================
# REED'S LOCKS
# =========================

locks = []

if admin_mode:

    st.sidebar.header("🔒 Reed's Locks of the Day")

    locks = st.sidebar.multiselect(
        "Select your picks",
        pick_options
    )


# =========================
# CARD RENDERER
# =========================

def render_card(game, lines, conf=None, edge=None, lock=False):

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

    st.markdown(
        f"""
<div style="
border:1px solid rgba(150,150,150,0.25);
border-radius:14px;
padding:18px;
margin-bottom:16px;
box-shadow:0 4px 12px rgba(0,0,0,0.08);
">

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
# CARD RENDERER
# =========================

def render_card(game, lines, conf=None, edge=None, lock=False):

    badge = ""

    if lock:
        badge += """
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

    st.markdown(
        f"""
<div style="
border:1px solid rgba(150,150,150,0.25);
border-radius:14px;
padding:18px;
margin-bottom:16px;
box-shadow:0 4px 12px rgba(0,0,0,0.08);
transition: all 0.15s ease;
">

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

tabs += ["Games", "Spread Bets", "Total Bets", "Engine", "Results"]

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

            render_card(r["Game"], lines, r["Confidence"], r["Spread Edge"])

    with col2:

        st.subheader("🔥 Top Total Bets")

        for _, r in total_bets.head(5).iterrows():

            lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Total Edge']:+.2f}
"""

            render_card(r["Game"], lines, r["Confidence"], r["Total Edge"])


# =========================
# LOCKS TAB
# =========================

# =========================
# LOCKS TAB
# =========================

if locks:

    with tab_objects[1]:

        st.header("🔒 Reed's Locks of the Day")

        cols = st.columns(2)

        for i, pick in enumerate(locks):

            game, bet = pick.split(" — ")

            row = spread_bets[spread_bets["Game"] == game]

            if row.empty:
                row = total_bets[total_bets["Game"] == game]

            r = row.iloc[0]

            edge = r["Spread Edge"] if "Spread Edge" in r else r["Total Edge"]
            conf = r["Confidence"]

            lines = f"""
<b>Bet:</b> {bet}<br>
<b style="color:#16a34a;">Edge:</b> {edge:+.2f}<br>
<b>Confidence:</b> {conf}
"""

            with cols[i % 2]:

                st.markdown(
                    f"""
<div style="
border:2px solid #ef4444;
border-radius:14px;
padding:18px;
margin-bottom:16px;
box-shadow:0 0 15px rgba(239,68,68,0.6);
background:rgba(239,68,68,0.05);
">

<div style="font-size:20px;font-weight:600;margin-bottom:10px;">
{game} 🔒
</div>

{lines}

</div>
""",
                    unsafe_allow_html=True
                )

# =========================
# GAMES
# =========================

games_index = 1 if not locks else 2

with tab_objects[games_index]:

    st.header("🎮 All Games Today")

    cols = st.columns(2)

    for i, (_, r) in enumerate(engine.iterrows()):

        lines = f"""
<b>Spread:</b> {r['Spread']}<br>
<b>Total:</b> {r['Total']}
"""

        with cols[i % 2]:
            render_card(r["Game"], lines)


# =========================
# SPREAD BETS
# =========================

spread_index = games_index + 1

with tab_objects[spread_index]:

    st.header("📈 Spread Edges")

    cols = st.columns(2)

    for i, (_, r) in enumerate(spread_bets.iterrows()):

        lines = f"""
<b>Market:</b> {r['Spread']}<br>
<b>Model:</b> {r['Model Spread']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Spread Edge']:+.2f}<br>
<b>Bet:</b> {r['Bet']}
"""

        with cols[i % 2]:
            render_card(r["Game"], lines, r["Confidence"], r["Spread Edge"])


# =========================
# TOTAL BETS
# =========================

total_index = spread_index + 1

with tab_objects[total_index]:

    st.header("📊 Total Edges")

    cols = st.columns(2)

    for i, (_, r) in enumerate(total_bets.iterrows()):

        lines = f"""
<b>Market:</b> {r['Total']}<br>
<b>Model:</b> {r['Model Total']}<br>
<b style="color:#16a34a;">Edge:</b> {r['Total Edge']:+.2f}<br>
<b>Bet:</b> {r['Bet']}
"""

        with cols[i % 2]:
            render_card(r["Game"], lines, r["Confidence"], r["Total Edge"])


# =========================
# ENGINE
# =========================

engine_index = total_index + 1

with tab_objects[engine_index]:

    st.dataframe(engine, use_container_width=True)


# =========================
# RESULTS
# =========================

with tab_objects[-1]:

    st.write("Results tracking coming soon.")
