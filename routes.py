from fastapi import APIRouter, HTTPException
import pandas as pd
import os
from api.auth.register.auth import router as auth_router 
from api.auth.signin.auth import router as signin_router  # Import the signin router
from api.auth.register.auth import router as register_router  # Import the register router

# # Ensure database tables are created
# models.Base.metadata.create_all(bind=engine)

router = APIRouter()

# Include authentication routes under /auth
# router.include_router(auth_router, prefix="/auth")
router.include_router(signin_router, prefix="/auth")
router.include_router(register_router, prefix="/auth")

# # Dependency: Get database session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

@router.get("/patients")
async def get_patients(limit: int = 100):
    """Get generated patient data"""
    try:
        df = pd.read_csv("data/raw/patients.csv")
        return df.head(limit).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Patient data not found. Generate data first.")
    
@router.get("/patientmedicalreview")
async def get_patientmedicalreview(limit: int = 100):
    """Get generated patient data"""
    try:
        df = pd.read_csv("data/raw/patientmedicalreview.csv")
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
    
@router.get("/patientdiagnosis")
async def get_patientdiagnosis(limit: int = 100):
    """Get generated patient data"""
    try:
        df = pd.read_csv("data/raw/patientdiagnosis.csv")
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
# from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
# from sqlalchemy.orm import Session
# from database import SessionLocal, engine
# import models
# from preprocessing import preprocess_health_data
# from anomaly_detection import detect_anomalies
# from api.auth.register.auth import router as auth_router 
# from api.auth.signin.auth import router as signin_router  # Import the signin router
# from api.auth.register.auth import router as register_router  # Import the register router
# import os
# import pandas as pd
# from models import HealthData

# # CSV_FILE_PATH = r"D:\UNI FILES\YEAR 4.2\Interactive Dashboard\Backend\data\Health Screening Data.csv"

# # Ensure database tables are created
# models.Base.metadata.create_all(bind=engine)

# router = APIRouter()

# # Include authentication routes under /auth
# # router.include_router(auth_router, prefix="/auth")
# router.include_router(signin_router, prefix="/auth")
# router.include_router(register_router, prefix="/auth")

# # Dependency: Get database session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# # Home route
# @router.get("/")
# def home():
#     return {"message": "Welcome to the Health Dashboard API"}


# # User management: Store user data in the database
# @router.post("/users/")
# def create_user(username: str, email: str, password: str, db: Session = Depends(get_db)):
#     """
#     Create a new user in the database.
#     """
#     new_user = models.User(username=username, email=email, password=password)
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return new_user

# # # Upload, preprocess, and save health data to the database
# # @router.post("/upload/")
# # async def upload_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
# #     """
# #     Upload a CSV file, preprocess it, and store the cleaned data in the database.
# #     """
# #     # Save file temporarily
# #     file_path = f"temp_{file.filename}"
# #     with open(file_path, "wb") as f:
# #         f.write(await file.read())

# #     # Preprocess data
# #     df = preprocess_health_data(file_path)

# #     # Save processed data to database
# #     for _, row in df.iterrows():
# #         new_entry = models.HealthData(
# #             bmi=row["bmi"],
# #             glucose_level=row["glucose_level"],
# #             gender=row["gender"]
# #         )
# #         db.add(new_entry)

# #     db.commit()
# #     os.remove(file_path)  # Clean up temp file
# #     return {"message": "Data uploaded and stored successfully!"}


# # # # Retrieve stored health data from the database
# # # @router.get("/health-data/")
# # # def get_health_data(db: Session = Depends(get_db)):
# # #     """
# # #     Retrieve all stored health data from the database.
# # #     """
# # #     health_data = db.query(models.HealthData).all()
# # #     if not health_data:
# # #         raise HTTPException(status_code=404, detail="No data found")
# # #     return health_data

# # @router.get("/health-screening-data/")
# # def get_health_screening_data():
# #     """
# #     Read the health screening data from the CSV file and return it as JSON.
# #     """
# #     # Check if the CSV file exists
# #     if not os.path.exists(CSV_FILE_PATH):
# #         raise HTTPException(status_code=404, detail="CSV file not found")

# #     try:
# #         # Read the CSV file into a DataFrame
# #         df = pd.read_csv(CSV_FILE_PATH)
# #         # Convert the DataFrame to JSON
# #         data = df.to_dict(orient="records")
# #         return data
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=f"Error reading CSV file: {str(e)}")


# # # # Anomaly detection for glucose levels**
# # # @router.get("/anomalies/")
# # # def get_anomalies(db: Session = Depends(get_db)):
# # #     """
# # #     Fetch glucose level data and detect anomalies.
# # #     """
# # #     health_data = db.query(models.HealthData).all()

# # #     if not health_data:
# # #         raise HTTPException(status_code=404, detail="No data found")

# # #     glucose_values = [entry.glucose_level for entry in health_data]
# # #     anomalies = detect_anomalies(glucose_values)

# # #     return {"anomalies": anomalies} if anomalies else {"message": "No anomalies detected"}

# # # def load_health_screening_data(db: Session):
# # #     """
# # #     Load health screening data from a CSV file into the database.
# # #     """
# # #     # Path to your CSV file
# # #     CSV_FILE_PATH = r"D:\UNI FILES\YEAR 4.2\Interactive Dashboard\Backend\data\Health Screening Data.csv"

# # #     # Check if the CSV file exists
# # #     if not os.path.exists(CSV_FILE_PATH):
# # #         raise FileNotFoundError(f"CSV file not found at {CSV_FILE_PATH}")

# # #     # Read the CSV file into a DataFrame
# # #     df = pd.read_csv(CSV_FILE_PATH)

# # #     # Print the columns of the DataFrame
# # #     print(df.columns)

# # #     # Insert data into the database
# # #     for _, row in df.iterrows():
# # #         health_entry = models.HealthData(
# # #             age=row["age"],
# # #             gender=row["gender"],
# # #             height=row["height"],
# # #             weight=row["weight"],
# # #             ap_hi=row["ap_hi"],
# # #             ap_lo=row["ap_lo"],
# # #             cholesterol=row["cholesterol"],
# # #             gluc=row["gluc"],
# # #             smoke=row["smoke"],
# # #             alco=row["alco"],
# # #             active=row["active"],
# # #             cardio=row["cardio"],
# # #             AgeinYr=row["AgeinYr"],
# # #             BMI=row["BMI"],
# # #             BMICat=row["BMICat"],
# # #             AgeGroup=row["AgeGroup"]
# # #         )
# # #         db.add(health_entry)

# # #     # Commit the changes
# # #     db.commit()
# # #     db.refresh(health_entry)
# # #     return health_entry

# # # @router.post("/load-health-data/")
# # # def load_health_data(db: Session = Depends(get_db)):
# # #     """
# # #     Load health screening data from the CSV file into the database.
# # #     """
# # #     try:
# # #         load_health_screening_data(db)
# # #         return {"message": "Health screening data loaded successfully"}
# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=str(e))
