import random
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import uuid
from .patientgenerator import COUNTIES, SUB_COUNTIES

fake = Faker()

def generate_screening_log(patients_df):
    screenings = []
    for _, patient in patients_df.iterrows():
        # Base screening record
        screening_date = fake.date_time_between(start_date="-1y", end_date="now")
        height = round(np.random.normal(170, 10), 1)  # cm
        weight = round(np.random.normal(70, 15), 1)   # kg
        bmi = round(weight / ((height/100) ** 2), 1)
        age = (datetime.now() - datetime.strptime(patient["date_of_birth"], "%Y-%m-%d")).days // 365
        
        # Blood pressure with possible hypertension
        is_hypertensive = random.random() < 0.3
        systolic = round(np.random.normal(120, 15 if not is_hypertensive else 25))
        diastolic = round(np.random.normal(80, 10 if not is_hypertensive else 15))
        
        # Glucose with possible diabetes
        is_diabetic = random.random() < 0.2
        glucose_value = round(np.random.normal(100, 20 if not is_diabetic else 40), 1)
        glucose_type = random.choice(["FBS", "RBS"])
        
        # CVD Risk calculation (simplified)
        cvd_risk_score = max(0, round(
            (age / 10) + 
            (1 if is_hypertensive else 0) * 5 + 
            (1 if is_diabetic else 0) * 3 +
            (1 if patient["is_regular_smoker"] else 0) * 2 +
            np.random.normal(0, 3)
        ))
        cvd_risk_level = "Low" if cvd_risk_score < 10 else "Medium" if cvd_risk_score < 20 else "High"
        
        # PHQ-4 mental health assessment
        phq4_score = random.randint(0, 12)
        phq4_risk_level = "None" if phq4_score < 3 else "Mild" if phq4_score < 6 else "Moderate" if phq4_score < 9 else "Severe"
        
        screening = {
            "screening_id": str(uuid.uuid4()),
            "patient_id": patient["patient_id"],
            "first_name": patient["first_name"],
            "last_name": patient["last_name"],
            "middle_name": patient["middle_name"],
            "gender": patient["gender"],
            "date_of_birth": patient["date_of_birth"],
            "age": age,
            "national_id": patient["national_id"],
            "height": height,
            "weight": weight,
            "bmi": bmi,
            "avg_systolic": systolic,
            "avg_diastolic": diastolic,
            "avg_pulse": round(np.random.normal(75, 10)),
            "glucose_value": glucose_value,
            "glucose_type": glucose_type,
            "glucose_date_time": screening_date.strftime("%Y-%m-%d %H:%M:%S"),
            "last_meal_time": (screening_date - timedelta(hours=random.randint(1, 6))).strftime("%Y-%m-%d %H:%M:%S"),
            "is_before_diabetes_diagnosis": is_diabetic and random.random() < 0.5,
            "is_before_htn_diagnosis": is_hypertensive and random.random() < 0.5,
            "is_regular_smoker": patient["is_regular_smoker"],
            "cvd_risk_score": cvd_risk_score,
            "cvd_risk_level": cvd_risk_level,
            "phq4_score": phq4_score,
            "phq4_risk_level": phq4_risk_level,
            "phq4_mental_health": phq4_risk_level,  # Simplified
            "refer_assessment": cvd_risk_level != "Low" or phq4_risk_level in ["Moderate", "Severe"],
            "country_id": patient["country_id"],
            "country_name": patient["country_name"],
            "county_id": patient["county_id"],
            "county_name": patient["county_name"],
            "sub_county_id": patient["sub_county_id"],
            "sub_county_name": patient["sub_county_name"],
            "site_id": patient["site_id"],
            "site_name": patient["site_name"],
            "landmark": patient["landmark"],
            "latitude": round(random.uniform(-1.0, 1.0) + 37.0, 6),  # Kenya approx
            "longitude": round(random.uniform(-1.0, 1.0) + 36.0, 6),
            "phone_number": patient["phone_number"],
            "phone_number_category": patient["phone_number_category"],
            "type": random.choice(["Inpatient", "Outpatient"]),
            "category": random.choice(["Community", "Facility"]),
            "device_info_id": str(uuid.uuid4()),
            "is_latest": True,  # Assume all are latest for simulation
            "is_active": True,
            "is_deleted": False,
            "tenant_id": patient["tenant_id"],
            "created_by": patient["created_by"],
            "updated_by": patient["updated_by"],
            "created_at": screening_date.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": screening_date.strftime("%Y-%m-%d %H:%M:%S")
        }
        screenings.append(screening)
    
    return pd.DataFrame(screenings)