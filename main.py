import atexit
import json
from fastapi import Depends, FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import numpy as np
from pydantic import BaseModel
from utils.monitoring import monitor_activity
from routes import router
import pandas as pd
from database import init_db, get_db
from models import Base
from sms_service import sms_service
from sqlalchemy.orm import Session
from src.generators.patientgenerator import generate_patients, _assign_health_conditions_wrapper
from src.generators.screeninglog_generator import generate_screening_log
from utils.email_utils import send_email
from src.generators.bplog_generator import generate_bp_logs
from src.generators.glucoselog_generator import generate_glucose_log
from src.generators.patientmedicalcompliance_generator import generate_patient_medical_compliances
from src.generators.patientlifestyle_generator import generate_patient_lifestyles
from src.generators.patientmedicalreview_generator import generate_patient_medical_reviews
from src.generators.patientdiagnosis_generator import generate_patient_diagnoses
from src.generators.health_metrics_generator import generate_health_metrics
from src.analytics.anomaly_detector import detect_anomalies
from src.generators.site_user_generation import generate_site_user_data
from src.generators.patient_visit_generator import generate_visits
import os
from typing import Dict, List, Optional
import os
import uuid
from fastapi import FastAPI
from models import Base
from database import engine
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Import notification functions from follow_up
from utils.followup import followup_activity, send_sms_alert, send_email_alert, SMS_RECIPIENTS, EMAIL_RECIPIENTS

app = FastAPI()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())  # Proper shutdown on app exit

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj) if not np.isnan(obj) else None
        return super().default(obj)

app.json_encoder = CustomJSONEncoder

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Or ["*"] for all origins (not recommended in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include API routes
app.include_router(router, prefix="/api")

# Ensure data directory exists
os.makedirs("data/raw", exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Interactive Health Dashboard API"}

@app.get("/ping")
def ping():
    return {"message": "API is running"}

@app.post("/generate-data")
async def generate_data(
    background_tasks: BackgroundTasks,
    num_patients: Optional[int] = 100,
    days: Optional[int] = 30,
    frequency: Optional[str] = "5 min"  # Default frequency for health metrics
):
    """Endpoint to trigger data generation"""
    background_tasks.add_task(
        run_pipeline,
        num_patients=num_patients,
        days=days,
        frequency=frequency
    )
    return {
        "message": "Data generation started in background",    
        "task_id": str(uuid.uuid4()),
        "expected_time_range": {
            "start": (datetime.now() - timedelta(days=days)).isoformat(),
            "end": datetime.now().isoformat()
        }}

@app.get("/api/anomalies")
async def get_anomalies(
    limit: int = 100,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Endpoint to fetch anomalies with filtering options"""
    try:
        # Read anomalies from CSV (or you could query from database if stored there)
        anomalies_path = "data/raw/anomalies.csv"
        if not os.path.exists(anomalies_path):
            return {"anomalies": [], "count": 0}
        
        anomalies = pd.read_csv(anomalies_path)
        
        # Apply filters if provided
        if severity:
            anomalies = anomalies[anomalies['severity'] == int(severity)]
        if alert_type:
            anomalies = anomalies[anomalies['alert_type'] == alert_type]
        
        # Convert to list of dicts
        anomalies = anomalies.head(limit).to_dict(orient='records')
        
        return {
            "anomalies": anomalies,
            "count": len(anomalies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def send_data_generation_notification(num_patients: int, days: int, success: bool = True):
    """Send notifications about data generation status including activity monitoring alerts"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get current activity metrics and alerts
    activity_data = monitor_activity()
    activity_alerts = activity_data.get("alerts", [])
    # Get current followup metrics and alerts
    followup_metrics = followup_activity()
    followup_alerts = followup_metrics.get("alerts", [])
    
    # Get current site and user stats with fallbacks
    current_sites = activity_data.get('current', {}).get('sites', 'N/A')
    current_users = activity_data.get('current', {}).get('users', 'N/A')
    site_change = activity_data.get('sites_percentage_change', 'N/A')
    user_change = activity_data.get('users_percentage_change', 'N/A')

    # Load sites and users dataframes from CSV
    try:
        sites_df = pd.read_csv("data/raw/sites.csv")
    except Exception:
        sites_df = pd.DataFrame(columns=["is_active"])
    try:
        users_df = pd.read_csv("data/raw/users.csv")
    except Exception:
        users_df = pd.DataFrame(columns=["is_active"])

    # Calculate detailed site statistics
    total_sites = len(sites_df)
    active_sites = sites_df["is_active"].sum() if "is_active" in sites_df.columns else 0
    inactive_sites = total_sites - active_sites
    site_stats = f"{inactive_sites} inactive sites, {active_sites} active sites, {total_sites} total sites"
        
    # Calculate detailed user statistics
    total_users = len(users_df)
    active_users = users_df["is_active"].sum() if "is_active" in users_df.columns else 0
    inactive_users = total_users - active_users
    user_stats = f"{inactive_users} inactive users, {active_users} active users, {total_users} total users"

    if success:
        # Base success message
        sms_message = f"Data generation completed at {timestamp}. Generated {num_patients} patients for {days} days."
        email_subject = "Data Generation Completed"
        email_message = f"""
        <p>Data generation process has completed successfully.</p>
        <p><strong>Details:</strong></p>
        <ul>
            <li>Patients generated: {num_patients}</li>
            <li>Time period: {days} days</li>
            <li>Completed at: {timestamp}</li>
        </ul>
        """
        
        # Add activity metrics summary
        email_message += f"""
        <h3>Site and User Monitoring Data Activity Metrics:</h3>
        <ul>
            <li>Active sites: {current_sites} ({site_change}% change)</li>
            <li>Active users: {current_users} ({user_change}% change)</li>
            <li>Inactive sites: {inactive_sites}</li>
            <li>Inactive users: {inactive_users}</li>
        </ul>
        """
        
        # Add activity alerts if any exist
        if activity_alerts:
            sms_message += "\n\nSITE MONITORING ACTIVITY ALERTS:"
            email_message += "<h3>Site Monitoring Activity Alerts:</h3><ul>"
            
            for alert in activity_alerts:
                # Safely get alert stats
                alert_stats = {}
                if isinstance(alert.get('stats'), dict):
                    alert_stats = alert['stats']
                elif isinstance(alert.get('stats'), str):
                    try:
                        alert_stats = json.loads(alert['stats'])
                    except (json.JSONDecodeError, TypeError):
                        alert_stats = {}
                
                alert_sites = alert_stats.get('active', current_sites)
                alert_users = alert_stats.get('active', current_users)
                # inactive_sites = alert_stats.get('total', inactive_sites)
                # inactive_users = alert_stats.get('total', inactive_users)
                
                sms_message += (
                    f"\n- This message is of severity: {alert.get('severity', 'unknown')} and it says: "
                    f"active sites: {alert_sites}, inactive sites: {inactive_sites}, total sites: {total_sites}, "
                    f"percentage change: {site_change}%, "
                    f"active users: {alert_users}, inactive users: {inactive_users}, total users: {total_users}, "
                    f"percentage change: {user_change}%"
                )
                email_message += f"<li>{alert.get('message', 'No message')} (severity: {alert.get('severity', 'unknown')})</li>"
            
            email_message += "</ul>"

        # Add followup alerts if any exist
        if followup_alerts:
            sms_message += "\n\nFOLLOW-UP ALERTS:"
            email_message += "<h3>Follow-up Current Alerts:</h3><ul>"
            
            for alert in followup_alerts:
                sms_message += f"\n- {alert.get('message', 'No message')}"
                email_message += f"<li>{alert.get('message', 'No message')} (severity: {alert.get('severity', 'unknown')})</li>"
            
            email_message += "</ul>"
        
        try:
            send_sms_alert(sms_message)
            send_email_alert(email_subject, email_message)
        except Exception as e:
            print(f"Failed to send success notifications: {e}")
    else:
        # Failure message (keep original format)
        sms_message = f"Data generation FAILED at {timestamp}. Check logs."
        email_subject = "Data Generation Failed"
        email_message = f"""
        <p>Data generation process has failed.</p>
        <p><strong>Time:</strong> {timestamp}</p>
        <p>Please check the server logs for more details.</p>
        """
        
        # # Still include activity alerts in failure case
        # if activity_alerts:
        #     sms_message += "\n\nSITE MONITORING ACTIVITY ALERTS:"
        #     email_message += "<h3>Site Monitoring Activity Alerts:</h3><ul>"
            
        #     for alert in activity_alerts:
        #         # Safely get alert stats
        #         alert_stats = {}
        #         if isinstance(alert.get('stats'), dict):
        #             alert_stats = alert['stats']
        #         elif isinstance(alert.get('stats'), str):
        #             try:
        #                 alert_stats = json.loads(alert['stats'])
        #             except (json.JSONDecodeError, TypeError):
        #                 alert_stats = {}
                
        #         alert_sites = alert_stats.get('active', current_sites)
        #         alert_users = alert_stats.get('active', current_users)
        #         inactive_sites = alert_stats.get('total', inactive_sites)
        #         inactive_users = alert_stats.get('total', inactive_users)
                
        #         sms_message += (
        #             f"\n- This message is of severity: {alert.get('severity', 'unknown')} and it says: "
        #             f"active sites: {alert_sites},"
        #             f" inactive sites: {inactive_sites}, "
        #             f"percentage change: {site_change}%, "
        #             f"active users: {alert_users}, "
        #             f"inactive users: {inactive_users}, "
        #             f"percentage change: {user_change}%"
        #         )
        #         email_message += f"<li>{alert.get('message', 'No message')} (severity: {alert.get('severity', 'unknown')})</li>"
            
        #     email_message += "</ul>"

        # # Add followup alerts if any exist
        # if followup_alerts:
        #     sms_message += "\n\nFOLLOW-UP ALERTS:"
        #     email_message += "<h3>Current Alerts:</h3><ul>"
            
        #     for alert in followup_alerts:
        #         sms_message += f"\n- {alert.get('message', 'No message')}"
        #         email_message += f"<li>{alert.get('message', 'No message')} (severity: {alert.get('severity', 'unknown')})</li>"
            
        #     email_message += "</ul>"
        
        try:
            send_sms_alert(sms_message)
            send_email_alert(email_subject, email_message)
        except Exception as e:
            print(f"Failed to send failure notifications: {e}")

# def send_data_generation_notification(num_patients: int, days: int, success: bool = True):
#     """Send notifications about data generation status including activity monitoring alerts"""
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
#     # Get current activity metrics and alerts
#     activity_data = monitor_activity()
#     activity_alerts = activity_data.get("alerts", [])
#     # Get current followup metrics and alerts
#     followup_metrics = followup_activity()
#     alerts = followup_metrics.get("alerts", [])
    
#     if success:
#         # Base success message
#         sms_message = f"Data generation completed at {timestamp}. Generated {num_patients} patients for {days} days."
#         email_subject = "Data Generation Completed"
#         email_message = f"""
#         <p>Data generation process has completed successfully.</p>
#         <p><strong>Details:</strong></p>
#         <ul>
#             <li>Patients generated: {num_patients}</li>
#             <li>Time period: {days} days</li>
#             <li>Completed at: {timestamp}</li>
#         </ul>
#         """
        
#         # Add activity metrics summary
#         email_message += f"""
#         <h3>Site and User Monitoring Data Activity Metrics:</h3>
#         <ul>
#             <li>Active sites: {activity_data['current']['sites']} ({activity_data['sites_percentage_change']}% change)</li>
#             <li>Active users: {activity_data['current']['users']} ({activity_data['users_percentage_change']}% change)</li>
#         </ul>
#         """
        
#         # Add alerts if any exist
#         if activity_alerts:
#             sms_message += "\n\nSITE MONITORING ACTIVITY ALERTS:"
#             email_message += "<h3>Site Monitoring Activity Alerts:</h3><ul>"
            
#             for alert in activity_alerts:
#                 sms_message += f"\n- This mesage is of severity: {alert['severity']} and it says: inactive sites: {alert['sites']}, percentage change: {activity_data['sites_percentage_change']}, inactive users: {alert['users']}, percentage change: {activity_data['users_percentage_change']}"
#                 email_message += f"<li>{alert['message']} (severity: {alert['severity']})</li>"
            
#             email_message += "</ul>"

#         # Add alerts if any exist
#         if alerts:
#             sms_message += "\n\nFOLLOW-UP ALERTS:"
#             email_message += "<h3>Follow-up Current Alerts:</h3><ul>"
            
#             for alert in alerts:
#                 sms_message += f"\n- {alert['message']}"
#                 email_message += f"<li>{alert['message']} (severity: {alert['severity']})</li>"
            
#             email_message += "</ul>"
        
#         try:
#             send_sms_alert(sms_message)
#             send_email_alert(email_subject, email_message)
#         except Exception as e:
#             print(f"Failed to send success notifications: {e}")
#     else:
#         # Failure message (keep original format)
#         sms_message = f"Data generation FAILED at {timestamp}. Check logs."
#         email_subject = "Data Generation Failed"
#         email_message = f"""
#         <p>Data generation process has failed.</p>
#         <p><strong>Time:</strong> {timestamp}</p>
#         <p>Please check the server logs for more details.</p>
#         """
        
#         # Still include activity alerts in failure case
#         if activity_alerts:
#             sms_message += "\n\nSITE MONITORING ACTIVITY ALERTS:"
#             email_message += "<h3> Site Monitoring Activity Alerts:</h3><ul>"
            
#             for alert in activity_alerts:
#                 sms_message += f"\n- This mesage is of severity: {alert['severity']} and it says: active sites: {alert['sites']} out of total sites: {activity_data['total_sites']}, percentage change: {activity_data['sites_percentage_change']}, active users: {alert['users']} out of total users: {activity_data['total_users']}, percentage change: {activity_data['users_percentage_change']}"
#                 email_message += f"<li>{alert['message']} (severity: {alert['severity']})</li>"
            
#             email_message += "</ul>"

#         # Add alerts if any exist
#         if alerts:
#             sms_message += "\n\nFOLLOW-UP ALERTS:"
#             email_message += "<h3>Current Alerts:</h3><ul>"
            
#             for alert in alerts:
#                 sms_message += f"\n- {alert['message']}"
#                 email_message += f"<li>{alert['message']} (severity: {alert['severity']})</li>"
            
#             email_message += "</ul>"
        
#         try:
#             send_sms_alert(sms_message)
#             send_email_alert(email_subject, email_message)
#         except Exception as e:
#             print(f"Failed to send failure notifications: {e}")

def scheduled_data_generation():
    """Function to be called every 5 minutes"""
    from database import SessionLocal
    print(f"\n--- Running scheduled data generation at {datetime.now()} ---")
    db = SessionLocal()  # Create a new database session
    try:
        run_pipeline(
            num_patients=100,  # Smaller batch for frequent updates
            days=30,           # Shorter lookback period
            frequency="5min",
            db=db
        )
        # Send success notification
        send_data_generation_notification(100, 30, success=True)
    except Exception as e:
        print(f"Scheduled job failed: {str(e)}")
        db.rollback()
        # Send failure notification
        send_data_generation_notification(100, 30, success=False)
    finally:
        db.close()
        print("Database session closed")

# Add this to your startup event
@app.on_event("startup")
def startup():
    os.makedirs("data/raw", exist_ok=True)
    print(f"Data will be saved to: {os.path.abspath('data/raw')}")

    init_db()
    print("Database tables created (if not already existing).")
    
    # Schedule the data generation job
    scheduler.add_job(
        scheduled_data_generation,
        trigger=IntervalTrigger(minutes=5),
        id="periodic_data_generation",
        replace_existing=True
    )
    print("Scheduled data generation job added (runs every 5 minutes)")

class SMSRequest(BaseModel):
    recipients: List[str]
    message: str
    sender_id: Optional[str] = "Masterclass"

@app.post("/send-sms")
async def send_sms(request: SMSRequest):
    """
    Send SMS to one or more recipients
    """
    try:
        response = sms_service.send_sms(
            message=request.message,
            recipients=request.recipients,
            sender_id=request.sender_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_pipeline(
    num_patients: int = 100,
    days: int = 30,
    frequency: str = "5min",
    db: Session = None 
):
    """Core data generation pipeline"""
    from database import SessionLocal

    db = db or SessionLocal()  # Use provided session or create a new one
    try:
        print(f"Database session valid: {db.is_active}")
        print(f"Starting data generation for {days} days...")
        
        # Calculate consistent date range for all generated data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 0. Generate sites and users first (since patients need sites)
        sites_df, users_df = generate_site_user_data()
        sites_df.to_csv("data/raw/sites.csv", index=False)
        users_df.to_csv("data/raw/users.csv", index=False)
        
        # 1. Generate patients WITH DATE RANGE
        print(f"Generating {num_patients} patients between {start_date} and {end_date}")
        patients = generate_patients(num_patients, start_date, end_date)
        patients_df = pd.DataFrame(patients)
        columns_to_drop = [
            'has_diabetes', 'on_diabetes_meds',
            'has_mental_health_issue', 'on_mh_treatment',
            'has_hypertension', 'on_htn_meds'
        ]
        patients_df = patients_df.drop(columns=[col for col in columns_to_drop if col in patients_df.columns])
        patients_df.to_csv("data/raw/patients.csv", index=False)

        # 2. Generate screening logs
        screenings = generate_screening_log(patients, days)
        screenings.to_csv("data/raw/screenings.csv", index=False)
        
        # 3. Generate clinical logs
        bp_logs = generate_bp_logs(screenings)
        bp_logs.to_csv("data/raw/bp_logs.csv", index=False)
        
        glucose_logs = generate_glucose_log(screenings)
        glucose_logs.to_csv("data/raw/glucose_logs.csv", index=False)

        visits_df = generate_visits()
        visits_df.to_csv("data/raw/patient_visits.csv", index=False)
    
        compliances = generate_patient_medical_compliances(bp_logs)
        compliances.to_csv("data/raw/compliances.csv", index=False)

        lifestyles = generate_patient_lifestyles(bp_logs)
        lifestyles.to_csv("data/raw/lifestyles.csv", index=False)

        medical_reviews = generate_patient_medical_reviews(bp_logs, visits_per_patient=3)
        medical_reviews.to_csv("data/raw/medical_reviews.csv", index=False)

        diagnoses = generate_patient_diagnoses(patients)
        diagnoses.to_csv("data/raw/diagnoses.csv", index=False)
        
        # 4. Generate continuous metrics
        health_metrics = generate_health_metrics(
            patients,
            start_date=start_date,
            days=days,
            frequency=frequency
        )
        health_metrics.to_csv(f"data/raw/health_metrics_{frequency}.csv", index=False)

        # 5. Run anomaly detection on all generated data
        health_data = {
            'patients': patients,
            'sites': sites_df,
            'users': users_df,
            'screenings': screenings,
            'bp_logs': bp_logs,
            'glucose_logs': glucose_logs,
            'health_metrics': health_metrics,
            'compliances': compliances,
            'lifestyles': lifestyles,
            'medical_reviews': medical_reviews,
            'diagnoses': diagnoses,
            'visits': visits_df
        }
        anomalies = detect_anomalies(health_data)
        anomalies.to_csv("data/raw/anomalies.csv", index=False)
        
        print("Data generation and anomaly detection completed successfully")
        
        # Send success notification
        send_data_generation_notification(num_patients, days, success=True)
        
    except Exception as e:
        print(f"Error in data generation: {str(e)}")
        # Send failure notification
        send_data_generation_notification(num_patients, days, success=False)
        if db:  # Only rollback if we have a session
            db.rollback()
        raise
    finally:
        if db:  # Only close if we have a session
            db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)



