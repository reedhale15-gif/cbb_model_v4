import pandas as pd


# =========================
# CLEANING HELPERS
# =========================

def clean_numeric_column(series):
    """
    Extract numeric value before newline.
    Example: '42.3\\n128' -> 42.3
    """
    return (
        series.astype(str)
        .str.split("\n")
        .str[0]
        .str.replace("+", "", regex=False)
        .astype(float)
    )


def clean_team_name(series):
    """
    Remove embedded matchup text from TEAM column.
    Example:
    'Wisconsin\\n   (H) 26 Iowa (won)' -> 'Wisconsin'
    """
    return series.astype(str).str.split("\n").str[0].str.strip()


# =========================
# BUILD EFFICIENCY TABLE
# =========================

def build_efficiency_table(filepath="data/bart_clean.csv"):

    df = pd.read_csv(filepath)

    # Remove accidental duplicated header rows
    df = df[df["RK"] != "RK"]

    df_clean = pd.DataFrame()

    # Basic identifiers
    df_clean["TEAM"] = clean_team_name(df["TEAM"])
    df_clean["CONF"] = df["CONF"]

    # Games played
    df_clean["G"] = pd.to_numeric(df["G"], errors="coerce")
    df_clean = df_clean.dropna(subset=["G"])
    df_clean["G"] = df_clean["G"].astype(int)

    # Core efficiency metrics
    df_clean["ADJOE"] = clean_numeric_column(df["ADJOE"])
    df_clean["ADJDE"] = clean_numeric_column(df["ADJDE"])
    df_clean["TEMPO"] = clean_numeric_column(df["ADJ T."])

    # Shooting
    df_clean["EFG"] = clean_numeric_column(df["EFG%"])
    df_clean["EFGD"] = clean_numeric_column(df["EFGD%"])

    # Turnovers
    df_clean["TOR"] = clean_numeric_column(df["TOR"])
    df_clean["TORD"] = clean_numeric_column(df["TORD"])

    # Rebounding
    df_clean["ORB"] = clean_numeric_column(df["ORB"])
    df_clean["DRB"] = clean_numeric_column(df["DRB"])

    # Free throw rate
    df_clean["FTR"] = clean_numeric_column(df["FTR"])
    df_clean["FTRD"] = clean_numeric_column(df["FTRD"])

    # Wins Above Bubble (recency / performance signal)
    df_clean["WAB"] = clean_numeric_column(df["WAB"])

    print("\nEfficiency table built successfully.\n")
    print(df_clean.head())

    return df_clean


# =========================

if __name__ == "__main__":
    df_eff = build_efficiency_table()
    df_eff.to_csv("data/efficiency_table.csv", index=False)
    print("\nSaved to data/efficiency_table.csv")
