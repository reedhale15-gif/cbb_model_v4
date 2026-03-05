from playwright.sync_api import sync_playwright
import pandas as pd
import re


URL = "https://barttorvik.com/schedule.php"


def clean_matchup_string(matchup):
    """
    Example:
    '26 Iowa at 27 Wisconsin FS1'
    → Away: Iowa
    → Home: Wisconsin
    """

    # Remove rankings like '26 ' or '27 '
    matchup = re.sub(r"\b\d+\s", "", matchup)

    # Split at " at "
    parts = matchup.split(" at ")

    if len(parts) != 2:
        return None, None

    away = parts[0].strip()
    home = parts[1].strip()

    # Remove trailing TV network (all caps words at end)
    home = re.sub(r"\s[A-Z0-9+]+$", "", home)

    return away, home


def scrape_schedule():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        print("Loading Bart schedule page...")
        page.goto(URL, timeout=60000)

        page.wait_for_selector("table tr", timeout=60000)

        rows = page.query_selector_all("table tr")

        games = []

        for row in rows:
            cells = row.query_selector_all("td")
            row_data = [cell.inner_text().strip() for cell in cells]

            if len(row_data) == 5:
                time = row_data[0]
                matchup = row_data[1]

                away, home = clean_matchup_string(matchup)

                if away and home:
                    games.append({
                        "TIME": time,
                        "AWAY": away,
                        "HOME": home
                    })

        browser.close()

    df = pd.DataFrame(games)

    print("Clean schedule:")
    print(df.head())

    return df


if __name__ == "__main__":
    df = scrape_schedule()
    df.to_csv("data/bart_schedule_clean.csv", index=False)
    print("Saved to data/bart_schedule_clean.csv")
