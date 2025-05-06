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

def save_historical_data(previous_sites, previous_users, current_sites, current_users):
    """Save both previous and current activity counts with timestamp"""
    try:
        # Load existing data or create new structure
        if HISTORICAL_DATA_PATH.exists():
            with open(HISTORICAL_DATA_PATH) as f:
                historical_data = json.load(f)
                # Ensure all required keys exist
                historical_data.setdefault("sites", [])
                historical_data.setdefault("users", [])
                historical_data.setdefault("changes", [])
        else:
            historical_data = {
                "sites": [],
                "users": [],
                "changes": []
            }
        
        # Get current timestamp
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        timestamp = now.isoformat()
        
        # Store the change record
        change_record = {
            "timestamp": timestamp,
            "previous_sites": previous_sites,
            "current_sites": current_sites,
            "previous_users": previous_users,
            "current_users": current_users
        }
        historical_data["changes"].append(change_record)
        
        # Store daily snapshot (only if it's a new day)
        if not historical_data["sites"] or historical_data["sites"][-1]["date"] != today:
            historical_data["sites"].append({
                "date": today,
                "count": current_sites,
                "timestamp": timestamp
            })
            historical_data["users"].append({
                "date": today,
                "count": current_users,
                "timestamp": timestamp
            })
        
        # Keep data size manageable
        historical_data["changes"] = historical_data["changes"][-100:]  # Keep last 100 changes
        historical_data["sites"] = historical_data["sites"][-30:]  # Keep last 30 days
        historical_data["users"] = historical_data["users"][-30:]  # Keep last 30 days
        
        # Save back to file
        with open(HISTORICAL_DATA_PATH, 'w') as f:
            json.dump(historical_data, f)
            
    except Exception as e:
        print(f"Error saving historical data: {e}")

def main():
    # 1. Load previous counts
    previous_counts = load_previous_counts()
    prev_sites = previous_counts["active_sites"]
    prev_users = previous_counts["active_users"]
    
    # 2. Get current counts
    current_sites, current_users = get_current_active_counts()
    
    # 3. Check for significant drops
    sites_dropped = detect_5_percent_drop(prev_sites, current_sites)
    users_dropped = detect_5_percent_drop(prev_users, current_users)
    
    # 4. Save historical data (including previous state)
    save_historical_data(prev_sites, prev_users, current_sites, current_users)
    
    # 5. Only now update the previous counts
    save_current_counts(current_sites, current_users)
    
    return sites_dropped, users_dropped

def calculate_decline_percentage(prev, curr):
    if prev == 0:
        return 0
    return round(((curr - prev) / prev) * 100, 1)  # one decimal place


# def main():
#     previous_counts = load_previous_counts()  # Read before overwrite
#     current_sites, current_users = get_current_active_counts()

#     # Calculate decline percentages
#     site_decline = calculate_decline_percentage(previous_counts["active_sites"], current_sites)
#     user_decline = calculate_decline_percentage(previous_counts["active_users"], current_users)

#     # Detect 5% decline
#     site_declined = site_decline <= -5
#     user_declined = user_decline <= -5

#     # Save historical snapshot (with actual previous values)
#     save_historical_data(
#         previous_sites=previous_counts["active_sites"],
#         previous_users=previous_counts["active_users"],
#         current_sites=current_sites,
#         current_users=current_users
#     )

#     # Finally update stored counts
#     save_current_counts(current_sites, current_users)

#     # Return all data needed for frontend
#     # return {
#     #     "previous": {
#     #         "sites": previous_counts["active_sites"],
#     #         "users": previous_counts["active_users"]
#     #     },
#     #     "current": {
#     #         "sites": current_sites,
#     #         "users": current_users
#     #     },
#     #     "site_decline_percent": site_decline,
#     #     "user_decline_percent": user_decline,
#     #     "site_activity_declined_5_percent": site_declined,
#     #     "user_activity_declined_5_percent": user_declined,
#     #     "historical_data": load_historical_data()  # Add this function if not exists
#     # }
#     return site_declined, user_declined

# def calculate_decline_percentage(prev, curr):
#     if prev == 0:
#         return 0
#     return round(((curr - prev) / prev) * 100, 1)

# def load_historical_data():
#     """Load historical data from file"""
#     if not HISTORICAL_DATA_PATH.exists():
#         return {"sites": [], "users": [], "changes": []}
#     with open(HISTORICAL_DATA_PATH) as f:
#         return json.load(f)
# def main():
#     previous_counts = load_previous_counts()  # Read before overwrite
#     current_sites, current_users = get_current_active_counts()

#     # Detect decline
#     site_declined = detect_5_percent_drop(previous_counts["active_sites"], current_sites)
#     user_declined = detect_5_percent_drop(previous_counts["active_users"], current_users)

#     # Save historical snapshot (with actual previous values)
#     save_historical_data(
#         previous_sites=previous_counts["active_sites"],
#         previous_users=previous_counts["active_users"],
#         current_sites=current_sites,
#         current_users=current_users
#     )

#     # Finally update stored counts
#     save_current_counts(current_sites, current_users)

#     # Optionally return these for frontend
#     return {
#         "previous": {
#             "sites": previous_counts["active_sites"],
#             "users": previous_counts["active_users"]
#         },
#         "current": {
#             "sites": current_sites,
#             "users": current_users
#         },
#         "percent_declines": {
#             "sites": calculate_decline_percentage(previous_counts["active_sites"], current_sites),
#             "users": calculate_decline_percentage(previous_counts["active_users"], current_users)
#         },
#         "site_activity_declined_5_percent": site_declined,
#         "user_activity_declined_5_percent": user_declined
#     }

# def calculate_decline_percentage(prev, curr):
#     if prev == 0:
#         return 0
#     return round(((curr - prev) / prev) * 100, 1)  # one decimal place

