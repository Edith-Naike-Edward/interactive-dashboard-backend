from datetime import datetime
import json
from pathlib import Path
import pandas as pd

DATA_PATH = Path("data/previous_counts.json")
SITE_CSV = Path("data/raw/sites.csv")
USER_CSV = Path("data/raw/users.csv")
HISTORICAL_DATA_PATH = Path("data/historical_activity.json")

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

def save_historical_data(active_sites, active_users):
    """Save daily activity counts with timestamp"""
    try:
        # Load existing data or create new structure
        if HISTORICAL_DATA_PATH.exists():
            with open(HISTORICAL_DATA_PATH) as f:
                historical_data = json.load(f)
        else:
            historical_data = {"sites": [], "users": []}
        
        # Get current date (just date, no time)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check if we already have data for today
        if historical_data["sites"] and historical_data["sites"][-1]["date"] == today:
            # Update today's entry
            historical_data["sites"][-1]["count"] = active_sites
            historical_data["users"][-1]["count"] = active_users
        else:
            # Add new entry
            historical_data["sites"].append({"date": today, "count": active_sites})
            historical_data["users"].append({"date": today, "count": active_users})
        
        # Keep only last 30 days of data
        historical_data["sites"] = historical_data["sites"][-30:]
        historical_data["users"] = historical_data["users"][-30:]
        
        # Save back to file
        with open(HISTORICAL_DATA_PATH, 'w') as f:
            json.dump(historical_data, f)
            
    except Exception as e:
        print(f"Error saving historical data: {e}")
