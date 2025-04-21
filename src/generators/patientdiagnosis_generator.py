import pandas as pd
import random
import uuid
from faker import Faker

fake = Faker()

# Diagnosis types and classifications
DIABETES_TYPES = ["Type 1", "Type 2", "Gestational", "Prediabetes", "Other"]
DIABETES_PATIENT_TYPES = ["Newly diagnosed", "Known diabetic", "Unknown status"]
DIABETES_CONTROL_TYPES = ["Well controlled", "Moderately controlled", "Poorly controlled", "Unknown"]
HTN_PATIENT_TYPES = ["Newly diagnosed", "Known hypertensive", "Unknown status"]

def generate_diagnosis_record(bp_log):
    """Generate diagnosis record for a given bp_log"""

    created_at = fake.date_time_between(start_date="-5y", end_date="now")
    updated_at = fake.date_time_between(start_date=created_at, end_date="now")

    # Derive age from bp_log if present, else use random
    age = bp_log.get('age', random.randint(20, 80))

    # Diagnosis probabilities based on age
    has_diabetes = random.random() < (0.05 + (age / 1000))  # ~5–13%
    has_hypertension = random.random() < (0.15 + (age / 500))  # ~15–35%

    # Diabetes
    diabetes_year = random.randint(created_at.year - 10, created_at.year) if has_diabetes else None
    diabetes_type = random.choice(DIABETES_TYPES) if has_diabetes else None
    diabetes_patient_type = random.choice(DIABETES_PATIENT_TYPES) if has_diabetes else "Unknown status"
    diabetes_control = random.choice(DIABETES_CONTROL_TYPES) if has_diabetes else None

    # Hypertension
    htn_year = random.randint(created_at.year - 10, created_at.year) if has_hypertension else None
    htn_patient_type = random.choice(HTN_PATIENT_TYPES) if has_hypertension else "Unknown status"

    return {
        "patient_diagnosis_id": str(uuid.uuid4()),
        "patient_track_id": bp_log['patient_track_id'],
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
        "tenant_id": bp_log['tenant_id'],
        "created_by": bp_log['created_by'],
        "updated_by": bp_log['updated_by'],
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_patient_diagnoses_from_bplogs(bp_logs_df):
    """Generate diagnosis records based on bp_log records"""

    diagnoses = []
    for _, bp_log in bp_logs_df.iterrows():
        # 1–2 diagnosis records per bp_log
        num_records = random.choices([1, 2], weights=[0.85, 0.15])[0]
        for _ in range(num_records):
            diagnosis = generate_diagnosis_record(bp_log)
            diagnoses.append(diagnosis)

    return pd.DataFrame(diagnoses)


# Example usage:
# bp_logs_df = generate_bp_log(screening_df)
# diagnoses_df = generate_patient_diagnoses_from_bplogs(bp_logs_df)
# print(diagnoses_df.head())