from playwright.sync_api import sync_playwright
import pandas as pd


URL = "https://barttorvik.com/trank.php"


def scrape_bart_torvik():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        print("Loading BartTorvik page...")
        page.goto(URL, timeout=60000)

        page.wait_for_selector("table tr", timeout=60000)

        rows = page.query_selector_all("table tr")

        data = []
        for row in rows:
            cells = row.query_selector_all("th, td")
            row_data = [cell.inner_text().strip() for cell in cells]
            if len(row_data) > 5:
                data.append(row_data)

        browser.close()

    df = pd.DataFrame(data)

    # Remove D-I AVG row
    df = df.iloc[1:].reset_index(drop=True)

    # Promote header row
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)

    print("Cleaned shape:", df.shape)
    print(df.head())

    return df


if __name__ == "__main__":
    df = scrape_bart_torvik()
    df.to_csv("data/bart_clean.csv", index=False)
    print("Saved to data/bart_clean.csv")
