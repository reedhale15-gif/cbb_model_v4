import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
import pandas as pd
import re
from teams.team_name_normalizer import normalize_team

URL = "https://barttorvik.com/schedule.php"


def clean_matchup_string(matchup):

    matchup = re.sub(r"\b\d+\s", "", matchup)

    parts = matchup.split(" at ")

    if len(parts) != 2:
        return None, None

    away = parts[0].strip()
    home = parts[1].strip()

    # Remove all trailing broadcast tokens
    home = re.sub(r"\s+(ESPN2|ESPN|ESPN\+|FS1|BTN|SECN|ACCN|CBSSN|Peacock|Pat-T)$", "", home)

    # Remove leftover uppercase tokens
    home = re.sub(r"\s+[A-Z0-9+\-]+$", "", home)

    return away, home


def scrape_schedule():

    with sync_playwright() as p:

        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        print("Loading Bart schedule page...")
        page.goto(URL, timeout=60000)

        page.wait_for_selector("table", timeout=60000)

        rows = page.query_selector_all("table tr")

        games = []

        for row in rows:

            cells = row.query_selector_all("td")

            if len(cells) < 2:
                continue

            time = cells[0].inner_text().strip()
            matchup = cells[1].inner_text().strip()

            away, home = clean_matchup_string(matchup)

            if not away or not home:
                continue

            try:
                away = normalize_team(away)
                home = normalize_team(home)
            except:
                continue

            games.append({
                "TIME": time,
                "AWAY": away,
                "HOME": home
            })

        browser.close()

    df = pd.DataFrame(games)

    print("\nGames scraped:", len(df))
    print(df.head())

    return df


if __name__ == "__main__":
    df = scrape_schedule()
    df.to_csv("data/bart_schedule_clean.csv", index=False)
    print("Saved to data/bart_schedule_clean.csv")
