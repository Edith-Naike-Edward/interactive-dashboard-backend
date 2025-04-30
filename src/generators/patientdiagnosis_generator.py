from datetime import datetime
import pandas as pd
import random
import uuid
from faker import Faker
# from patientgenerator import created_by, updated_by
from .patientgenerator import get_created_and_updated_by

fake = Faker()

# Diagnosis types and classifications
DIABETES_TYPES = ["Type 1", "Type 2", "Gestational", "Prediabetes", "Other"]
DIABETES_PATIENT_TYPES = ["Newly diagnosed", "Known diabetic", "Unknown status"]
DIABETES_CONTROL_TYPES = ["Well controlled", "Moderately controlled", "Poorly controlled", "Unknown"]
HTN_PATIENT_TYPES = ["Newly diagnosed", "Known hypertensive", "Unknown status"]

def generate_diagnosis_record(patient):
    """Generate diagnosis record for a given patient"""
    # site_id = patient['site_id']
    # created_by, updated_by = get_created_and_updated_by(site_id)
    created_by = patient['created_by']
    updated_by = patient['updated_by']

    patient_created_at = pd.to_datetime(patient["created_at"])
    diagnosis_time = fake.date_time_between(start_date=patient_created_at, end_date=datetime.now())

    # Derive age from patient if present, else use random
    age = patient.get('age', random.randint(20, 80))

    # Diagnosis probabilities based on age
    has_diabetes = random.random() < (0.05 + (age / 1000))  # ~5–13%
    has_hypertension = random.random() < (0.15 + (age / 500))  # ~15–35%

    # Diabetes
    diabetes_year = random.randint(patient_created_at.year - 10, patient_created_at.year) if has_diabetes else None
    diabetes_type = random.choice(DIABETES_TYPES) if has_diabetes else None
    diabetes_patient_type = random.choice(DIABETES_PATIENT_TYPES) if has_diabetes else "Unknown status"
    diabetes_control = random.choice(DIABETES_CONTROL_TYPES) if has_diabetes else None

    # Hypertension
    htn_year = random.randint(patient_created_at.year - 10, patient_created_at.year) if has_hypertension else None
    htn_patient_type = random.choice(HTN_PATIENT_TYPES) if has_hypertension else "Unknown status"

    return {
        "patient_diagnosis_id": str(uuid.uuid4()),
        "patient_track_id": str(uuid.uuid4()),
        "diabetes_year_of_diagnosis": diabetes_year,
        "diabetes_patient_type": diabetes_patient_type,
        "htn_patient_type": htn_patient_type,
        "diabetes_diagnosis": diabetes_type,
        "htn_year_of_diagnosis": htn_year,
        "is_diabetes_diagnosis": has_diabetes,
        "is_htn_diagnosis": has_hypertension,
        "diabetes_diag_controlled_type": diabetes_control,
        "is_active": random.choices([True, False], weights=[0.9, 0.1])[0],
        "is_deleted": False,
        "tenant_id": patient['tenant_id'],
        "created_by": created_by,
        "updated_by": updated_by,
        "created_at": diagnosis_time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": diagnosis_time.strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_patient_diagnoses(patients):
    """Generate diagnosis records based on patient records"""

    diagnoses = []
    for _, patient in patients.iterrows():
        # 1–2 diagnosis records per bp_log
        num_records = random.choices([1, 2], weights=[0.85, 0.15])[0]
        for _ in range(num_records):
            diagnosis = generate_diagnosis_record(patient)
            diagnoses.append(diagnosis)

    return pd.DataFrame(diagnoses)


# Example usage:
# bp_logs_df = generate_bp_log(screening_df)
# diagnoses_df = generate_patient_diagnoses_from_bplogs(bp_logs_df)
# print(diagnoses_df.head())