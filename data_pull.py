import os
import pandas as pd
from datetime import datetime, timedelta
import cbbpy.mens_scraper as s


DATA_DIR = "data"


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def pull_games_for_date(date_str):
    print(f"Pulling games for {date_str}")

    game_ids = s.get_game_ids(date_str)

    all_info = []
    all_box = []

    for gid in game_ids:
        print(f"Pulling game {gid}")
        info_df, box_df, _ = s.get_game(gid, info=True, box=True, pbp=False)
        all_info.append(info_df)
        all_box.append(box_df)

    if all_info:
        info_df = pd.concat(all_info, ignore_index=True)
        box_df = pd.concat(all_box, ignore_index=True)
    else:
        info_df = pd.DataFrame()
        box_df = pd.DataFrame()

    return info_df, box_df


def save_data_append(df, filepath):
    if df.empty:
        return

    if os.path.exists(filepath):
        existing = pd.read_csv(filepath)
        combined = pd.concat([existing, df], ignore_index=True)
        combined.drop_duplicates(inplace=True)
        combined.to_csv(filepath, index=False)
    else:
        df.to_csv(filepath, index=False)


def run_data_pull():
    ensure_data_dir()

    today = datetime.today()
    yesterday = today - timedelta(days=1)

    date_str = yesterday.strftime("%m-%d-%Y")

    info_df, box_df = pull_games_for_date(date_str)

    info_path = os.path.join(DATA_DIR, "games_info.csv")
    box_path = os.path.join(DATA_DIR, "games_box.csv")

    save_data_append(info_df, info_path)
    save_data_append(box_df, box_path)

    print("Daily data pull complete.")


if __name__ == "__main__":
    run_data_pull()
