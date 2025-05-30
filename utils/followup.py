import os
from pathlib import Path
from typing import Dict
import africastalking
import pandas as pd
import json
from datetime import datetime, timedelta
import time
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sib_api_v3_sdk import Configuration, ApiClient
from sib_api_v3_sdk.api import transactional_emails_api
from sib_api_v3_sdk.models import SendSmtpEmail
import requests

# Define paths
DIAGNOSES_PATH = Path("data/raw/diagnoses.csv")
BP_LOGS_PATH = Path("data/raw/bp_logs.csv")
GLUCOSE_LOGS_PATH = Path("data/raw/glucose_logs.csv")
HISTORICAL_METRICS_PATH = Path("data/historical_metrics.json")

# Configuration
MIN_COMPARISON_INTERVAL = 300  # 5 minutes in seconds
MAX_HISTORICAL_METRICS = 1000
MAX_HISTORICAL_ALERTS = 100

# Notification settings
SMS_RECIPIENTS = ["+254721685600", "+254702171841"]
EMAIL_RECIPIENTS = ["edithnaike@gmail.com"]
SMS_SENDER_ID = "Masterclass"
EMAIL_SENDER = {"name": "Edith", "email": "edith_naike27@students.uonbi.ac.ke"}


def load_data_safely(file_path, required_columns=None):
    """Safe data loading with validation"""
    try:
        df = pd.read_csv(file_path)
        if required_columns:
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def get_most_recent_comparable_metrics():
    """Get metrics that are old enough for comparison"""
    historical_data = load_historical_data()
    if not historical_data or not historical_data.get("metrics"):
        return None
    
    now = datetime.now()
    comparable_metrics = [
        m for m in historical_data["metrics"]
        if (now - datetime.fromisoformat(m["timestamp"])).total_seconds() > MIN_COMPARISON_INTERVAL
    ]
    
    return max(comparable_metrics, key=lambda x: x["timestamp"]) if comparable_metrics else None

def calculate_followup_metrics():
    """Calculate followup metrics with robust error handling"""
    default_metrics = {
            "current_metrics": {
                "percent_new_diagnoses": 0,
                "percent_bp_followup": 0,
                "percent_bg_followup": 0,
                "percent_bp_controlled": 0,
                "timestamp": datetime.now().isoformat()
            },
            "historical_data": [],
            "last_checked": datetime.now().isoformat(),
            "performance_declined": False,
            "threshold_violations": {
                "new_diagnoses": False,
                "bp_followup": False,
                "bg_followup": False,
                "bp_controlled": False
            }
        }
    
    try:
        # Load data with validation
        diagnoses_df = load_data_safely(DIAGNOSES_PATH, ["patient_track_id", "diabetes_patient_type", "htn_patient_type"])
        bp_logs_df = load_data_safely(BP_LOGS_PATH, ["patient_track_id", "avg_systolic", "avg_diastolic"])
        glucose_logs_df = load_data_safely(GLUCOSE_LOGS_PATH, ["patient_track_id"])
        
        if diagnoses_df is None or bp_logs_df is None or glucose_logs_df is None:
            print("Warning: One or more data files could not be loaded")
            return default_metrics
        
        # Calculate metrics with division protection
        total_diagnosed = diagnoses_df["patient_track_id"].nunique()
        new_diagnoses = diagnoses_df[
            (diagnoses_df['diabetes_patient_type'] == 'Newly diagnosed') |
            (diagnoses_df['htn_patient_type'] == 'Newly diagnosed')
        ]["patient_track_id"].nunique()
        
        bp_patients = bp_logs_df["patient_track_id"].nunique()
        bp_followup_counts = bp_logs_df.groupby("patient_track_id").size()
        bp_followup = bp_followup_counts[bp_followup_counts > 1].count() if bp_patients > 0 else 0
        
        bg_patients = glucose_logs_df["patient_track_id"].nunique()
        bg_followup_counts = glucose_logs_df.groupby("patient_track_id").size()
        bg_followup = bg_followup_counts[bg_followup_counts > 1].count() if bg_patients > 0 else 0

        # BP control metrics
        bp_controlled_count = 0
        if bp_patients > 0:
            bp_controlled = bp_logs_df.groupby("patient_track_id").agg({
                'avg_systolic': 'mean',
                'avg_diastolic': 'mean'
            })
            bp_controlled_count = len(bp_controlled[
                (bp_controlled['avg_systolic'] < 140) & 
                (bp_controlled['avg_diastolic'] < 90)
            ])

        # Calculate percentages and threshold violations
        new_diag_percent = round((new_diagnoses / total_diagnosed * 100) if total_diagnosed > 0 else 0, 2)
        bp_followup_percent = round((bp_followup / bp_patients * 100) if bp_patients > 0 else 0, 2)
        bg_followup_percent = round((bg_followup / bg_patients * 100) if bg_patients > 0 else 0, 2)
        bp_controlled_percent = round((bp_controlled_count / bp_patients * 100) if bp_patients > 0 else 0, 2)

        new_diag_violation = (new_diag_percent < 50) if total_diagnosed > 0 else True
        bp_followup_violation = (bp_followup_percent < 50) if bp_patients > 0 else True
        bg_followup_violation = (bg_followup_percent < 50) if bg_patients > 0 else True
        bp_controlled_violation = (bp_controlled_percent < 50) if bp_patients > 0 else True

        # Convert numpy types to native Python types before returning
        default_metrics["performance_declined"] = bool(default_metrics["performance_declined"])
        for key in default_metrics["threshold_violations"]:
            default_metrics["threshold_violations"][key] = bool(default_metrics["threshold_violations"][key])

        default_metrics.update({
            "current_metrics": {
                "percent_new_diagnoses": new_diag_percent,
                "percent_bp_followup": bp_followup_percent,
                "percent_bg_followup": bg_followup_percent,
                "percent_bp_controlled": bp_controlled_percent,
                "timestamp": datetime.now().isoformat()
            },
            "performance_declined": new_diag_violation or bp_followup_violation or bg_followup_violation or bp_controlled_violation,
            "threshold_violations": {
                "new_diagnoses": new_diag_violation,
                "bp_followup": bp_followup_violation,
                "bg_followup": bg_followup_violation,
                "bp_controlled": bp_controlled_violation
            }
        })
        
    except Exception as e:
        print(f"Error calculating metrics: {e}")
    
    return default_metrics

def calculate_percentage_change(previous, current):
    """Safe percentage change calculation"""
    if previous is None or previous == 0:
        return 0
    return round(((current - previous) / previous) * 100, 2)

def load_historical_data():
    """Load historical data with validation"""
    default_data = {"metrics": [], "alerts": []}
    
    if not HISTORICAL_METRICS_PATH.exists():
        return default_data
    
    try:
        with open(HISTORICAL_METRICS_PATH, 'r') as f:
            content = f.read().strip()
            if not content:
                return default_data
            
            data = json.loads(content)
            # Validate structure
            if not isinstance(data, dict):
                return default_data
            if "metrics" not in data:
                data["metrics"] = []
            if "alerts" not in data:
                data["alerts"] = []
                
            return data
            
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading historical data: {e}")
        return default_data

def save_historical_data(current_metrics):
    """Save metrics to historical data with proper comparison"""
    try:
        historical_data = load_historical_data()
        previous_metrics = get_most_recent_comparable_metrics()
        
        # Add current metrics
        historical_data["metrics"].append(current_metrics["current_metrics"])
        
        # Calculate changes if we have previous metrics to compare with
        if previous_metrics:
            changes = {
                "new_diagnoses": calculate_percentage_change(
                    previous_metrics["percent_new_diagnoses"],
                    current_metrics["current_metrics"]["percent_new_diagnoses"]
                ),
                "bp_followup": calculate_percentage_change(
                    previous_metrics["percent_bp_followup"],
                    current_metrics["current_metrics"]["percent_bp_followup"]
                ),
                "bg_followup": calculate_percentage_change(
                    previous_metrics["percent_bg_followup"],
                    current_metrics["current_metrics"]["percent_bg_followup"]
                ),
                "bp_controlled": calculate_percentage_change(
                    previous_metrics["percent_bp_controlled"],
                    current_metrics["current_metrics"]["percent_bp_controlled"]
                )
            }
            
            current_metrics["current_metrics"]["changes"] = changes
            
            # Create alert if performance declined
            if current_metrics["performance_declined"]:
                alert = {
                    "timestamp": current_metrics["current_metrics"]["timestamp"],
                    "metrics": current_metrics["current_metrics"].copy(),
                    "changes": changes
                }
                historical_data["alerts"].append(alert)
        
        # Trim data to maintain size limits
        historical_data["metrics"] = historical_data["metrics"][-MAX_HISTORICAL_METRICS:]
        historical_data["alerts"] = historical_data["alerts"][-MAX_HISTORICAL_ALERTS:]
        
        # Save back to file
        HISTORICAL_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORICAL_METRICS_PATH, 'w') as f:
            json.dump(historical_data, f, indent=2)
            
        # Update the historical data in the response
        current_metrics["historical_data"] = historical_data["metrics"]
        return current_metrics
        
    except Exception as e:
        print(f"Error saving historical data: {e}")
        return None

def send_sms_alert(message: str):
    """Send SMS alert via Africa's Talking"""
    try:
        response = africastalking.SMS.send(message, SMS_RECIPIENTS, sender_id=SMS_SENDER_ID)
        print(f"SMS sent: {response}")
        return True
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return False

# def send_email_alert(subject: str, message: str):
#     """Send email alert via SendinBlue"""
#     try:
#         import os
#         print("SENDINBLUE_API_KEY =", os.getenv("SENDINBLUE_API_KEY")) 
#         send_smtp_email = SendSmtpEmail(
#             to=[{"email": email, "name": "Admin"} for email in EMAIL_RECIPIENTS],
#             sender=EMAIL_SENDER,
#             subject=subject,
#             html_content=f"<p>{message}</p>"
#         )
#         response = transactional_emails_api.TransactionalEmailsApi(ApiClient(Configuration())).send_transac_email(send_smtp_email)
#         print(f"Email sent: {response}")
#         return True
#     except Exception as e:
#         print(f"Failed to send email: {e}")
#         return False
SENDINBLUE_API_KEY = os.getenv("SENDINBLUE_API_KEY")
EMAIL_API_URL = "https://api.brevo.com/v3/smtp/email"

def send_email_alert(subject: str, message: str):
    """Send email alert using Sendinblue (Brevo) with requests"""
    headers = {
        "accept": "application/json",
        "api-key": SENDINBLUE_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {"name": EMAIL_SENDER["name"], "email": EMAIL_SENDER["email"]},
        "to": [{"email": email, "name": "Edith Naike"} for email in EMAIL_RECIPIENTS],
        "subject": subject,
        "htmlContent": f"<html><body><p>{message}</p></body></html>"
    }

    try:
        response = requests.post(EMAIL_API_URL, headers=headers, json=payload)
        print(f"Email response code: {response.status_code}")
        print(f"Email response: {response.json()}")
        return response.status_code == 201
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def generate_alerts(metrics_data: Dict) -> Dict:
    """Generate alerts based on metrics data"""
    alerts = []
    timestamp = datetime.now().isoformat()
    
    # Check threshold violations
    if metrics_data["threshold_violations"]["new_diagnoses"]:
        alert_msg = f"New diagnoses below threshold: {metrics_data['current_metrics']['percent_new_diagnoses']}%"
        alerts.append({
            "type": "new_diagnoses_threshold",
            "severity": "high",
            "message": alert_msg,
            "timestamp": timestamp
        })
        send_sms_alert(f"ALERT: {alert_msg}")
        send_email_alert("New Diagnoses Alert", alert_msg)
    
    if metrics_data["threshold_violations"]["bp_followup"]:
        alert_msg = f"BP follow-up below threshold: {metrics_data['current_metrics']['percent_bp_followup']}%"
        alerts.append({
            "type": "bp_followup_threshold",
            "severity": "medium",
            "message": alert_msg,
            "timestamp": timestamp
        })
        send_sms_alert(f"ALERT: {alert_msg}")
        send_email_alert("BP Follow-up Alert", alert_msg)
    
    if metrics_data["threshold_violations"]["bg_followup"]:
        alert_msg = f"BG follow-up below threshold: {metrics_data['current_metrics']['percent_bg_followup']}%"
        alerts.append({
            "type": "bg_followup_threshold",
            "severity": "medium",
            "message": alert_msg,
            "timestamp": timestamp
        })
        send_sms_alert(f"ALERT: {alert_msg}")
        send_email_alert("BG Follow-up Alert", alert_msg)
    
    if metrics_data["threshold_violations"]["bp_controlled"]:
        alert_msg = f"BP controlled below threshold: {metrics_data['current_metrics']['percent_bp_controlled']}%"
        alerts.append({
            "type": "bp_controlled_threshold",
            "severity": "high",
            "message": alert_msg,
            "timestamp": timestamp
        })
        send_sms_alert(f"ALERT: {alert_msg}")
        send_email_alert("BP Controlled Alert", alert_msg)
    
    metrics_data["alerts"] = alerts
    return metrics_data

def followup_activity() -> Dict:
    """Main monitoring workflow"""
    # Calculate current metrics
    current_metrics = calculate_followup_metrics()
    
    # If calculate_followup_metrics failed severely, return a default
    # if not current_metrics or "current_metrics" not in current_metrics:
    #     print("Warning: Invalid metrics, returning defaults.")
    #     return current_metrics
    # Validate the structure before proceeding
    if not current_metrics or "current_metrics" not in current_metrics:
        print("Error: Invalid metrics structure returned")
        return {
            "error": "Failed to generate valid metrics",
                "timestamp": datetime.now().isoformat()
        }
    
    # Save to historical data and get enhanced metrics with changes
    enhanced_metrics = save_historical_data(current_metrics)
    
    if enhanced_metrics:
        # Generate alerts based on the metrics
        final_metrics = generate_alerts(enhanced_metrics)
        return final_metrics
    
    return current_metrics


