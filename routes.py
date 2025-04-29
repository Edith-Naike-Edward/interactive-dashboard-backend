from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
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
    save_current_counts,
    get_current_active_counts,
    detect_5_percent_drop
)
# from utils.patient_summary import get_patient_summary
from src.generators.patientgenerator import generate_patients, generated_patients

router = APIRouter()

# Include authentication routes under /auth
router.include_router(signin_router, prefix="/auth")
router.include_router(register_router, prefix="/auth")

@router.get("/sites")
async def get_sites(limit: int = 100):
    """Get generated site data"""
    try:
        df = pd.read_csv("data/raw/sites.csv")
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Site data not found. Generate data first.")

@router.get("/users")
async def get_users(limit: int = 240):
    """Get generated user data"""
    try:
        df = pd.read_csv("data/raw/users.csv")
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="User data not found. Generate data first.")
    
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
    previous_counts = load_previous_counts()
    current_sites, current_users = get_current_active_counts()

    site_declined = detect_5_percent_drop(previous_counts["active_sites"], current_sites)
    user_declined = detect_5_percent_drop(previous_counts["active_users"], current_users)

    # Save new counts
    save_current_counts(current_sites, current_users)

    return {
        "active_sites": current_sites,
        "active_users": current_users,
        "site_activity_declined_5_percent": site_declined,
        "user_activity_declined_5_percent": user_declined
    }

@router.get("/patients")
async def generate_and_get_patients(
    num_patients: int,
    days: int,
    # limit: int = 10,  # added a limit parameter
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
        return df.head().to_dict(orient="records")

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

@router.get("/compliances")
async def get_compliances(limit: int = 100):
    """Get patient compliance data"""
    try:
        df = pd.read_csv("data/raw/compliances.csv")
        return df.head(limit).to_dict(orient="records")
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
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Patient data not found. Generate data first.")

# @router.get("/anomalies")
# async def get_anomalies(limit: int = 50):
#     """Get detected anomalies"""
#     try:
#         # This would come from your anomaly detection system
#         health_df = pd.read_csv(f"data/raw/health_metrics_hourly.csv")
#         anomalies = health_df[
#             (health_df["glucose"] > 180) | 
#             (health_df["blood_pressure_systolic"] > 140)
#         ]
#         return anomalies.head(limit).to_dict(orient="records")
#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail="Health metrics not found. Generate data first.")
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
        return df.head(limit).to_dict(orient="records")
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
