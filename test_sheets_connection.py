import gspread
from google.oauth2.service_account import Credentials

# Define scope
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials
creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=scope
)

client = gspread.authorize(creds)

# Open your sheet (exact name)
sheet = client.open("CBB Model v4")

# Select first worksheet
worksheet = sheet.sheet1

# Write test value
worksheet.update("A1", [["CONNECTED SUCCESSFULLY"]])

print("Google Sheets connection successful.")
