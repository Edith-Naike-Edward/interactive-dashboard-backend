from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from routes import router
import pandas as pd
from src.generators.patientgenerator import generate_patients, _assign_health_conditions_wrapper
from src.generators.screeninglog_generator import generate_screening_log
from src.generators.bplog_generator import generate_bp_log
from src.generators.glucoselog_generator import generate_glucose_log
from src.generators.patientmedicalcompliance_generator import generate_patient_medical_compliances
from src.generators.patientlifestyle_generator import generate_patient_lifestyles
from src.generators.patientmedicalreview_generator import generate_patient_medical_reviews
from src.generators.patientdiagnosis_generator import generate_patient_diagnoses
from src.generators.health_metrics_generator import generate_health_metrics
from src.analytics.anomaly_detector import detect_anomalies
from src.generators.site_user_generation import generate_site_user_data, add_is_active_sites, add_is_active_users
from src.generators.patient_visit_generator import generate_visits
import os
from typing import Optional
import os
import uuid
from fastapi import FastAPI

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# THIS IS THE FIX - Creates the folder automatically when starting
@app.on_event("startup")
def startup():
    os.makedirs("data/raw", exist_ok=True)  # Creates folder if missing
    print(f"Data will be saved to: {os.path.abspath('data/raw')}")

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
    frequency: Optional[str] = "hourly"
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

def run_pipeline(
    num_patients: int = 100,
    days: int = 30,
    frequency: str = "hourly"
):
    """Core data generation pipeline"""
    try:
        print(f"Starting data generation for {days} days...")
        
        # Calculate consistent date range for all generated data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 0. Generate sites and users first (since patients need sites)
        sites_df, users_df = generate_site_user_data()
        # sites_df = add_is_active_sites(sites_df)
        sites_df.to_csv("data/raw/sites.csv", index=False)
        # users_df = add_is_active_users(users_df)
        users_df.to_csv("data/raw/users.csv", index=False)
        
        # 1. Generate patients WITH DATE RANGE
        print(f"Generating {num_patients} patients between {start_date} and {end_date}")
        patients = generate_patients(num_patients, start_date, end_date)
        patients_df = pd.DataFrame(patients)
        # patients_df = patients_df.apply(_assign_health_conditions_wrapper, axis=1)
        columns_to_drop = [
            'has_diabetes', 'on_diabetes_meds',
            'has_mental_health_issue', 'on_mh_treatment',
            'has_hypertension', 'on_htn_meds'
        ]
        patients_df = patients_df.drop(columns=[col for col in columns_to_drop if col in patients_df.columns])
        patients_df.to_csv("data/raw/patients.csv", index=False)


        # 2. Generate screening logs
        # screenings = generate_screening_log(patients)
        screenings = generate_screening_log(patients, days)
        screenings.to_csv("data/raw/screenings.csv", index=False)
        
        # 3. Generate clinical logs
        bp_logs = generate_bp_log(screenings)
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
        
        # print("Data generation completed successfully")
    except Exception as e:
        print(f"Error in data generation: {str(e)}")
        raise e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


