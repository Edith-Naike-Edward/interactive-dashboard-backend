import pandas as pd
import random
from datetime import datetime
import uuid
from faker import Faker

fake = Faker()

# Common medication names for hypertension and diabetes
COMMON_MEDICATIONS = [
    # Diuretics
    "Hydrochlorothiazide", "Chlorthalidone", "Indapamide", "Furosemide", 
    "Spironolactone", "Eplerenone",

    # Beta blockers
    "Metoprolol", "Atenolol", "Propranolol", "Bisoprolol", "Carvedilol",

    # ACE inhibitors
    "Lisinopril", "Enalapril", "Ramipril", "Benazepril",

    # ARBs
    "Losartan", "Valsartan", "Irbesartan", "Telmisartan",

    # Calcium channel blockers
    "Amlodipine", "Diltiazem", "Verapamil", "Nifedipine",

    # Diabetes medications
    "Metformin", "Glimepiride", "Glipizide", "Glyburide", "Gliclazide", 
    "Glibenclamide", "Sitagliptin", "Saxagliptin", "Linagliptin", 
    "Empagliflozin", "Dapagliflozin", "Canagliflozin",

    # Insulins
    "Insulin Lispro", "Insulin Aspart", "Insulin Glargine", "Insulin Detemir", 
    "NPH Insulin",

    # GLP-1 agonists
    "Liraglutide", "Semaglutide", "Dulaglutide",

    # Antiplatelets/anticoagulants
    "Aspirin", "Clopidogrel", "Ticagrelor", "Warfarin", "Rivaroxaban", 
    "Apixaban", "Dabigatran",

    # Statins
    "Atorvastatin", "Simvastatin", "Rosuvastatin", "Pravastatin",

    # Nitrates
    "Nitroglycerin", "Isosorbide Mononitrate", "Isosorbide Dinitrate",

    # Combination drugs
    "Sacubitril/Valsartan",

    # Antidepressants
    "Fluoxetine", "Sertraline", "Escitalopram", "Paroxetine", "Duloxetine", 
    "Venlafaxine", "Amitriptyline", "Imipramine", "Bupropion", "Mirtazapine",

    # Anxiolytics
    "Lorazepam", "Diazepam", "Clonazepam", "Alprazolam", "Buspirone",

    # Antipsychotics/mood stabilizers
    "Quetiapine", "Aripiprazole", "Lithium", "Valproate"
]

# Compliance types
COMPLIANCE_TYPES = [
    "Medication Adherence",
    "Dietary Compliance",
    "Exercise Regimen",
    "Appointment Attendance",
    "Self-Monitoring",
    "Lifestyle Modification"
]


def generate_medical_compliance_record(bp_log):
    """Generate a single medical compliance record for a given BP log"""

    created_at = fake.date_time_between(start_date="-2y", end_date="now")
    updated_at = fake.date_time_between(start_date=created_at, end_date="now")

    # 70% chance it's medication adherence
    is_medication = random.random() < 0.7

    if is_medication:
        name = random.choice(COMMON_MEDICATIONS)
        compliance_name = "Medication Adherence"
        other_compliance = None
    else:
        name = None
        compliance_name = random.choice(COMPLIANCE_TYPES[1:])  # Exclude Medication Adherence
        other_compliance = fake.sentence(nb_words=3) if random.random() < 0.3 else None

    return {
        "patient_medical_compliance_id": str(uuid.uuid4()),
        "compliance_id": str(uuid.uuid4()),
        "name": name,
        "compliance_name": compliance_name,
        "other_compliance": other_compliance,
        "bplog_id": bp_log['bplog_id'],
        "patient_track_id": bp_log['patient_track_id'],
        "is_active": random.choices([True, False], weights=[0.8, 0.2])[0],
        "is_deleted": False,
        "tenant_id": bp_log['tenant_id'],
        "created_by": bp_log['created_by'],
        "updated_by": bp_log['updated_by'],
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S")
    }


def generate_patient_medical_compliances(bp_logs):
    """Generate compliance records for each BP log"""

    compliances = []
    for _, bp_log in bp_logs.iterrows():
        # Generate 1 to 5 compliance records per BP log
        num_records = random.choices([1, 2, 3, 4, 5], weights=[0.3, 0.3, 0.2, 0.1, 0.1])[0]
        
        for _ in range(num_records):
            compliance = generate_medical_compliance_record(bp_log)
            compliances.append(compliance)

    return pd.DataFrame(compliances)


# Example usage:
# screenings_df = generate_screening_logs()  # from your screeninglog_generator
# bp_logs_df = generate_bp_log(screenings_df)
# compliance_df = generate_patient_medical_compliances(bp_logs_df)
