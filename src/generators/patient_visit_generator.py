import pandas as pd
from faker import Faker
import random
import uuid
import os
from datetime import datetime, timedelta

fake = Faker()

def generate_patient_visits(num_visits, patient_ids, user_ids, patient):
    """Generate patient visit records"""
    visits = []
    
    for _ in range(num_visits):
        # Determine visit type
        visit_type = random.choices(
            ['prescription', 'investigation', 'medical_review', 'mixed'],
            weights=[0.4, 0.3, 0.2, 0.1]
        )[0]
        
        is_prescription = visit_type in ['prescription', 'mixed']
        is_investigation = visit_type in ['investigation', 'mixed']
        is_medical_review = visit_type in ['medical_review', 'mixed']
        
        treatment_options = {
            'prescription': [
                "Prescribed medication for condition",
                "Refilled existing prescriptions",
                "Adjusted medication dosage"
            ],
            'investigation': [
                "Ordered lab tests",
                "Referred for imaging",
                "Recommended diagnostic procedures"
            ],
            'medical_review': [
                "Follow-up assessment",
                "Chronic condition management",
                "Progress evaluation"
            ],
            'mixed': [
                "Comprehensive treatment plan",
                "Multi-disciplinary approach",
                "Integrated care plan"
            ]
        }
        
        patient_treatment_plan = random.choice(treatment_options[visit_type])
        
        # Generate timestamps
        patient_created_at = pd.to_datetime(patient["created_at"])
        visit_date = fake.date_time_between(start_date=patient_created_at, end_date=datetime.now())
        created_at = visit_date + timedelta(minutes=random.randint(5, 60))
        updated_at = created_at + timedelta(days=random.randint(0, 30))
        
        visits.append({
            "is_prescription": is_prescription,
            "is_investigation": is_investigation,
            "patient_visit_id": str(uuid.uuid4()),
            "is_medical_review": is_medical_review,
            "patient_treatment_plan": patient_treatment_plan,
            "patient_track_id": str(uuid.uuid4()),
            "is_active": random.choices([True, False], weights=[0.9, 0.1])[0],
            "is_deleted": random.choices([True, False], weights=[0.05, 0.95])[0],
            "tenant_id": str(uuid.uuid4()),
            "created_by": random.choice(user_ids),
            "updated_by": random.choice(user_ids),
            "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "visit_date": visit_date.strftime("%Y-%m-%d %H:%M:%S"),
            "patient_id": patient['patient_id']  # Use the specific patient's ID
        })
    
    return pd.DataFrame(visits)

def generate_visits():
    try:
        patient_df = pd.read_csv("data/raw/patients.csv")
        user_df = pd.read_csv("data/raw/users.csv")
        
        patient_ids = patient_df['patient_id'].tolist()
        user_ids = user_df['id'].tolist()
        
        visits_dfs = []
        for _, patient in patient_df.iterrows():
            num_visits = random.randint(1, 5)
            visits_df = generate_patient_visits(num_visits, patient_ids, user_ids, patient)
            visits_dfs.append(visits_df)
        
        all_visits = pd.concat(visits_dfs, ignore_index=True)
        
        # Ensure directory exists
        os.makedirs("data/raw", exist_ok=True)
        
        # Save to CSV
        all_visits.to_csv("data/raw/patient_visits.csv", index=False)
        return all_visits
        
    except Exception as e:
        print(f"Error generating visits: {str(e)}")
        return None
