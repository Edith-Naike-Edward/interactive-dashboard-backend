from datetime import datetime
import json
import os
from pathlib import Path
from typing import Dict, List
import pandas as pd
import africastalking
from sib_api_v3_sdk import Configuration, ApiClient
from sib_api_v3_sdk.api import transactional_emails_api
from sib_api_v3_sdk.models import SendSmtpEmail

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

# Notification settings
SMS_RECIPIENTS = ["+254721685600"]  # Replace with actual numbers
EMAIL_RECIPIENTS = ["edithnaike@gmail.com"]  # Replace with actual emails
SMS_SENDER_ID = "Masterclass"  # Your Africa's Talking sender ID
EMAIL_SENDER = {"name": "Alert System", "email": "alerts@students.uonbi.ac.ke"}

username = "masterclass"  # Your Africa's Talking username
AFRICASTALKING_APIKEY = os.getenv("AFRICASTALKING_APIKEY")
# Initialize SMS service
try:
    africastalking.initialize(username, AFRICASTALKING_APIKEY)  # Replace with actual credentials
    sms = africastalking.SMS
except Exception as e:
    print(f"Failed to initialize SMS service: {e}")
    sms = None

# Initialize Email service
try:
    email_config = Configuration()
    email_config.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")
    email_client = ApiClient(email_config)
    email_api = transactional_emails_api.TransactionalEmailsApi(email_client)
except Exception as e:
    print(f"Failed to initialize email service: {e}")
    email_api = None

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

def send_sms_alert(message: str):
    """Send SMS alert via Africa's Talking"""
    if not sms:
        print("SMS service not available")
        return False
        
    try:
        response = sms.send(message, SMS_RECIPIENTS, sender_id=SMS_SENDER_ID)
        print(f"SMS sent: {response}")
        return True
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return False

def send_email_alert(subject: str, message: str):
    """Send email alert via SendinBlue"""
    if not email_api:
        print("Email service not available")
        return False
    
    try:
        send_smtp_email = SendSmtpEmail(
            to=[{"email": email, "name": "Admin"} for email in EMAIL_RECIPIENTS],
            sender=EMAIL_SENDER,
            subject=subject,
            html_content=f"<p>{message}</p>"
        )
        response = email_api.send_transac_email(send_smtp_email)
        print(f"Email sent: {response}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def generate_alerts(activity_data: Dict) -> List[Dict]:
    """Generate alerts based on activity data and send notifications"""
    alerts = []
    timestamp = datetime.now().isoformat()
    
    # Check for site activity decline
    if activity_data.get("site_activity_declined_5_percent", False):
        change = activity_data["sites_percentage_change"]
        severity = "high" if change <= -10 else "medium"
        alert_msg = f"Site activity declined by {abs(change)}% (Current: {activity_data['current']['sites']}, Previous: {activity_data['previous']['sites']})"
        
        alerts.append({
            "type": "site_activity_decline",
            "severity": severity,
            "message": alert_msg,
            "timestamp": timestamp
        })
        
        # Send notifications for medium/high severity
        sms_msg = f"ALERT: Site activity declined by {abs(change)}%"
        email_subject = f"{severity.upper()} ALERT: Site Activity Decline"
        # send_sms_alert(sms_msg)
        send_email_alert(email_subject, alert_msg)
    
    # Check for user activity decline
    if activity_data.get("user_activity_declined_5_percent", False):
        change = activity_data["users_percentage_change"]
        severity = "high" if change <= -10 else "medium"
        alert_msg = f"User activity declined by {abs(change)}% (Current: {activity_data['current']['users']}, Previous: {activity_data['previous']['users']})"
        
        alerts.append({
            "type": "user_activity_decline",
            "severity": severity,
            "message": alert_msg,
            "timestamp": timestamp
        })
        
        # Send notifications
        sms_msg = f"ALERT: User activity declined by {abs(change)}%"
        email_subject = f"{severity.upper()} ALERT: User Activity Decline"
        # send_sms_alert(sms_msg)
        send_email_alert(email_subject, alert_msg)
    
    # Check for inactive sites/users
    try:
        sites_df = pd.read_csv(SITE_CSV)
        users_df = pd.read_csv(USER_CSV)
        
        # Inactive sites
        inactive_sites = sites_df[~sites_df["is_active"]]
        if len(inactive_sites) > 0:
            alert_msg = f"{len(inactive_sites)} inactive sites detected"
            alerts.append({
                "type": "inactive_sites",
                "severity": "high",
                "message": alert_msg,
                "timestamp": timestamp,
                "details": inactive_sites[["site_id", "name"]].to_dict('records')
            })
            
            # Send notifications
            sms_msg = f"ALERT: {len(inactive_sites)} inactive sites"
            email_subject = "HIGH ALERT: Inactive Sites Detected"
            send_sms_alert(sms_msg)
            send_email_alert(email_subject, alert_msg)
        
        # Inactive users
        inactive_users = users_df[~users_df["is_active"]]
        if len(inactive_users) > 0:
            alert_msg = f"{len(inactive_users)} inactive users detected"
            alerts.append({
                "type": "inactive_users",
                "severity": "medium",
                "message": alert_msg,
                "timestamp": timestamp,
                "details": inactive_users[["id", "name"]].to_dict('records')
            })
            
            # Send notifications if more than threshold
            if len(inactive_users) > 10:  # Only notify if more than 10 inactive users
                sms_msg = f"ALERT: {len(inactive_users)} inactive users"
                email_subject = "MEDIUM ALERT: Inactive Users Detected"
                send_sms_alert(sms_msg)
                send_email_alert(email_subject, alert_msg)
                
    except Exception as e:
        print(f"Error checking inactive sites/users: {e}")
    
    return alerts

def monitor_activity() -> Dict:
    """Main monitoring function with alert generation"""
    # 1. Get previous counts that are old enough for comparison
    prev_sites, prev_users = get_most_recent_comparable_counts()
    
    # 2. Get current counts
    current_sites, current_users = get_current_active_counts()
    
    # Handle cases where we couldn't get current data
    if current_sites is None or current_users is None:
        error_msg = "Could not get current counts"
        print(f"Error: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
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
    
    # 5. Determine if activity declined
    site_decline = sites_change <= -5
    user_decline = users_change <= -5
    
    # 6. Save to history
    save_historical_data(current_sites, current_users, prev_sites, prev_users)
    
    # 7. Generate activity data
    activity_data = {
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
        "site_activity_declined_5_percent": site_decline,
        "user_activity_declined_5_percent": user_decline,
        "last_updated": datetime.now().isoformat()
    }
    
    # 8. Generate and process alerts
    alerts = generate_alerts(activity_data)
    activity_data["alerts"] = alerts
    
    return activity_data