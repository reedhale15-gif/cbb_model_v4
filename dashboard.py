import streamlit as st
import pandas as pd

st.set_page_config(page_title="CBB Model v4", layout="wide")

st.title("CBB Model v4")

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
# TABS
# =========================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Home",
    "Games",
    "Spread Bets",
    "Total Bets",
    "Engine",
    "Results"
])


# =========================
# CARD FUNCTION
# =========================

def render_card(title, lines):

    st.markdown(
        f"""
<div style="
border:1px solid rgba(150,150,150,0.25);
border-radius:14px;
padding:18px;
margin-bottom:14px;
box-shadow:0 2px 6px rgba(0,0,0,0.06);
">

<div style="font-size:20px;font-weight:600;margin-bottom:10px;">
{title}
</div>

{lines}

</div>
""",
        unsafe_allow_html=True
    )


# =========================
# HOME TAB
# =========================

with tab1:

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Top Spread Bets")

        for _, r in spread_bets.head(5).iterrows():

            lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b>Edge:</b> {r['Spread Edge']:+.2f}<br>
<span style="
background:{confidence_color(r['Confidence'])};
color:white;
padding:4px 10px;
border-radius:8px;
font-size:12px;
font-weight:600;">
{r['Confidence']}
</span>
"""

            render_card(r["Game"], lines)

    with col2:

        st.subheader("Top Total Bets")

        for _, r in total_bets.head(5).iterrows():

            lines = f"""
<b>Bet:</b> {r['Bet']}<br>
<b>Edge:</b> {r['Total Edge']:+.2f}<br>
<span style="
background:{confidence_color(r['Confidence'])};
color:white;
padding:4px 10px;
border-radius:8px;
font-size:12px;
font-weight:600;">
{r['Confidence']}
</span>
"""

            render_card(r["Game"], lines)


# =========================
# GAMES TAB
# =========================

with tab2:

    for _, r in engine.iterrows():

        lines = f"""
<b>Market Spread:</b> {r['Spread']}<br>
<b>Market Total:</b> {r['Total']}
"""

        render_card(r["Game"], lines)


# =========================
# SPREAD BETS TAB
# =========================

with tab3:

    for _, r in spread_bets.iterrows():

        lines = f"""
<b>Market:</b> {r['Spread']}<br>
<b>Model:</b> {r['Model Spread']}<br>
<b>Edge:</b> {r['Spread Edge']:+.2f}<br>
<b>Bet:</b> {r['Bet']}<br>
<span style="
background:{confidence_color(r['Confidence'])};
color:white;
padding:4px 10px;
border-radius:8px;
font-size:12px;
font-weight:600;">
{r['Confidence']}
</span>
"""

        render_card(r["Game"], lines)


# =========================
# TOTAL BETS TAB
# =========================

with tab4:

    for _, r in total_bets.iterrows():

        lines = f"""
<b>Market:</b> {r['Total']}<br>
<b>Model:</b> {r['Model Total']}<br>
<b>Edge:</b> {r['Total Edge']:+.2f}<br>
<b>Bet:</b> {r['Bet']}<br>
<span style="
background:{confidence_color(r['Confidence'])};
color:white;
padding:4px 10px;
border-radius:8px;
font-size:12px;
font-weight:600;">
{r['Confidence']}
</span>
"""

        render_card(r["Game"], lines)


# =========================
# ENGINE TAB
# =========================

with tab5:

    df = engine[[
        "Game",
        "Spread",
        "Model Spread",
        "Spread Edge",
        "Total",
        "Model Total",
        "Total Edge",
        "OE Diff",
        "DE Diff"
    ]]

    df = df.rename(columns={
        "Spread": "Market Spread",
        "Total": "Market Total"
    })

    st.dataframe(df, use_container_width=True)


# =========================
# RESULTS TAB
# =========================

with tab6:

    st.write("Results tracking coming soon.")
