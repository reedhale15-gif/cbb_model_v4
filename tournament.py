import re
from typing import Iterable

import pandas as pd

TOURNAMENT_SEEDS = {
    "Duke": 1,
    "Arizona": 1,
    "Michigan": 1,
    "Florida": 1,
    "UConn": 2,
    "Purdue": 2,
    "Iowa St.": 2,
    "Houston": 2,
    "Michigan St.": 3,
    "Gonzaga": 3,
    "Virginia": 3,
    "Illinois": 3,
    "Kansas": 4,
    "Arkansas": 4,
    "Alabama": 4,
    "Nebraska": 4,
    "St. John's": 5,
    "Wisconsin": 5,
    "Texas Tech": 5,
    "Vanderbilt": 5,
    "Louisville": 6,
    "BYU": 6,
    "Tennessee": 6,
    "North Carolina": 6,
    "UCLA": 7,
    "Miami (FL)": 7,
    "Kentucky": 7,
    "Saint Mary's": 7,
    "Ohio St.": 8,
    "Villanova": 8,
    "Georgia": 8,
    "Clemson": 8,
    "TCU": 9,
    "Utah St.": 9,
    "Saint Louis": 9,
    "Iowa": 9,
    "UCF": 10,
    "Missouri": 10,
    "Santa Clara": 10,
    "Texas A&M": 10,
    "South Florida": 11,
    "Texas": 11,
    "NC State": 11,
    "Miami (OH)": 11,
    "SMU": 11,
    "VCU": 11,
    "Northern Iowa": 12,
    "High Point": 12,
    "Akron": 12,
    "McNeese St.": 12,
    "Cal Baptist": 13,
    "Hawai'i": 13,
    "Hofstra": 13,
    "Troy": 13,
    "North Dakota": 14,
    "Kennesaw St.": 14,
    "Wright St.": 14,
    "Penn": 14,
    "Furman": 15,
    "Queens": 15,
    "Tennessee St.": 15,
    "Idaho": 15,
    "Siena": 16,
    "Long Island": 16,
    "UMBC": 16,
    "Howard": 16,
    "Prairie View A&M": 16,
    "Lehigh": 16,
}

SEED_ALIASES = {
    "iowa state": "Iowa St.",
    "michigan state": "Michigan St.",
    "ohio state": "Ohio St.",
    "utah state": "Utah St.",
    "mcneese": "McNeese St.",
    "mcneese state": "McNeese St.",
    "saint marys": "Saint Mary's",
    "st marys": "Saint Mary's",
    "saint louis": "Saint Louis",
    "st louis": "Saint Louis",
    "north carolina state": "NC State",
    "n c state": "NC State",
    "nc state": "NC State",
    "miami fl": "Miami (FL)",
    "miami florida": "Miami (FL)",
    "miami ohio": "Miami (OH)",
    "miami oh": "Miami (OH)",
    "hawaii": "Hawai'i",
    "kennesaw state": "Kennesaw St.",
    "wright state": "Wright St.",
    "tennessee state": "Tennessee St.",
    "long island university": "Long Island",
    "liu": "Long Island",
    "long island": "Long Island",
}

DISPLAY_ALIASES = {
    "Iowa State": "Iowa St.",
    "Michigan State": "Michigan St.",
    "Ohio State": "Ohio St.",
    "Utah State": "Utah St.",
    "McNeese State": "McNeese St.",
    "N.C. State": "NC State",
    "NC State": "NC State",
    "Miami (FL)": "Miami (FL)",
    "Miami (OH)": "Miami (OH)",
    "Saint Mary's": "Saint Mary's",
    "Saint Louis": "Saint Louis",
    "Hawaii": "Hawai'i",
    "Kennesaw State": "Kennesaw St.",
    "Wright State": "Wright St.",
    "Tennessee State": "Tennessee St.",
    "LIU": "Long Island",
    "Long Island": "Long Island",
}


def _normalize_team_name(name: str) -> str:
    normalized = str(name).strip().lower()
    normalized = normalized.replace("&", " and ")
    normalized = normalized.replace("'", "")
    normalized = normalized.replace(".", " ")
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace("(", " ")
    normalized = normalized.replace(")", " ")
    normalized = re.sub(r"\bsaint\b", "st", normalized)
    normalized = re.sub(r"\bstate\b", "st", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


SEED_LOOKUP = {
    _normalize_team_name(team): seed
    for team, seed in TOURNAMENT_SEEDS.items()
}

for alias, canonical in SEED_ALIASES.items():
    SEED_LOOKUP[_normalize_team_name(alias)] = TOURNAMENT_SEEDS[canonical]


def get_seed(team_name: str):
    return SEED_LOOKUP.get(_normalize_team_name(team_name))


def format_seeded_team(team_name: str) -> str:
    seed = get_seed(team_name)
    if seed is None:
        return team_name
    return f"({seed}) {team_name}"


def apply_seeds_to_dataframe(
    df: pd.DataFrame,
    team_columns: Iterable[str] = ("Home", "Away"),
    bet_columns: Iterable[str] = (),
) -> pd.DataFrame:
    seeded = df.copy()

    for col in team_columns:
        if col in seeded.columns:
            seeded[col] = seeded[col].apply(format_seeded_team)

    for col in bet_columns:
        if col in seeded.columns:
            seeded[col] = seeded[col].apply(_format_seeded_bet)

    if "Home" in seeded.columns and "Away" in seeded.columns and "Game" in seeded.columns:
        seeded["Game"] = seeded["Away"] + " @ " + seeded["Home"]

    return seeded


def _format_seeded_bet(value: str) -> str:
    bet = str(value)

    candidates = {team: team for team in TOURNAMENT_SEEDS}
    candidates.update(DISPLAY_ALIASES)

    for display_name, canonical in sorted(candidates.items(), key=lambda item: len(item[0]), reverse=True):
        seed = TOURNAMENT_SEEDS[canonical]
        seeded_pattern = re.compile(rf"\({seed}\)\s+{re.escape(display_name)}")
        if seeded_pattern.search(bet):
            return bet

        pattern = re.compile(rf"(?<!\w){re.escape(display_name)}(?!\w)")
        match = pattern.search(bet)
        if match:
            matched_text = match.group(0)
            return pattern.sub(f"({seed}) {matched_text}", bet, count=1)

    return bet
