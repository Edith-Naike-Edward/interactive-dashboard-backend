import pandas as pd
import random
from datetime import datetime, timedelta
import uuid
from faker import Faker

fake = Faker()

# Lifestyle categories and details
LIFESTYLE_CATEGORIES = {
    "Diet": [
        "Reduce salt intake", "Increase vegetable consumption", "Reduce sugar intake",
        "Follow Mediterranean diet", "Low-carb diet", "Portion control"
    ],
    "Exercise": [
        "30 minutes walking daily", "Aerobic exercise 3x/week", "Strength training 2x/week",
        "Yoga practice", "Swimming weekly", "Cycling regimen"
    ],
    "Substance Use": [
        "Smoking cessation", "Reduce alcohol consumption", "Caffeine reduction",
        "Drug abstinence", "Nicotine replacement therapy"
    ],
    "Sleep": [
        "Sleep hygiene improvement", "Regular sleep schedule", "Reduce screen time before bed",
        "Treat sleep apnea", "Relaxation techniques"
    ],
    "Stress Management": [
        "Meditation practice", "Deep breathing exercises", "Counseling sessions",
        "Work-life balance", "Time management"
    ],
    "Other": [
        "Regular health checkups", "Medication adherence", "Weight management",
        "Blood pressure monitoring", "Blood sugar monitoring"
    ]
}

LIFESTYLE_ANSWERS = [
    "Following as recommended", "Partially following", "Not following", "Needs improvement",
    "Exceeding recommendations", "Recently started", "Consistently maintained"
]

def generate_lifestyle_comment(lifestyle_name):
    """Generate appropriate comment based on lifestyle category"""
    base_comments = {
        "Diet": "Nutritional counseling provided with focus on {}. Meal planning resources offered.",
        "Exercise": "Physical activity plan developed emphasizing {}. Follow-up scheduled to assess progress.",
        "Substance Use": "Harm reduction strategies discussed for {}. Support resources provided.",
        "Sleep": "Sleep improvement plan created targeting {}. Sleep diary recommended.",
        "Stress Management": "Stress reduction techniques taught including {}. Follow-up scheduled.",
        "Other": "Health maintenance guidance provided regarding {}. Educational materials shared."
    }
    category = next((k for k in LIFESTYLE_CATEGORIES if lifestyle_name in LIFESTYLE_CATEGORIES[k]), "Other")
    return base_comments[category].format(lifestyle_name.lower())

def generate_lifestyle_record(bp_log):
    """Generate lifestyle record using bp_log linkage"""
    created_at = fake.date_time_between(start_date="-2y", end_date="now")
    updated_at = fake.date_time_between(start_date=created_at, end_date="now")

    category = random.choice(list(LIFESTYLE_CATEGORIES.keys()))
    lifestyle_name = random.choice(LIFESTYLE_CATEGORIES[category])
    lifestyle_answer = random.choice(LIFESTYLE_ANSWERS)
    comments = generate_lifestyle_comment(lifestyle_name)

    if "Not following" in lifestyle_answer:
        comments += " Patient requires additional support and motivation."
    elif "Following as recommended" in lifestyle_answer:
        comments += " Patient demonstrates good compliance."

    return {
        "comments": comments,
        "patient_lifestyle_id": str(uuid.uuid4()),
        "lifestyle_id": str(uuid.uuid4()),
        "lifestyle_name": lifestyle_name,
        "lifestyle_answer": lifestyle_answer,
        "patient_track_id": bp_log['patient_track_id'],  # Link to bp_log
        "is_active": random.choices([True, False], weights=[0.9, 0.1])[0],
        "is_deleted": False,
        "tenant_id": bp_log['tenant_id'],
        "created_by": bp_log['created_by'],
        "updated_by": bp_log['updated_by'],
        "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_patient_lifestyles(bp_log_df):
    """Generate lifestyle records using bp_log linkage"""
    lifestyles = []

    # Iterate through the BP logs
    for _, bp_log_row in bp_log_df.iterrows():
        # Randomly decide how many lifestyle records to generate per log
        num_samples = random.choice([1, 2, 3, 4])

        for _ in range(num_samples):
            lifestyle = generate_lifestyle_record(bp_log_row)
            lifestyles.append(lifestyle)

    return pd.DataFrame(lifestyles)


# Example usage:
# patients = generate_patients(100)
# bp_logs = generate_bp_logs(patients)  # Assumes bp_logs include 'patient_id'
# lifestyles = generate_patient_lifestyles(patients, bp_logs)
# print(lifestyles.head())