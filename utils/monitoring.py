from datetime import datetime
import json
from pathlib import Path
import pandas as pd

DATA_PATH = Path("data/previous_counts.json")
SITE_CSV = Path("data/raw/sites.csv")
USER_CSV = Path("data/raw/users.csv")
HISTORICAL_DATA_PATH = Path("data/historical_activity.json")

from datetime import datetime
import json
from pathlib import Path
import pandas as pd
import time

DATA_PATH = Path("data/previous_counts.json")
SITE_CSV = Path("data/raw/sites.csv")
USER_CSV = Path("data/raw/users.csv")
HISTORICAL_DATA_PATH = Path("data/historical_activity.json")
MIN_COMPARISON_INTERVAL = 300  # 5 minutes in seconds

def get_most_recent_comparable_counts():
    """Get the most recent counts that are old enough for comparison"""
    if not HISTORICAL_DATA_PATH.exists():
        return None, None

    try:
        with open(HISTORICAL_DATA_PATH) as f:
            historical_data = json.load(f)

        now = time.time()

        comparable_sites = [
            entry for entry in historical_data.get("sites", [])
            if "timestamp" in entry and
            (now - datetime.fromisoformat(entry["timestamp"]).timestamp()) > MIN_COMPARISON_INTERVAL
        ]

        comparable_users = [
            entry for entry in historical_data.get("users", [])
            if "timestamp" in entry and
            (now - datetime.fromisoformat(entry["timestamp"]).timestamp()) > MIN_COMPARISON_INTERVAL
        ]

        latest_site = max(comparable_sites, key=lambda x: x["timestamp"]) if comparable_sites else None
        latest_user = max(comparable_users, key=lambda x: x["timestamp"]) if comparable_users else None

        return (
            latest_site["count"] if latest_site else None,
            latest_user["count"] if latest_user else None
        )

    except Exception as e:
        print(f"Error reading historical data: {e}")
        return None, None


def get_current_active_counts():
    """Get current counts from CSV files with validation"""
    try:
        sites_df = pd.read_csv(SITE_CSV)
        users_df = pd.read_csv(USER_CSV)
        
        # Validate the data frames
        if "is_active" not in sites_df.columns or "is_active" not in users_df.columns:
            raise ValueError("Missing 'is_active' column in data")
            
        active_sites = sites_df[sites_df["is_active"]].shape[0]
        active_users = users_df[users_df["is_active"]].shape[0]
        
        return active_sites, active_users
    except Exception as e:
        print(f"Error reading current counts: {e}")
        return None, None

def calculate_percentage_change(previous, current):
    """Safe percentage calculation with validation"""
    if previous is None or current is None:
        return 0.0
    if previous == 0:
        return 0.0  # Avoid division by zero
    return round(((current - previous) / previous) * 100, 1)

def save_historical_data(current_sites, current_users, prev_sites, prev_users):
    """Save current counts to historical data with proper validation"""
    try:
        historical_data = {
            "sites": [],
            "users": [],
            "changes": []
        }
        
        if HISTORICAL_DATA_PATH.exists():
            with open(HISTORICAL_DATA_PATH) as f:
                try:
                    historical_data.update(json.load(f))
                except json.JSONDecodeError:
                    print("Warning: Historical data file corrupted, starting fresh")
        
        timestamp = datetime.now().isoformat()
        
        # Calculate changes
        site_change = calculate_percentage_change(prev_sites, current_sites)
        user_change = calculate_percentage_change(prev_users, current_users)
        
        # Add new entries
        historical_data["sites"].append({
            "timestamp": timestamp,
            "count": current_sites,
            "percentage_change": site_change
        })
        
        historical_data["users"].append({
            "timestamp": timestamp,
            "count": current_users,
            "percentage_change": user_change
        })
        
        historical_data["changes"].append({
            "timestamp": timestamp,
            "prev_sites": prev_sites,
            "current_sites": current_sites,
            "site_change": site_change,
            "prev_users": prev_users,
            "current_users": current_users,
            "user_change": user_change
        })
        
        # Maintain reasonable data size
        historical_data["sites"] = historical_data["sites"][-1000:]
        historical_data["users"] = historical_data["users"][-1000:]
        historical_data["changes"] = historical_data["changes"][-1000:]
        
        with open(HISTORICAL_DATA_PATH, 'w') as f:
            json.dump(historical_data, f, indent=2)
            
    except Exception as e:
        print(f"Error saving historical data: {e}")

def main():
    """Main monitoring function with proper comparison logic"""
    # 1. Get previous counts that are old enough for comparison
    prev_sites, prev_users = get_most_recent_comparable_counts()
    
    # 2. Get current counts
    current_sites, current_users = get_current_active_counts()
    
    # Handle cases where we couldn't get current data
    if current_sites is None or current_users is None:
        print("Error: Could not get current counts")
        return {
            "error": "Could not get current counts",
            "last_updated": datetime.now().isoformat()
        }
    
    # 3. If no previous data exists, use current as previous (no change)
    if prev_sites is None:
        prev_sites = current_sites
    if prev_users is None:
        prev_users = current_users
    
    # 4. Calculate changes
    sites_change = calculate_percentage_change(prev_sites, current_sites)
    users_change = calculate_percentage_change(prev_users, current_users)
    
    # 5. Save to history (with both previous and current values)
    save_historical_data(current_sites, current_users, prev_sites, prev_users)
    
    return {
        "current": {
            "sites": current_sites,
            "users": current_users
        },
        "previous": {
            "sites": prev_sites,
            "users": prev_users
        },
        "sites_percentage_change": sites_change,
        "users_percentage_change": users_change,
        "site_activity_declined_5_percent": sites_change <= -5,
        "user_activity_declined_5_percent": users_change <= -5,
        "last_updated": datetime.now().isoformat()
    }
# def get_most_recent_counts():
#     """Get the most recent counts from historical data"""
#     if not HISTORICAL_DATA_PATH.exists():
#         return None, None

#     try:
#         with open(HISTORICAL_DATA_PATH) as f:
#             historical_data = json.load(f)

#             # Get most recent site count (only consider entries with 'timestamp')
#             site_count = None
#             if historical_data.get("sites"):
#                 timestamped_sites = [site for site in historical_data["sites"] if "timestamp" in site]
#                 if timestamped_sites:
#                     latest_site = max(timestamped_sites, key=lambda x: x["timestamp"])
#                     site_count = latest_site["count"]

#             # Get most recent user count (only consider entries with 'timestamp')
#             user_count = None
#             if historical_data.get("users"):
#                 timestamped_users = [user for user in historical_data["users"] if "timestamp" in user]
#                 if timestamped_users:
#                     latest_user = max(timestamped_users, key=lambda x: x["timestamp"])
#                     user_count = latest_user["count"]

#             return site_count, user_count

#     except Exception as e:
#         print(f"Error reading historical data: {e}")
#         return None, None


# def get_current_active_counts():
#     """Get current counts from CSV files"""
#     try:
#         sites_df = pd.read_csv(SITE_CSV)
#         users_df = pd.read_csv(USER_CSV)
#         active_sites = sites_df[sites_df["is_active"]].shape[0]
#         active_users = users_df[users_df["is_active"]].shape[0]
#         return active_sites, active_users
#     except Exception as e:
#         print(f"Error reading current counts: {e}")
#         return 0, 0

# def calculate_percentage_change(previous, current):
#     """Safe percentage calculation"""
#     if previous is None or previous == 0:
#         return 0
#     return round(((current - previous) / previous) * 100, 1)

# def is_significant_drop(percentage_change):
#     """Check for significant drop"""
#     return percentage_change <= -5

# # def save_historical_data(current_sites, current_users):
# #     """Save current counts to historical data with timestamp"""
# #     try:
# #         historical_data = {
# #             "sites": [],
# #             "users": [],
# #             "changes": []
# #         }
        
# #         if HISTORICAL_DATA_PATH.exists():
# #             with open(HISTORICAL_DATA_PATH) as f:
# #                 historical_data.update(json.load(f))
        
# #         timestamp = datetime.now().isoformat()
        
# #         # Add current counts
# #         historical_data["sites"].append({
# #             "timestamp": timestamp,
# #             "count": current_sites
# #         })
# #         historical_data["users"].append({
# #             "timestamp": timestamp,
# #             "count": current_users
# #         })
        
# #         # Limit data size
# #         # historical_data["sites"] = historical_data["sites"][-1000:]
# #         # historical_data["users"] = historical_data["users"][-1000:]
        
# #         with open(HISTORICAL_DATA_PATH, 'w') as f:
# #             json.dump(historical_data, f)
            
# #     except Exception as e:
# #         print(f"Error saving historical data: {e}")
# def save_historical_data(current_sites, current_users, prev_sites, prev_users):
#     """Save current counts and percentage changes to historical data with timestamp"""
#     try:
#         historical_data = {
#             "sites": [],
#             "users": [],
#             "changes": []
#         }

#         if HISTORICAL_DATA_PATH.exists():
#             with open(HISTORICAL_DATA_PATH) as f:
#                 historical_data.update(json.load(f))

#         timestamp = datetime.now().isoformat()

#         # Calculate changes before saving
#         site_change = calculate_percentage_change(prev_sites, current_sites)
#         user_change = calculate_percentage_change(prev_users, current_users)

#         # Save entry with change included
#         historical_data["sites"].append({
#             "timestamp": timestamp,
#             "count": current_sites,
#             "percentage_change": site_change
#         })

#         historical_data["users"].append({
#             "timestamp": timestamp,
#             "count": current_users,
#             "percentage_change": user_change
#         })

#         historical_data["changes"].append({
#             "timestamp": timestamp,
#             "site_change": site_change,
#             "user_change": user_change,
#             "prev_sites": prev_sites,
#             "current_sites": current_sites,
#             "prev_users": prev_users,
#             "current_users": current_users
#         })

#         with open(HISTORICAL_DATA_PATH, 'w') as f:
#             json.dump(historical_data, f, indent=2)

#     except Exception as e:
#         print(f"Error saving historical data: {e}")

# def main():
#     """Main monitoring function using historical data for comparison"""
#     prev_sites, prev_users = get_most_recent_counts()
#     current_sites, current_users = get_current_active_counts()

#     if prev_sites is None:
#         prev_sites = current_sites
#     if prev_users is None:
#         prev_users = current_users

#     sites_change = calculate_percentage_change(prev_sites, current_sites)
#     users_change = calculate_percentage_change(prev_users, current_users)
#     sites_dropped = is_significant_drop(sites_change)
#     users_dropped = is_significant_drop(users_change)

#     save_historical_data(current_sites, current_users, prev_sites, prev_users)

#     return {
#         "current": {"sites": current_sites, "users": current_users},
#         "previous": {"sites": prev_sites, "users": prev_users},
#         "sites_percentage_change": sites_change,
#         "users_percentage_change": users_change,
#         "site_activity_declined_5_percent": sites_dropped,
#         "user_activity_declined_5_percent": users_dropped,
#         "last_updated": datetime.now().isoformat()
#     }


# def main():
#     """Main monitoring function using historical data for comparison"""
#     # 1. Get most recent counts from historical data
#     prev_sites, prev_users = get_most_recent_counts()
    
#     # 2. Get current counts
#     current_sites, current_users = get_current_active_counts()
    
#     # 3. Handle case where there's no previous data
#     if prev_sites is None:
#         prev_sites = current_sites
#     if prev_users is None:
#         prev_users = current_users
    
#     # 4. Calculate changes
#     sites_change = calculate_percentage_change(prev_sites, current_sites)
#     users_change = calculate_percentage_change(prev_users, current_users)
#     sites_dropped = is_significant_drop(sites_change)
#     users_dropped = is_significant_drop(users_change)
    
#     # 5. Save current data to history
#     save_historical_data(current_sites, current_users)
    
#     return {
#         "current_sites": current_sites,
#         "current_users": current_users,
#         "previous_sites": prev_sites,
#         "previous_users": prev_users,
#         "sites_percentage_change": sites_change,
#         "users_percentage_change": users_change,
#         "sites_dropped": sites_dropped,
#         "users_dropped": users_dropped,
#         "last_updated": datetime.now().isoformat()
#     }
