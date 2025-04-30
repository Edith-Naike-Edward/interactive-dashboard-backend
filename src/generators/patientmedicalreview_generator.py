import pandas as pd
import random
from datetime import datetime, timedelta
import uuid
from faker import Faker
import numpy as np

fake = Faker()

# Common medical phrases for different sections
CLINICAL_NOTES = [
    "Patient presents with stable condition and reports good medication adherence.",
    "Mild symptoms reported but overall condition well-managed.",
    "Symptoms worsening, considering medication adjustment.",
    "New symptoms reported, requires further investigation.",
    "Excellent response to current treatment regimen.",
    "Patient experiencing side effects from current medications.",
    "Condition stable but lifestyle modifications needed.",
    "Acute exacerbation noted, immediate intervention required.",
    "Follow-up scheduled to monitor progress.",
    "Patient non-compliant with prescribed treatment."
]

PHYSICAL_EXAM_COMMENTS = [
    "BP: {bp}, HR: {hr}, RR: {rr}, Temp: {temp}. No acute distress.",
    "General appearance: Well-developed, well-nourished. No acute distress.",
    "Cardiovascular: Regular rate and rhythm, no murmurs.",
    "Respiratory: Clear to auscultation bilaterally.",
    "Abdomen: Soft, non-tender, non-distended.",
    "Extremities: No edema, pulses 2+ throughout.",
    "Neurologic: Alert and oriented x3, no focal deficits.",
    "Skin: Warm and dry, no rashes or lesions.",
    "HEENT: Normocephalic, atraumatic. PERRLA. Mucous membranes moist.",
    "Musculoskeletal: No joint swelling or tenderness."
]

COMPLAINT_COMMENTS = [
    "Reports occasional headaches relieved with medication.",
    "No new complaints since last visit.",
    "Complains of increased fatigue and dizziness.",
    "Reports improved energy levels with current treatment.",
    "Experiencing intermittent chest discomfort.",
    "Shortness of breath with moderate exertion.",
    "Frequent urination and increased thirst reported.",
    "Joint pain and stiffness in mornings.",
    "Sleep disturbances and anxiety symptoms.",
    "No specific complaints today."
]

def generate_vital_signs():
    """Generate realistic vital signs"""
    return {
        'bp': f"{random.randint(100, 180)}/{random.randint(60, 100)}",
        'hr': random.randint(50, 100),
        'rr': random.randint(12, 20),
        'temp': round(random.uniform(36.1, 38.2), 1)
    }

def generate_medical_review_record(bp_log, visit_id=None, days=30):
    """Generate medical review record for a given patient"""
    # Base review information
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Clamp compliance time to the last 'days' days
    review_time = fake.date_time_between(
        start_date=start_date,
        end_date=end_date
    )
    
    # Generate vital signs
    vitals = generate_vital_signs()
    
    # Generate clinical notes with context
    clinical_note = random.choice(CLINICAL_NOTES)
    if "stable" in clinical_note.lower() and random.random() < 0.3:
        clinical_note += " Continue current management plan."
    elif "worsening" in clinical_note.lower():
        clinical_note += " Consider specialist referral." if random.random() < 0.5 else " Adjust medications as needed."
    
    # Generate physical exam comments with vitals
    physical_exam = random.choice(PHYSICAL_EXAM_COMMENTS).format(**vitals)
    
    # Generate complaint comments
    complaint_comment = random.choice(COMPLAINT_COMMENTS)
    if "No new complaints" not in complaint_comment and random.random() < 0.6:
        complaint_comment += f" Started {random.randint(1, 14)} days ago." 
    
    return {
        "clinical_note": clinical_note,
        "physical_exam_comments": physical_exam,
        "patient_track_id": bp_log['patient_track_id'],  # Linking to patient
        "complaint_comments": complaint_comment,
        "patient_visit_id":  visit_id if visit_id else str(uuid.uuid4()),  # Visit ID from the log or new UUID
        "patient_medical_review_id": str(uuid.uuid4()),
        "is_active": random.choices([True, False], weights=[0.85, 0.15])[0],
        "is_deleted": False,  # Typically few records would be deleted
        "tenant_id": bp_log['tenant_id'],  # Same as patient's tenant
        "created_by": bp_log['created_by'],  # Same as patient creator
        "updated_by": bp_log['updated_by'],  # Same as patient updater
        "updated_at": review_time.strftime("%Y-%m-%d %H:%M:%S"),
        "created_at": review_time.strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_patient_medical_reviews(bp_logs, visits_per_patient=3, days=30):
    """Generate medical review records for all patients"""
    medical_reviews = []
    
    for _, bp_log in bp_logs.iterrows():
        # Generate 1-5 visits per patient (weighted toward fewer visits)
        num_visits = random.choices([1, 2, 3, 4, 5], weights=[0.4, 0.3, 0.15, 0.1, 0.05])[0]
        
        # Create visit IDs that will be shared across related records
        visit_ids = [str(uuid.uuid4()) for _ in range(num_visits)]
        
        for visit_id in visit_ids:
            # Each visit gets 1 medical review record
            medical_reviews.append(generate_medical_review_record(bp_log, visit_id, days=days))
    
    return pd.DataFrame(medical_reviews)

# Example usage:
# patients = generate_patients(100)  # Using your existing patient generator
# medical_reviews = generate_patient_medical_reviews(patients)