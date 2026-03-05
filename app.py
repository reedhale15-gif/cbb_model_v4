import streamlit as st
import pandas as pd

st.set_page_config(page_title="CBB Model Dashboard", layout="wide")

st.title("CBB Model v4 Dashboard")

# =========================
# LOAD DATA
# =========================

engine = pd.read_csv("data/engine.csv")

engine = engine[engine["Spread"].notna()]

# =========================
# EDGE FILTER
# =========================

st.sidebar.header("Filters")

spread_edge_filter = st.sidebar.slider(
    "Minimum Spread Edge",
    0.0,
    15.0,
    4.0
)

total_edge_filter = st.sidebar.slider(
    "Minimum Total Edge",
    0.0,
    20.0,
    6.0
)

# =========================
# GAMES
# =========================

st.header("Games")

games = engine[["Home","Away","Spread","Total"]]

st.dataframe(games, use_container_width=True)

# =========================
# SPREAD EDGES
# =========================

st.header("Spread Edges")

spread = engine.copy()

spread = spread[spread["Spread Edge"].abs() >= spread_edge_filter]

spread = spread.sort_values("Spread Edge", ascending=False)

st.dataframe(
    spread[["Home","Away","Spread","Model Spread","Spread Edge"]],
    use_container_width=True
)

# =========================
# TOTAL EDGES
# =========================

st.header("Total Edges")

totals = engine.copy()

totals = totals[totals["Total Edge"].abs() >= total_edge_filter]

totals = totals.sort_values("Total Edge", ascending=False)

st.dataframe(
    totals[["Home","Away","Total","Model Total","Total Edge"]],
    use_container_width=True
)
