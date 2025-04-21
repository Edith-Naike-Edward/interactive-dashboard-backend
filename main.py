from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from routes import router
import pandas as pd
from src.generators.patientgenerator import generate_patients
from src.generators.screeninglog_generator import generate_screening_log
from src.generators.bplog_generator import generate_bp_log
from src.generators.glucoselog_generator import generate_glucose_log
from src.generators.patientmedicalcompliance_generator import generate_patient_medical_compliances
from src.generators.patientlifestyle_generator import generate_patient_lifestyles
from src.generators.health_metrics_generator import generate_health_metrics
from src.analytics.anomaly_detector import detect_anomalies
import os
from typing import Optional
import os
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
    return {"message": "Data generation started in background"}

def run_pipeline(
    num_patients: int = 100,
    days: int = 30,
    frequency: str = "hourly"
):
    """Core data generation pipeline"""
    try:
        print("Starting data generation...")
        
        # 1. Generate patients
        patients = generate_patients(num_patients)
        patients.to_csv("data/raw/patients.csv", index=False)
        
        # 2. Generate screening logs
        screenings = generate_screening_log(patients)
        screenings.to_csv("data/raw/screenings.csv", index=False)
        
        # 3. Generate clinical logs
        bp_logs = generate_bp_log(screenings)
        bp_logs.to_csv("data/raw/bp_logs.csv", index=False)
        
        glucose_logs = generate_glucose_log(screenings)
        glucose_logs.to_csv("data/raw/glucose_logs.csv", index=False)

        compliances = generate_patient_medical_compliances(bp_logs)
        compliances.to_csv("data/raw/compliances.csv", index=False)

        lifestyles = generate_patient_lifestyles(bp_logs)
        lifestyles.to_csv("data/raw/lifestyles.csv", index=False)
        
        # 4. Generate continuous metrics
        health_metrics = generate_health_metrics(
            patients,
            start_date=datetime.now() - timedelta(days=days),
            days=days,
            frequency=frequency
        )
        health_metrics.to_csv(f"data/raw/health_metrics_{frequency}.csv", index=False)

        # 5. Run anomaly detection on all generated data
        health_data = {
            'screenings': screenings,
            'bp_logs': bp_logs,
            'glucose_logs': glucose_logs,
            'health_metrics': health_metrics,
            'compliances': compliances,
            'lifestyles': lifestyles
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
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from routes import router

# app = FastAPI()

# # Enable CORS to allow frontend requests
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],  # Allow Next.js frontend
#     allow_credentials=True,
#     allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
#     allow_headers=["*"],  # Allow all headers
# )

# # Include API routes
# app.include_router(router, prefix="/api")

# @app.get("/")
# def read_root():
#     return {"message": "Welcome to the Interactive Health Dashboard API"}

# @app.get("/ping")
# def ping():
#     return {"message": "API is running"}

