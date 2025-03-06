from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from preprocessing import preprocess_health_data
from anomaly_detection import detect_anomalies
from api.auth.register.auth import router as auth_router 
from api.auth.signin.auth import router as signin_router  # Import the signin router
from api.auth.register.auth import router as register_router  # Import the register router
import os
import pandas as pd
from models import HealthData

CSV_FILE_PATH = r"D:\UNI FILES\YEAR 4.2\Interactive Dashboard\Backend\data\Health Screening Data.csv"

# Ensure database tables are created
models.Base.metadata.create_all(bind=engine)

router = APIRouter()

# Include authentication routes under /auth
# router.include_router(auth_router, prefix="/auth")
router.include_router(signin_router, prefix="/auth")
router.include_router(register_router, prefix="/auth")

# Dependency: Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Home route
@router.get("/")
def home():
    return {"message": "Welcome to the Health Dashboard API"}


# User management: Store user data in the database
@router.post("/users/")
def create_user(username: str, email: str, password: str, db: Session = Depends(get_db)):
    """
    Create a new user in the database.
    """
    new_user = models.User(username=username, email=email, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def load_health_screening_data(db: Session):
    """
    Load health screening data from a CSV file into the database.
    """
    # Path to your CSV file
    CSV_FILE_PATH = r"D:\UNI FILES\YEAR 4.2\Interactive Dashboard\Backend\data\Health Screening Data.csv"

    # Check if the CSV file exists
    if not os.path.exists(CSV_FILE_PATH):
        raise FileNotFoundError(f"CSV file not found at {CSV_FILE_PATH}")

    # Read the CSV file into a DataFrame
    df = pd.read_csv(CSV_FILE_PATH)

    # Print the columns of the DataFrame
    print(df.columns)

    # Insert data into the database
    for _, row in df.iterrows():
        health_entry = models.HealthData(
            age=row["age"],
            gender=row["gender"],
            height=row["height"],
            weight=row["weight"],
            ap_hi=row["ap_hi"],
            ap_lo=row["ap_lo"],
            cholesterol=row["cholesterol"],
            gluc=row["gluc"],
            smoke=row["smoke"],
            alco=row["alco"],
            active=row["active"],
            cardio=row["cardio"],
            AgeinYr=row["AgeinYr"],
            BMI=row["BMI"],
            BMICat=row["BMICat"],
            AgeGroup=row["AgeGroup"]
        )
        db.add(health_entry)

    # Commit the changes
    db.commit()
    db.refresh(health_entry)
    return health_entry

@router.post("/load-health-data/")
def load_health_data(db: Session = Depends(get_db)):
    """
    Load health screening data from the CSV file into the database.
    """
    try:
        load_health_screening_data(db)
        return {"message": "Health screening data loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Upload, preprocess, and save health data to the database
@router.post("/upload/")
async def upload_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a CSV file, preprocess it, and store the cleaned data in the database.
    """
    # Save file temporarily
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Preprocess data
    df = preprocess_health_data(file_path)

    # Save processed data to database
    for _, row in df.iterrows():
        new_entry = models.HealthData(
            bmi=row["bmi"],
            glucose_level=row["glucose_level"],
            gender=row["gender"]
        )
        db.add(new_entry)

    db.commit()
    os.remove(file_path)  # Clean up temp file
    return {"message": "Data uploaded and stored successfully!"}


# Retrieve stored health data from the database
@router.get("/health-data/")
def get_health_data(db: Session = Depends(get_db)):
    """
    Retrieve all stored health data from the database.
    """
    health_data = db.query(models.HealthData).all()
    if not health_data:
        raise HTTPException(status_code=404, detail="No data found")
    return health_data

@router.get("/health-screening-data/")
def get_health_screening_data():
    """
    Read the health screening data from the CSV file and return it as JSON.
    """
    # Check if the CSV file exists
    if not os.path.exists(CSV_FILE_PATH):
        raise HTTPException(status_code=404, detail="CSV file not found")

    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(CSV_FILE_PATH)
        # Convert the DataFrame to JSON
        data = df.to_dict(orient="records")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV file: {str(e)}")


# Anomaly detection for glucose levels**
@router.get("/anomalies/")
def get_anomalies(db: Session = Depends(get_db)):
    """
    Fetch glucose level data and detect anomalies.
    """
    health_data = db.query(models.HealthData).all()

    if not health_data:
        raise HTTPException(status_code=404, detail="No data found")

    glucose_values = [entry.glucose_level for entry in health_data]
    anomalies = detect_anomalies(glucose_values)

    return {"anomalies": anomalies} if anomalies else {"message": "No anomalies detected"}

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from database import SessionLocal
# import models
# from anomaly_detection import detect_anomalies

# router = APIRouter()

# # Dependency: Get database session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# @router.get("/anomalies/")
# def get_anomalies(db: Session = Depends(get_db)):
#     """
#     Fetch glucose level data and detect anomalies.
#     """
#     # Query all health data from the database
#     health_data = db.query(models.HealthData).all()

#     # Raise an HTTP 404 error if no data is found
#     if not health_data:
#         raise HTTPException(status_code=404, detail="No data found")

#     # Extract glucose levels from the health data
#     glucose_values = [entry.glucose_level for entry in health_data]
    
#     # Detect anomalies in the glucose levels
#     anomalies = detect_anomalies(glucose_values)

#     # Return a message if no anomalies are detected
#     if not anomalies:
#         return {"message": "No anomalies detected"}

#     # Return the detected anomalies
#     return {"anomalies": anomalies}

# # from fastapi import APIRouter, UploadFile, File, Depends
# # import pandas as pd
# # from sqlalchemy.orm import Session
# # from database import SessionLocal
# # from preprocessing import preprocess_health_data
# # import models

# # router = APIRouter()

# # # Dependency: Get database session
# # def get_db():
# #     db = SessionLocal()
# #     try:
# #         yield db
# #     finally:
# #         db.close()

# # @router.post("/upload/")
# # async def upload_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
# #     """
# #     Upload and preprocess a CSV file, then store it in the database.
# #     """
# #     contents = await file.read()
    
# #     # Save file temporarily
# #     file_path = f"temp_{file.filename}"
# #     with open(file_path, "wb") as f:
# #         f.write(contents)
    
# #     # Preprocess data
# #     df = preprocess_health_data(file_path)
    
# #     # Save to database
# #     for _, row in df.iterrows():
# #         new_entry = models.HealthData(
# #             bmi=row["bmi"],
# #             glucose_level=row["glucose_level"],
# #             gender=row["gender"]
# #         )
# #         db.add(new_entry)

# #     db.commit()
# #     return {"message": "Data uploaded and stored successfully!"}

# # # from fastapi import APIRouter, Depends
# # # from sqlalchemy.orm import Session
# # # from database import SessionLocal, engine
# # # import models

# # # models.Base.metadata.create_all(bind=engine)  # Create tables if they don't exist

# # # router = APIRouter()

# # # def get_db():
# # #     db = SessionLocal()
# # #     try:
# # #         yield db
# # #     finally:
# # #         db.close()

# # # @router.get("/")
# # # def home():
# # #     return {"message": "Welcome to the Health Dashboard API"}

# # # @router.post("/users/")
# # # def create_user(username: str, email: str, password: str, db: Session = Depends(get_db)):
# # #     new_user = models.User(username=username, email=email, password=password)
# # #     db.add(new_user)
# # #     db.commit()
# # #     db.refresh(new_user)
# # #     return new_user

# # # @router.get("/health-data/")
# # # def get_health_data(db: Session = Depends(get_db)):
# # #     return db.query(models.HealthData).all()
