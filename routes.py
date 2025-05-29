from datetime import datetime
from pathlib import Path
import traceback
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import numpy as np
import pandas as pd
from utils.dataloader import reload_all_data
from database import get_db
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from datetime import datetime, timedelta
from api.auth.signin.auth import router as signin_router  # Import the signin router
from api.auth.register.auth import router as register_router  # Import the register router
# from utils.monitoring import (
#     main,
#     HISTORICAL_DATA_PATH
# )
# from utils.followup import (
#     main,
#     HISTORICAL_METRICS_PATH 
# )
from utils.monitoring import monitor_activity as monitoring_main, HISTORICAL_DATA_PATH
from utils.followup import followup_activity as followup_main
import json  # Add this import if not already present
# from utils.patient_summary import get_patient_summary
from src.generators.patientgenerator import generate_patients, generated_patients

router = APIRouter()

# Include authentication routes under /auth
router.include_router(signin_router, prefix="/auth")
router.include_router(register_router, prefix="/auth")

DIAGNOSES_PATH = Path("data/raw/diagnoses.csv")
BP_LOGS_PATH = Path("data/raw/bp_logs.csv")
GLUCOSE_LOGS_PATH = Path("data/raw/glucose_logs.csv")
PREVIOUS_METRICS_PATH = Path("data/previous_metrics.json")
HISTORICAL_METRICS_PATH = Path("data/historical_metrics.json")
HISTORICAL_DATA_PATH = Path("data/historical_activity.json")


@router.get("/sites")
async def get_sites(limit: int = 100):
    """Get generated site data"""
    try:
        df = pd.read_csv("data/raw/sites.csv")
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Site data not found. Generate data first.")

@router.get("/users")
async def get_users(limit: int = 280):
    """Get generated user data"""
    try:
        df = pd.read_csv("data/raw/users.csv")
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="User data not found. Generate data first.")
    
@router.get("/users/count")
async def get_active_user_count():
    """Get count of active users"""
    try:
        df = pd.read_csv("data/raw/users.csv")
        df['is_active'] = df['is_active'].astype(bool)
        user_count = df.shape[0]
        active_count = df[df['is_active'] == True].shape[0]
        return {"active_user_count": active_count, "total_user_count": user_count}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="User data not found.")

@router.post("/reload-data")
async def reload_data(db: Session = Depends(get_db)):
    try:
        reload_all_data(db)
        return {"message": "Data reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/visits")
async def get_users(limit: int = 1000):
    """Get generated user data"""
    try:
        df = pd.read_csv("data/raw/patient_visits.csv")
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Visits data not found. Generate data first.")
    
@router.get("/check-activity-decline")
async def check_activity_decline():
    """Endpoint to check for activity declines based on historical trends."""
    try:
        monitoring_data = monitoring_main()

        # If main() returned an error dictionary
        if "error" in monitoring_data:
            raise HTTPException(status_code=500, detail=monitoring_data["error"])

        # Load full historical activity records
        historical_data = {}
        if HISTORICAL_DATA_PATH.exists():
            with open(HISTORICAL_DATA_PATH, "r") as f:
                try:
                    historical_data = json.load(f)
                except json.JSONDecodeError:
                    historical_data = {"warning": "Historical data file is corrupted"}

        return {
            "status": "success",
            "data": {
                "current": monitoring_data["current"],
                "previous": monitoring_data["previous"],
                "sites_percentage_change": monitoring_data["sites_percentage_change"],
                "users_percentage_change": monitoring_data["users_percentage_change"],
                "site_activity_declined_5_percent": monitoring_data["site_activity_declined_5_percent"],
                "user_activity_declined_5_percent": monitoring_data["user_activity_declined_5_percent"],
                "last_checked": monitoring_data["last_updated"],
                "historical_data": historical_data
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") 
    
@router.get("/monitoring-metrics", response_class=JSONResponse)
async def get_monitoring_metrics():
    """
    Endpoint to compute and return the latest monitoring metrics,
    compare with previous, and provide full historical metrics and alerts.
    """
    print("\n=== Starting monitoring metrics generation ===")
    print(f"Current time: {datetime.now().isoformat()}")
    
    try:
        # Validate input data files exist
        required_files = [DIAGNOSES_PATH, BP_LOGS_PATH, GLUCOSE_LOGS_PATH]
        print("\nChecking required data files:")
        for file_path in required_files:
            file_exists = file_path.exists()
            print(f"- {file_path.name}: {'Found' if file_exists else 'MISSING'}")
            if not file_exists:
                raise HTTPException(status_code=404, detail=f"{file_path.name} data file not found.")

        # Run the monitoring workflow
        print("\nRunning main monitoring workflow...")
        metrics_data = followup_main()
        # Convert numpy types to native Python types for JSON serialization
        metrics_data = json.loads(
            json.dumps(metrics_data, default=lambda x: bool(x) if isinstance(x, np.bool_) else x)
        )
        print("Main workflow completed with result:", json.dumps(metrics_data, indent=2))

        # Debug: Check structure of returned metrics
        if not metrics_data:
            print("ERROR: Main workflow returned None")
            raise HTTPException(status_code=500, detail="Monitoring workflow returned no data")
            
        if "current_metrics" not in metrics_data:
            print("ERROR: current_metrics key missing in returned data")
            print("Full returned data structure:", type(metrics_data))
            if isinstance(metrics_data, dict):
                print("Keys in returned data:", metrics_data.keys())
            raise HTTPException(status_code=500, detail="'current_metrics' key missing in response")

        # Ensure changes exists even if no comparison was made
        if 'changes' not in metrics_data["current_metrics"]:
            print("No previous metrics found for comparison - initializing empty changes")
            metrics_data["current_metrics"]['changes'] = {
                'new_diagnoses': 0,
                'bp_followup': 0,
                'bg_followup': 0,
                'bp_controlled': 0
            }

        print("\nFinal metrics data structure:")
        print(json.dumps(metrics_data, indent=2))
        
        print("\n=== Monitoring metrics generation completed successfully ===")
        return {
            "status": "success",
            "data": metrics_data
        }
        
    except HTTPException as http_err:
        print(f"\nHTTP Exception occurred: {http_err.detail}")
        raise http_err
        
    except Exception as e:
        print(f"\nERROR in monitoring metrics endpoint: {str(e)}")
        print("Traceback:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate monitoring metrics: {str(e)}")

@router.get("/patients")
async def generate_and_get_patients(
    num_patients: int = 100,  # Default value
    days: int = 30,     # Default value
    background_tasks: BackgroundTasks = None
):
    """
    Generate synthetic patient data and return a preview.
    Saves the data as both a versioned file and a latest file.
    """
    try:
        # Set up date range
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()

        # Generate patient data
        patients_df = generate_patients(num_patients, start_date, end_date)

        # Ensure data directory exists
        data_dir = Path("data/raw")
        data_dir.mkdir(parents=True, exist_ok=True)

        # Save patient data
        # version = datetime.now().strftime("%Y%m%d_%H%M%S")
        # versioned_filename = f"patients_{version}.csv"
        latest_filename = "patients.csv"

        # patients_df.to_csv(data_dir / versioned_filename, index=False)
        patients_df.to_csv(data_dir / latest_filename, index=False)

        # Read and return a limited preview
        df = pd.read_csv(data_dir / latest_filename)

        # Convert NaN/NaT values to None (which becomes null in JSON)
        cleaned_df = df.replace({np.nan: None, pd.NaT: None})
        
        # Return the cleaned data
       # Return all records instead of just the first 5
        return cleaned_df.to_dict(orient="records")
        # return df.head().to_dict(orient="records")

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Patient data not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/medical_reviews")
async def get_patientmedicalreview(limit: int = 100):
    """Get generated patient data"""
    try:
        df = pd.read_csv("data/raw/medical_reviews.csv")
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Patient data not found. Generate data first.")
    
@router.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "Database connection successful"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/compliances")
async def get_compliances(limit: int = 100):
    """Get patient compliance data"""
    try:
        df = pd.read_csv("data/raw/compliances.csv")
        # Convert NaN/NaT values to None (which becomes null in JSON)
        cleaned_df = df.replace({np.nan: None, pd.NaT: None})
        
        # Return the cleaned data
        # Return all records instead of just the first 5
        return cleaned_df.to_dict(orient="records")
        # return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Compliance data not found. Generate data first.")

@router.get("/lifestyles")
async def get_lifestyles(limit: int = 100):
    """Get patient lifestyle data"""
    try:
        df = pd.read_csv("data/raw/lifestyles.csv")
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Lifestyle data not found. Generate data first.")
    
@router.get("/diagnoses")
async def get_patientdiagnosis(limit: int = 100):
    """Get generated patient data"""
    try:
        df = pd.read_csv("data/raw/diagnoses.csv")

        # Convert NaN/NaT values to None (which becomes null in JSON)
        cleaned_df = df.replace({np.nan: None, pd.NaT: None})
        
        # Return the cleaned data
        # Return all records instead of just the first 5
        return cleaned_df.to_dict(orient="records")
        # return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Patient data not found. Generate data first.")

@router.get("/anomalies")
async def get_anomalies(limit: int = 50, severity: str = None):
    """Get detected anomalies with optional severity filter"""
    try:
        df = pd.read_csv("data/raw/anomalies.csv")
        
        if severity:
            severity = severity.upper()
            df = df[df["alert_type"].str.contains(severity)]
            
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Anomaly data not found. Generate data first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/screenings")
async def get_screenings(limit: int = 100):
    """Get screening log data"""
    try:
        df = pd.read_csv("data/raw/screenings.csv")
        # Convert NaN/NaT values to None (which becomes null in JSON)
        cleaned_df = df.replace({np.nan: None, pd.NaT: None})
        
        # Return the cleaned data
        return cleaned_df.to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Screening data not found. Generate data first.")
    
@router.get("/bp-logs")
async def get_bp_logs(patient_id: str = None, limit: int = 100):
    """Get blood pressure logs"""
    try:
        df = pd.read_csv("data/raw/bp_logs.csv")
        if patient_id:
            df = df[df["patient_id"] == patient_id]
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="BP logs not found. Generate data first.")

@router.get("/glucose-logs")
async def get_glucose_logs(patient_id: str = None, limit: int = 100):
    """Get glucose logs"""
    try:
        df = pd.read_csv("data/raw/glucose_logs.csv")
        if patient_id:
            df = df[df["patient_id"] == patient_id]
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Glucose logs not found. Generate data first.")
