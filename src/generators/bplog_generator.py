import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
from faker import Faker
from models import BPLog
from database import SessionLocal

fake = Faker()

def generate_bp_log(screenings_df):
    """Generate BP log data from screening data"""
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
                "created_at": reading_time,  # Keep as datetime object
                "updated_at": reading_time   # Keep as datetime object
            }
            bp_logs.append(bp_log)
    
    # return bp_logs  # FIX: Return the bp_logs list
    return pd.DataFrame(bp_logs) 

def save_bp_logs_to_db(bp_logs_data):
    """Save generated blood pressure logs to database"""
    db = SessionLocal()
    try:
        # First validate input type
        if not isinstance(bp_logs_data, (list, pd.DataFrame)):
            raise ValueError("bp_logs_data must be a list or DataFrame")
            
        # If DataFrame, convert to list of dicts
        if isinstance(bp_logs_data, pd.DataFrame):
            bp_logs_data = bp_logs_data.to_dict('records')
            
        bp_objects = []
        for log_data in bp_logs_data:
            if not isinstance(log_data, dict):
                raise ValueError(f"Expected dict, got {type(log_data)}: {log_data}")
                
            converted_data = {}
            for key, value in log_data.items():
                # Handle numpy types
                if hasattr(value, 'item'):
                    converted_data[key] = value.item()
                # Handle pandas Timestamps
                elif isinstance(value, pd.Timestamp):
                    converted_data[key] = value.to_pydatetime()
                # Handle datetime strings
                elif isinstance(value, str) and key.endswith(('_at', '_time')):
                    try:
                        converted_data[key] = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        converted_data[key] = value  # Keep original if parsing fails
                else:
                    converted_data[key] = value

            bp_objects.append(BPLog(**converted_data))
        
        db.bulk_save_objects(bp_objects)
        db.commit()
        print(f"Successfully saved {len(bp_objects)} BP logs to database")
        
    except Exception as e:
        db.rollback()
        print(f"Error saving BP logs: {str(e)}")
        # Print sample data for debugging
        if bp_logs_data and len(bp_logs_data) > 0:
            print("First problematic record:", bp_logs_data[0])
        raise
    finally:
        db.close()

def generate_bp_logs(screenings_df):
    """Generate blood pressure logs based on screening data"""
    print(f"Generating BP logs from {len(screenings_df)} screenings...")
    
    # Generate the BP log DataFrame
    bp_logs_df = generate_bp_log(screenings_df)
    print(f"Generated {len(bp_logs_df)} BP log records")
    
    # Convert to list of dictionaries properly
    bp_logs_list = bp_logs_df.to_dict('records')
    
    # Save to database
    save_bp_logs_to_db(bp_logs_list)
    
    return bp_logs_df