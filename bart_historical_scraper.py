import pandas as pd
from playwright.sync_api import sync_playwright

SEASONS = {
    "2022-23": "2023",
    "2023-24": "2024",
    "2024-25": "2025"
}

BASE_URL = "https://barttorvik.com/trank.php?year={year}"

def clean_number(text):
    return float(text.split("\n")[0].strip())

def clean_team(text):
    return text.split("\n")[0].strip()

def scrape_season(year_label, year_value):
    print(f"\nScraping {year_label}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = BASE_URL.format(year=year_value)
        page.goto(url)
        page.wait_for_timeout(6000)

        table = page.locator("table").first
        rows = table.locator("tr")

        data = []

        for i in range(1, rows.count()):
            cols = rows.nth(i).locator("td")

            if cols.count() < 15:
                continue

            try:
                team_raw = cols.nth(1).inner_text()
                team = clean_team(team_raw)

                adjoe = clean_number(cols.nth(5).inner_text())
                adjde = clean_number(cols.nth(6).inner_text())
                tempo = clean_number(cols.nth(7).inner_text())
                wab = clean_number(cols.nth(14).inner_text())

                data.append({
                    "SEASON": year_label,
                    "TEAM": team,
                    "ADJOE": adjoe,
                    "ADJDE": adjde,
                    "TEMPO": tempo,
                    "WAB": wab
                })

            except:
                continue

        browser.close()

    return pd.DataFrame(data)


def main():
    all_data = []

    for label, year in SEASONS.items():
        df = scrape_season(label, year)
        all_data.append(df)

    final_df = pd.concat(all_data, ignore_index=True)
    final_df.to_csv("data/historical_efficiency_3yr.csv", index=False)

    print("\nSaved to data/historical_efficiency_3yr.csv")


if __name__ == "__main__":
    main()
