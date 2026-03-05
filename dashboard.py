import streamlit as st
import pandas as pd

st.set_page_config(page_title="CBB Model v4", layout="wide")

st.title("CBB Model v4")

# =========================
# LOAD DATA
# =========================

engine = pd.read_csv("data/engine.csv")

# keep only games with odds
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
# CONFIDENCE COLORS
# =========================

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
# BUILD SPREAD BET TABLE
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


# =========================
# BUILD TOTAL BET TABLE
# =========================

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
    # SPREAD BETS
    # =====================

    with col1:

        st.subheader("🔥 Top 5 Spread Bets")

        top_spreads = spread_bets.head(5)

        best_edge = None
        if not top_spreads.empty:
            best_edge = top_spreads.iloc[0]["Spread Edge"]

        for _, r in top_spreads.iterrows():

            border = "2px solid #16a34a" if r["Spread Edge"] == best_edge else "1px solid rgba(150,150,150,0.2)"

            st.markdown(
                f"""
<div style="
border:{border};
border-radius:14px;
padding:18px;
margin-bottom:16px;
box-shadow:0 2px 6px rgba(0,0,0,0.05);
">

<div style="font-size:20px;font-weight:600;margin-bottom:8px;">
{r['Game']}
</div>

<div style="font-size:16px;margin-bottom:6px;">
<b>Bet:</b> {r['Bet']}
</div>

<div style="font-size:16px;margin-bottom:6px;color:#16a34a;">
<b>Edge:</b> {r['Spread Edge']:+.2f}
</div>

<span style="
background:{confidence_color(r['Confidence'])};
color:white;
padding:4px 10px;
border-radius:8px;
font-size:13px;
font-weight:600;
">
{r['Confidence']}
</span>

</div>
""",
                unsafe_allow_html=True
            )

    # =====================
    # TOTAL BETS
    # =====================

    with col2:

        st.subheader("🔥 Top 5 Total Bets")

        top_totals = total_bets.head(5)

        best_edge = None
        if not top_totals.empty:
            best_edge = top_totals.iloc[0]["Total Edge"]

        for _, r in top_totals.iterrows():

            border = "2px solid #16a34a" if r["Total Edge"] == best_edge else "1px solid rgba(150,150,150,0.2)"

            st.markdown(
                f"""
<div style="
border:{border};
border-radius:14px;
padding:18px;
margin-bottom:16px;
box-shadow:0 2px 6px rgba(0,0,0,0.05);
">

<div style="font-size:20px;font-weight:600;margin-bottom:8px;">
{r['Game']}
</div>

<div style="font-size:16px;margin-bottom:6px;">
<b>Bet:</b> {r['Bet']}
</div>

<div style="font-size:16px;margin-bottom:6px;color:#16a34a;">
<b>Edge:</b> {r['Total Edge']:+.2f}
</div>

<span style="
background:{confidence_color(r['Confidence'])};
color:white;
padding:4px 10px;
border-radius:8px;
font-size:13px;
font-weight:600;
">
{r['Confidence']}
</span>

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
