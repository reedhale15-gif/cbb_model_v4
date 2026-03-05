import streamlit as st
import pandas as pd

st.set_page_config(page_title="CBB Model v4", layout="wide")

st.title("CBB Model v4")

# =========================
# LOAD DATA
# =========================

engine = pd.read_csv("data/engine.csv")

# Only keep games with market odds
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


# =========================
# BUILD BET TABLES
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

spread_bets = spread_bets.sort_values(
    "Spread Edge",
    ascending=False
)


totals = engine.copy()

totals["Confidence"] = totals["Total Edge"].apply(total_confidence)

totals["Bet"] = totals.apply(
    lambda r: f"Over {r['Total']}"
    if r["Total Edge"] > 0
    else f"Under {r['Total']}",
    axis=1
)

total_bets = totals[totals["Total Edge"].abs() >= 6].copy()

total_bets = total_bets.sort_values(
    "Total Edge",
    ascending=False
)


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
# HOME TAB
# =========================

with tab1:

    col1, col2 = st.columns(2)

    # =====================
    # LEFT — SPREAD BETS
    # =====================

    with col1:

        st.subheader("🔥 Top 5 Spread Bets")

        top_spreads = spread_bets.sort_values(
            by="Spread Edge",
            ascending=False
        ).head(5)

        for _, r in top_spreads.iterrows():

            st.markdown(
                f"""
<div style="
border:1px solid #e6e6e6;
border-radius:12px;
padding:16px;
margin-bottom:14px;
background-color:#f9f9f9;
">

<b style="font-size:18px">{r['Game']}</b><br><br>

<b>Bet:</b> {r['Bet']}<br>
<b>Edge:</b> {r['Spread Edge']:+.2f}<br>
<b>Confidence:</b> {r['Confidence']}

</div>
""",
                unsafe_allow_html=True
            )

    # =====================
    # RIGHT — TOTAL BETS
    # =====================

    with col2:

        st.subheader("🔥 Top 5 Total Bets")

        top_totals = total_bets.sort_values(
            by="Total Edge",
            ascending=False
        ).head(5)

        for _, r in top_totals.iterrows():

            st.markdown(
                f"""
<div style="
border:1px solid #e6e6e6;
border-radius:12px;
padding:16px;
margin-bottom:14px;
background-color:#f9f9f9;
">

<b style="font-size:18px">{r['Game']}</b><br><br>

<b>Bet:</b> {r['Bet']}<br>
<b>Edge:</b> {r['Total Edge']:+.2f}<br>
<b>Confidence:</b> {r['Confidence']}

</div>
""",
                unsafe_allow_html=True
            )

# =========================
# GAMES TAB
# =========================

with tab2:

    games = engine[[
        "Game",
        "Spread",
        "Total"
    ]]

    games = games.rename(
        columns={
            "Spread": "Market Spread",
            "Total": "Market Total"
        }
    )

    st.dataframe(games, use_container_width=True)


# =========================
# SPREAD BETS TAB
# =========================

with tab3:

    df = spread_bets[[
        "Game",
        "Spread",
        "Model Spread",
        "Spread Edge",
        "Bet",
        "Confidence"
    ]]

    df = df.rename(
        columns={
            "Spread": "Market Line",
            "Spread Edge": "Edge"
        }
    )

    st.dataframe(df, use_container_width=True)


# =========================
# TOTAL BETS TAB
# =========================

with tab4:

    df = total_bets[[
        "Game",
        "Total",
        "Model Total",
        "Total Edge",
        "Bet",
        "Confidence"
    ]]

    df = df.rename(
        columns={
            "Total": "Market Total",
            "Total Edge": "Edge"
        }
    )

    st.dataframe(df, use_container_width=True)


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

    df = df.rename(
        columns={
            "Spread": "Market Spread",
            "Total": "Market Total"
        }
    )

    st.dataframe(df, use_container_width=True)


# =========================
# RESULTS TAB
# =========================

with tab6:

    st.write("Results tracking coming soon.")
