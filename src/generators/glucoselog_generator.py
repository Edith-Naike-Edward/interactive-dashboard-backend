import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
from faker import Faker

fake = Faker()

def generate_glucose_log(screenings_df):
    glucose_logs = []
    for _, screening in screenings_df.iterrows():
        track_id = str(uuid.uuid4()) # Simulated track ID
        # Generate 1-2 glucose readings per screening
        for reading_num in range(random.randint(1, 2)):
            # reading_time = datetime.strptime(screening["created_at"], "%Y-%m-%d %H:%M:%S") + timedelta(minutes=reading_num*30)
            screening_created_at = pd.to_datetime(screening["created_at"])
            reading_time = fake.date_time_between(start_date=screening_created_at, end_date=datetime.now())

            # Calculate glucose value (single float instead of array)
            glucose_value = round(float(np.random.normal(screening["glucose_value"], 5)), 1)
            
            # Calculate hba1c value (single float instead of array)
            hba1c_value = 5.5 + (screening["glucose_value"]-100)/50  # Base value
            hba1c = round(float(np.random.normal(hba1c_value, 0.5)), 1)
            
            glucose_log = {
                "glucose_log_id": str(uuid.uuid4()),
                "patient_id": screening["patient_id"],
                "patient_track_id": track_id,  # Simulated track ID
                "glucose_value": glucose_value,
                "glucose_type": screening["glucose_type"],
                "hba1c": hba1c,  # Rough conversion
                "type": screening["type"],
                "is_latest": reading_num == 0,  # First reading is latest
                "is_active": True,
                "is_deleted": False,
                "tenant_id": screening["tenant_id"],
                "glucose_date_time": reading_time.strftime("%Y-%m-%d %H:%M:%S"),
                "last_meal_time": screening["last_meal_time"],
                "created_by": screening["created_by"],
                "updated_by": screening["updated_by"],
                "created_at": reading_time.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": reading_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            glucose_logs.append(glucose_log)
    
    return pd.DataFrame(glucose_logs)