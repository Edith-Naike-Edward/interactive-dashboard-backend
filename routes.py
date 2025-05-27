from datetime import datetime
from pathlib import Path
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
from utils.monitoring import (
    load_previous_counts,
    main,
    get_current_active_counts,
    calculate_decline_percentage,
    HISTORICAL_DATA_PATH
)
from utils.followup import (
    load_previous_metrics,
    save_current_metrics,   
    calculate_monitoring_metrics,
    calculate_change_percentage,
    save_historical_metrics,
    load_historical_data,
    HISTORICAL_METRICS_PATH 
)
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

# @router.get("/patient-summary")
# async def patient_summary():
#     """
#     Retrieve aggregate patient statistics
    
#     Returns:
#         JSON response with:
#         - Total Patient Records
#         - New Patients Count
#         - Repeat Patients Count
#     """
#     try:
#         # Generate patient data
#         summary = get_patient_summary()

#         # return {
#         # "summary": summary,
#         # }
#         return JSONResponse(
#             status_code=200,
#             content={
#                 "message": "Patient summary retrieved successfully",
#                 "data": summary
#             }
#         )
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error processing patient data: {str(e)}"
#         )

@router.get("/check-activity-decline")
async def check_activity_decline():
    """
    Endpoint to check for activity decline and return comprehensive activity data.
    
    Returns:
        - Current and previous counts
        - Decline status (5% threshold)
        - Complete historical data
    """
    # 1. Load previous counts first and cache them
    previous_counts = load_previous_counts()
    previous_sites = previous_counts["active_sites"]
    previous_users = previous_counts["active_users"]
    # Use the main function which handles the proper sequence
    site_declined, user_declined = main()
    
    # Load the current state for response
    current_sites, current_users = get_current_active_counts()
    # previous_counts = load_previous_counts()
    
    # Load historical data for response
    historical_data = {}
    if HISTORICAL_DATA_PATH.exists():
        with open(HISTORICAL_DATA_PATH) as f:
            historical_data = json.load(f)

    return {
        "current": {
            "sites": current_sites,
            "users": current_users
        },
        "previous": {
            "sites": previous_sites,
            "users": previous_users
        },
        "percent_declines": {
            "sites": calculate_decline_percentage(previous_sites, current_sites),
            "users": calculate_decline_percentage(previous_users, current_users)
        },
        "historical_data": historical_data,
        "last_checked": datetime.now().isoformat(),
        "site_activity_declined_5_percent": site_declined,
        "user_activity_declined_5_percent": user_declined
    }

@router.get("/monitoring-metrics", response_class=JSONResponse)
async def get_monitoring_metrics():
    """
    Endpoint to check monitoring metrics and return comprehensive data.
    
    Returns:
        - Current and previous metrics
        - Percentage changes
        - Performance status (50% threshold)
        - Complete historical data
    """
    try:
        # Check if files exist
        if not DIAGNOSES_PATH.exists():
            raise HTTPException(status_code=404, detail="Diagnoses data file not found")
        if not BP_LOGS_PATH.exists():
            raise HTTPException(status_code=404, detail="BP logs file not found")
        if not GLUCOSE_LOGS_PATH.exists():
            raise HTTPException(status_code=404, detail="Glucose logs file not found")

        # Ensure data directory exists
        PREVIOUS_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        HISTORICAL_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Load data
        try:
            diagnoses_df = pd.read_csv(DIAGNOSES_PATH)
            bp_logs_df = pd.read_csv(BP_LOGS_PATH)
            glucose_logs_df = pd.read_csv(GLUCOSE_LOGS_PATH)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading CSV files: {str(e)}")
        
        # Calculate current metrics
        current = calculate_monitoring_metrics(diagnoses_df, bp_logs_df, glucose_logs_df)
        
        # Load previous metrics
        previous = load_previous_metrics()
        
        # Save current as new previous
        save_current_metrics(current)
        
        # Update historical data
        save_historical_metrics(previous, current)
        
        # Load historical data for response
        historical_data = load_historical_data()

        response_data = {
            "current": {
                "new_diagnoses": current["percent_new_diagnoses"],
                "bp_followup": current["percent_bp_followup"],
                "bg_followup": current["percent_bg_followup"],
                "bp_controlled": current["percent_bp_controlled"],
                "timestamp": current["timestamp"]
            },
            "previous": {
                "new_diagnoses": previous.get("percent_new_diagnoses", 0),
                "bp_followup": previous.get("percent_bp_followup", 0),
                "bg_followup": previous.get("percent_bg_followup", 0),
                "bp_controlled": previous.get("percent_bp_controlled", 0),
                "timestamp": previous.get("timestamp", "")
            },
            "percent_changes": {
                "new_diagnoses": calculate_change_percentage(
                    previous.get("percent_new_diagnoses", 0), 
                    current["percent_new_diagnoses"]
                ),
                "bp_followup": calculate_change_percentage(
                    previous.get("percent_bp_followup", 0),
                    current["percent_bp_followup"]
                ),
                "bg_followup": calculate_change_percentage(
                    previous.get("percent_bg_followup", 0),
                    current["percent_bg_followup"]
                ),
                "bp_controlled": calculate_change_percentage(
                    previous.get("percent_bp_controlled", 0),
                    current["percent_bp_controlled"]
                ) 
            },
            # "historical_data": historical_data,
            "historical_data": historical_data.get("metrics", []),
            "last_checked": datetime.now().isoformat(),
            "performance_declined": bool(current["performance_declined"]),
            "threshold_violations": {
                "new_diagnoses": bool(current["percent_new_diagnoses"] < 50),
                "bp_followup": bool(current["percent_bp_followup"] < 50),
                "bg_followup": bool(current["percent_bg_followup"] < 50),
                "bp_controlled": bool(current["percent_bp_controlled"] < 50)
            }
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        versioned_filename = f"patients_{version}.csv"
        latest_filename = "patients.csv"

        patients_df.to_csv(data_dir / versioned_filename, index=False)
        patients_df.to_csv(data_dir / latest_filename, index=False)

        # Read and return a limited preview
        df = pd.read_csv(data_dir / latest_filename)

        # Convert NaN/NaT values to None (which becomes null in JSON)
        cleaned_df = df.replace({np.nan: None, pd.NaT: None})
        
        # Return the cleaned data
        return cleaned_df.head().to_dict(orient="records")
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
        return cleaned_df.head().to_dict(orient="records")
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
        return cleaned_df.head().to_dict(orient="records")
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
        return cleaned_df.head().to_dict(orient="records")
        # return df.head(limit).to_dict(orient="records")
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
