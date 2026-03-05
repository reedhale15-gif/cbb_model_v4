import requests
import time
import csv
import os

# ==============================
# CONFIGURATION
# ==============================

APIFY_API_TOKEN = ""
ACTOR_ID = "PlyfIMsOwiVC7xgOw"

SEASONS = [2021, 2022, 2023, 2024, 2025]

TEAMS = [
    "Duke Blue Devils",
    "North Carolina Tar Heels",
    "Virginia Cavaliers",
    "Miami Hurricanes",
    "Clemson Tigers",
    "NC State Wolfpack",
    "Wake Forest Demon Deacons",
    "Florida State Seminoles",
    "Louisville Cardinals",
    "Syracuse Orange",
    "Georgia Tech Yellow Jackets",
    "Notre Dame Fighting Irish",
    "Boston College Eagles",
    "Pittsburgh Panthers",
    "Virginia Tech Hokies",
    "Michigan Wolverines",
    "Michigan State Spartans",
    "Ohio State Buckeyes",
    "Indiana Hoosiers",
    "Illinois Fighting Illini",
    "Purdue Boilermakers",
    "Wisconsin Badgers",
    "Iowa Hawkeyes",
    "Minnesota Golden Gophers",
    "Maryland Terrapins",
    "Nebraska Cornhuskers",
    "Northwestern Wildcats",
    "Penn State Nittany Lions",
    "Rutgers Scarlet Knights",
    "Kansas Jayhawks",
    "Baylor Bears",
    "Texas Longhorns",
    "Texas Tech Red Raiders",
    "Oklahoma Sooners",
    "Oklahoma State Cowboys",
    "TCU Horned Frogs",
    "Iowa State Cyclones",
    "Kansas State Wildcats",
    "West Virginia Mountaineers",
    "Kentucky Wildcats",
    "Tennessee Volunteers",
    "Alabama Crimson Tide",
    "Arkansas Razorbacks",
    "Auburn Tigers",
    "Florida Gators",
    "Georgia Bulldogs",
    "LSU Tigers",
    "Mississippi State Bulldogs",
    "Ole Miss Rebels",
    "South Carolina Gamecocks",
    "Missouri Tigers",
    "Texas A&M Aggies",
    "Vanderbilt Commodores",
    "UConn Huskies",
    "Villanova Wildcats",
    "Creighton Bluejays",
    "Marquette Golden Eagles",
    "Seton Hall Pirates",
    "Xavier Musketeers",
    "St. John's Red Storm",
    "Providence Friars",
    "Georgetown Hoyas",
    "Butler Bulldogs"
]

OUTPUT_FILE = "historical_boxscores_raw.csv"

# ==============================
# FUNCTIONS
# ==============================

def run_actor(season, team):
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_API_TOKEN}"

    payload = {
        "season": season,
        "team": team
    }

    response = requests.post(url, json=payload)

    if response.status_code != 201:
        print(f"❌ Failed to start actor for {team} {season}")
        print(response.text)
        return None

    return response.json()["data"]["id"]

def wait_for_run(run_id):
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"

    while True:
        response = requests.get(status_url)
        data = response.json()["data"]
        status = data["status"]

        if status == "SUCCEEDED":
            print("DEBUG RUN DATA:", data)
            return data.get("defaultDatasetId") or data.get("datasetId")

        elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
            print(f"❌ Run failed: {status}")
            print("DEBUG RUN DATA:", data)
            return None

        print("⏳ Waiting...")
        time.sleep(10)


def fetch_dataset(dataset_id):
    dataset_url = (
        f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        f"?view=overview&format=json&clean=true&token={APIFY_API_TOKEN}"
    )

    response = requests.get(dataset_url)

    if response.status_code != 200:
        print("❌ Failed to fetch dataset")
        print(response.text)
        return None

    data = response.json()

    if not data:
        print("❌ Dataset returned 0 rows.")
        return None

    return data

def append_to_csv(data):
    file_exists = os.path.isfile(OUTPUT_FILE)

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = None

        for row in data:
            if writer is None:
                fieldnames = row.keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

            writer.writerow(row)


# ==============================
# MAIN (TEST MODE)
# ==============================

TEST_SEASON = 2021
TEST_TEAM = "Duke Blue Devils"

print(f"\n🚀 TESTING {TEST_TEAM} — Season {TEST_SEASON}")

run_id = run_actor(TEST_SEASON, TEST_TEAM)

if run_id:
    dataset_id = wait_for_run(run_id)
    if dataset_id:
        data = fetch_dataset(dataset_id)
        if data:
            append_to_csv(data)
            print("✅ TEST SUCCESSFUL — Data saved.")
        else:
            print("❌ Failed fetching dataset.")
    else:
        print("❌ Run failed.")
else:
    print("❌ Actor did not start.")
