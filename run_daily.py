import subprocess
import sys

def run(script_name):
    print(f"\nRunning {script_name}...")
    result = subprocess.run([sys.executable, script_name])
    if result.returncode != 0:
        print(f"Error running {script_name}")
        sys.exit(1)

def main():
    # TORVIK DATA
    run("bart_scraper.py")
    run("bart_schedule.py")

    # ODDS
    run("odds_scraper.py")

    # MODEL
    run("efficiency_engine.py")
    run("projection_engine.py")
    run("edge_engine.py")

    # PUSH TO GOOGLE SHEETS
    run("push_to_sheets.py")

    print("\nDaily pipeline + Sheets push completed successfully.")

if __name__ == "__main__":
    main()

import subprocess

print("Pushing updated data to GitHub...")

subprocess.run(["git", "add", "data"])
subprocess.run(["git", "commit", "-m", "Daily model update"])
subprocess.run(["git", "push"])

print("Dashboard updated.")
