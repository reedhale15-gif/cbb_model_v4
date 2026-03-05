import pandas as pd
import requests
from datetime import datetime, timedelta
import os

ARCHIVE_FILE = "data/results_archive.csv"

from datetime import datetime, timedelta

yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")
START_DATE = yesterday
END_DATE = yesterday

GROUP_ID = 50  # NCAA Division I


def pull_scores():

    start = datetime.strptime(START_DATE, "%Y%m%d")
    end = datetime.strptime(END_DATE, "%Y%m%d")

    games = []

    while start <= end:

        date_str = start.strftime("%Y%m%d")

        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?groups={GROUP_ID}&limit=1000&dates={date_str}"

        r = requests.get(url)
        data = r.json()

        for event in data.get("events", []):

            comp = event["competitions"][0]

            if comp["status"]["type"]["name"] != "STATUS_FINAL":
                continue

            home = None
            away = None

            for team in comp["competitors"]:
                if team["homeAway"] == "home":
                    home = team
                else:
                    away = team

            games.append({
                "DATE": start.strftime("%Y-%m-%d"),
                "HOME": home["team"]["displayName"],
                "AWAY": away["team"]["displayName"],
                "HOME_SCORE": int(home["score"]),
                "AWAY_SCORE": int(away["score"])
            })

        start += timedelta(days=1)

    return pd.DataFrame(games)


def main():

    scores = pull_scores()

    if scores.empty:
        print("No completed games found.")
        return

    if os.path.exists(ARCHIVE_FILE):

        archive = pd.read_csv(ARCHIVE_FILE)

        scores = scores.merge(
            archive[["DATE","HOME","AWAY"]],
            on=["DATE","HOME","AWAY"],
            how="left",
            indicator=True
        )

        scores = scores[scores["_merge"] == "left_only"]

        scores = scores.drop(columns="_merge")

        archive = pd.concat([archive, scores], ignore_index=True)

    else:

        archive = scores

    archive.to_csv(ARCHIVE_FILE, index=False)

    print("Results archive updated.")
    print("Games added:", len(scores))


if __name__ == "__main__":
    main()
