import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
from faker import Faker

fake = Faker()

def generate_bp_log(screenings_df):
    bp_logs = []
    for _, screening in screenings_df.iterrows():
        track_id = str(uuid.uuid4()) # Simulated track ID
        # Generate 1-3 BP readings per screening
        for reading_num in range(random.randint(1, 3)):
            patient_created_at = pd.to_datetime(screening["created_at"])
            reading_time = fake.date_time_between(start_date=patient_created_at, end_date=datetime.now())
            
            # BP values based on screening averages with some variation
            systolic = round(np.random.normal(screening["avg_systolic"], 5))
            diastolic = round(np.random.normal(screening["avg_diastolic"], 3))
            pulse = round(np.random.normal(screening["avg_pulse"], 2))
            
            bp_log = {
                "bplog_id": str(uuid.uuid4()),
                "patient_id": screening["patient_id"],
                "patient_track_id": track_id,  # Simulated track ID
                "avg_systolic": systolic,
                "avg_diastolic": diastolic,
                "avg_pulse": pulse,
                "height": screening["height"],
                "weight": screening["weight"],
                "bmi": screening["bmi"],
                "temperature": round(np.random.normal(36.5, 0.5), 1),
                "is_regular_smoker": screening["is_regular_smoker"],
                "cvd_risk_score": screening["cvd_risk_score"],
                "cvd_risk_level": screening["cvd_risk_level"],
                "risk_level": screening["cvd_risk_level"],  # Simplified
                "type": screening["type"],
                "is_latest": reading_num == 0,  # First reading is latest
                "is_active": True,
                "is_deleted": False,
                "tenant_id": screening["tenant_id"],
                "created_by": screening["created_by"],
                "updated_by": screening["updated_by"],
                "created_at": reading_time.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": reading_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            bp_logs.append(bp_log)
    
    return pd.DataFrame(bp_logs)