from teams.team_registry import TEAM_REGISTRY

LOOKUP = {}
UNKNOWN_TEAMS = set()

for team in TEAM_REGISTRY:

    canonical = team["canonical"]

    for key in ["canonical","bart","odds","espn"]:

        name = team[key]

        if name:
            LOOKUP[name.strip()] = canonical


def normalize_team(name):

    name = name.strip()

    if name in LOOKUP:
        return LOOKUP[name]

    # record unknown team
    UNKNOWN_TEAMS.add(name)

    return name


def report_unknown():

    if not UNKNOWN_TEAMS:
        return

    print("\n========================")
    print("NEW TEAM NAMES DETECTED")
    print("========================")

    for t in sorted(UNKNOWN_TEAMS):
        print(t)

    print("\nAdd these to team_registry.py\n")
