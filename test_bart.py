import requests
import pandas as pd

url = "https://barttorvik.com/trank.php"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

print("Status Code:", response.status_code)

if response.status_code == 200:
    try:
        tables = pd.read_html(response.text)
        print("Number of tables found:", len(tables))
        print(tables[0].head())
    except Exception as e:
        print("Error reading tables:", e)
else:
    print("Failed to fetch page.")
