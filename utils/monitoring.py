import json
from pathlib import Path
import pandas as pd

DATA_PATH = Path("data/previous_counts.json")
SITE_CSV = Path("data/raw/sites.csv")
USER_CSV = Path("data/raw/users.csv")

def load_previous_counts():
    if not DATA_PATH.exists():
        return {"active_sites": 0, "active_users": 0}
    with open(DATA_PATH) as f:
        return json.load(f)

def save_current_counts(active_sites, active_users):
    with open(DATA_PATH, "w") as f:
        json.dump({"active_sites": active_sites, "active_users": active_users}, f)

def get_current_active_counts():
    sites_df = pd.read_csv(SITE_CSV)
    users_df = pd.read_csv(USER_CSV)

    active_sites = sites_df[sites_df["is_active"] == True].shape[0]
    active_users = users_df[users_df["is_active"] == True].shape[0]

    return active_sites, active_users

def detect_5_percent_drop(previous, current):
    if previous == 0:
        return False
    percent_change = ((current - previous) / previous) * 100
    return percent_change <= -5
