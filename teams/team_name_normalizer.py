import re
from teams.team_registry import TEAM_REGISTRY

UNKNOWN_TEAMS = {}
REGISTRY_CONFLICTS = {}

# -----------------------
# BUILD LOOKUP MAP
# -----------------------

LOOKUP = {}


def clean(name):

    name = str(name)

    # remove matchup rows
    name = name.split("vs")[0]

    # remove home/away markers
    name = re.sub(r"\((H|A)\)", "", name)

    # remove ranking numbers
    name = re.sub(r"\d+", "", name)

    # remove tournament suffixes
    name = re.sub(
        r"(NCAA-T|Horz-T|Slnd-T|MVC-T|WCC-T|CAA-T|BSky-T|SB-T|ASun-T|MAAC-T|OVC-T|Sum-T)",
        "",
        name
    )

    # normalize spaces
    name = re.sub(r"\s+", " ", name).strip().lower()

    return name


def add_lookup(alias, canonical):
    key = clean(alias)

    if not key:
        return

    existing = LOOKUP.get(key)

    if existing and existing != canonical:
        REGISTRY_CONFLICTS.setdefault(key, {existing}).add(canonical)
        return

    LOOKUP[key] = canonical

for team in TEAM_REGISTRY:

    canonical = team["canonical"]

    add_lookup(canonical, canonical)

    if team.get("bart"):
        add_lookup(team["bart"], canonical)

    if team.get("odds"):
        add_lookup(team["odds"], canonical)

    if team.get("espn"):
        add_lookup(team["espn"], canonical)


# -----------------------
# NORMALIZE TEAM
# -----------------------

def normalize_team(name, source="unknown"):

    key = clean(name)

    if key in LOOKUP:
        return LOOKUP[key]

    UNKNOWN_TEAMS.setdefault(source, set()).add(str(name))
    return name


# -----------------------
# REPORT UNKNOWN
# -----------------------

def report_unknown():

    if REGISTRY_CONFLICTS:
        print("\n========================")
        print("REGISTRY KEY CONFLICTS")
        print("========================")

        for key, canonicals in sorted(REGISTRY_CONFLICTS.items()):
            print(f"{key} => {sorted(canonicals)}")

        print("")

    if UNKNOWN_TEAMS:
        print("\n========================")
        print("NEW TEAM NAMES DETECTED")
        print("========================")

        for source, names in sorted(UNKNOWN_TEAMS.items()):
            print(f"\n[{source}]")
            for name in sorted(names):
                print(name)

        print("\nAdd these to TEAM_REGISTRY\n")
