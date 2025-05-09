import pandas as pd
from faker import Faker
import random
import numpy as np
from datetime import datetime, timedelta
import uuid
from config.settings import NUM_PATIENTS, KDHS_2022, REPEAT_PATIENT_RATE
from datetime import date
from src.generators.site_user_generation import generate_site_user_data
sites_df, _ = generate_site_user_data(n_users_per_site=0)  
fake = Faker()

# # Add these global variables after your other mappings
# patient_pool = []  # Stores base patient profiles
# generated_patients = []  # Tracks all generated patients (new and repeats)
# Global variables to track patients
patient_pool = []  # Stores base patient profiles
generated_patients = []  # Tracks all generated patients (new and repeats)
repeat_patient_ids = set()  # Track patient IDs of repeat patients

# County and sub-county mappings
COUNTIES = {
    "Makueni": 1, "Nyeri": 2, "Kakamega": 3, "Nakuru": 4, "Nyandarua": 5,
    "Meru": 6, "Kilifi": 7, "Mombasa": 8, "Nairobi": 9
}

SUB_COUNTIES = {
    # Makueni County
    "Makueni": "Makueni", "Mbooni": "Makueni", "Kaiti": "Makueni",
    "Kibwezi East": "Makueni", "Kibwezi West": "Makueni", "Kilome": "Makueni",
    
    # Nyeri County
    "Kieni East": "Nyeri", "Kieni West": "Nyeri", "Mathira East": "Nyeri",
    "Mathira West": "Nyeri", "Othaya": "Nyeri", "Mukurweini": "Nyeri",
    "Nyeri Town": "Nyeri", "Tetu": "Nyeri",
    
    # Kakamega County
    "Lukuyani": "Kakamega", "Butere": "Kakamega", "Mumias": "Kakamega",
    "Matete": "Kakamega", "Lugari": "Kakamega", "Lurambi": "Kakamega",
    "Khwisero": "Kakamega", "Mutungu": "Kakamega", "Navakholo": "Kakamega",
    "Kakamega South": "Kakamega", "Kakamega Central": "Kakamega",
    "Kakamega East": "Kakamega", "Kakamega North": "Kakamega",
    
    # Nakuru County
    "Nakuru Town East": "Nakuru", "Nakuru Town West": "Nakuru",
    "Naivasha": "Nakuru", "Molo": "Nakuru", "Gilgil": "Nakuru",
    "Bahati": "Nakuru", "Kuresoi North": "Nakuru", "Kuresoi South": "Nakuru",
    "Njoro": "Nakuru", "Rongai": "Nakuru", "Subukia": "Nakuru",
    
    # Nyandarua County
    "Ol Kalou": "Nyandarua", "Kipipiri": "Nyandarua", "Ndaragwa": "Nyandarua",
    "Kinangop": "Nyandarua", "Ol Joro Orok": "Nyandarua",
    
    # Meru County
    "Imenti Central": "Meru", "Imenti North": "Meru", "Imenti South": "Meru",
    "Tigania East": "Meru", "Tigania West": "Meru", "Buuri": "Meru",
    "Igembe Central": "Meru", "Igembe North": "Meru", "Igembe South": "Meru",
    
    # Kilifi County
    "Kilifi North": "Kilifi", "Kilifi South": "Kilifi", "Malindi": "Kilifi",
    "Magarini": "Kilifi", "Ganze": "Kilifi", "Rabai": "Kilifi",
    "Kaloleni": "Kilifi",
    
    # Mombasa County
    "Mvita": "Mombasa", "Kisauni": "Mombasa", "Changamwe": "Mombasa",
    "Likoni": "Mombasa", "Jomvu": "Mombasa", "Nyali": "Mombasa",
    
    # Nairobi County
    "Dagoretti North": "Nairobi", "Dagoretti South": "Nairobi",
    "Embakasi Central": "Nairobi", "Embakasi East": "Nairobi",
    "Embakasi North": "Nairobi", "Embakasi South": "Nairobi",
    "Embakasi West": "Nairobi", "Kamukunji": "Nairobi", "Kasarani": "Nairobi",
    "Lang'ata": "Nairobi", "Westlands": "Nairobi", "Kibra": "Nairobi",
    "Makadara": "Nairobi", "Mathare": "Nairobi", "Ruaraka": "Nairobi",
    "Starehe": "Nairobi", "Roysambu": "Nairobi"
}

subcounty_to_idmapping = {
    # Makueni County
    "Makueni": 1,
    "Mbooni": 2,
    "Kaiti": 3,
    "Kibwezi East": 4,
    "Kibwezi West": 5,
    "Kilome": 6,

    # Nyeri County
    "Kieni East": 7,
    "Kieni West": 8,
    "Mathira East": 9,
    "Mathira West": 10,
    "Othaya": 11,
    "Mukurweini": 12,
    "Nyeri Town": 13,
    "Tetu": 14,

    # Kakamega County
    "Lukuyani": 15,
    "Butere": 16,
    "Mumias": 17,
    "Matete": 18,
    "Lugari": 19,
    "Lurambi": 20,
    "Khwisero": 21,
    "Mutungu": 22,
    "Navakholo": 23,
    "Kakamega South": 24,
    "Kakamega Central": 25,
    "Kakamega East": 26,
    "Kakamega North": 27,

    # Nakuru County
    "Nakuru Town East": 28,
    "Nakuru Town West": 29,
    "Naivasha": 30,
    "Molo": 31,
    "Gilgil": 32,
    "Bahati": 33,
    "Kuresoi North": 34,
    "Kuresoi South": 35,
    "Njoro": 36,
    "Rongai": 37,
    "Subukia": 38,

    # Nyandarua County
    "Ol Kalou": 39,
    "Kipipiri": 40,
    "Ndaragwa": 41,
    "Kinangop": 42,
    "Ol Joro Orok": 43,

    # Meru County
    "Imenti Central": 44,
    "Imenti North": 45,
    "Imenti South": 46,
    "Tigania East": 47,
    "Tigania West": 48,
    "Buuri": 49,
    "Igembe Central": 50,
    "Igembe North": 51,
    "Igembe South": 52,

    # Kilifi County
    "Kilifi North": 53,
    "Kilifi South": 54,
    "Malindi": 55,
    "Magarini": 56,
    "Ganze": 57,
    "Rabai": 58,
    "Kaloleni": 59,

    # Mombasa County
    "Mvita": 60,
    "Kisauni": 61,
    "Changamwe": 62,
    "Likoni": 63,
    "Jomvu": 64,
    "Nyali": 65,

    # Nairobi County
    "Dagoretti North": 66,
    "Dagoretti South": 67,
    "Embakasi Central": 68,
    "Embakasi East": 69,
    "Embakasi North": 70,
    "Embakasi South": 71,
    "Embakasi West": 72,
    "Kamukunji": 73,
    "Kasarani": 74,
    "Lang'ata": 75,
    "Westlands": 76,
    "Kibra": 77,
    "Makadara": 78,
    "Mathare": 79,
    "Ruaraka": 80,
    "Starehe": 81,
    "Roysambu": 82

}

county_mapping = {
    1: "Makueni",
    2: "Nyeri",
    3: "Kakamega",
    4: "Nakuru",
    5: "Nyandarua",
    6: "Meru",
    7: "Kilifi",
    8: "Mombasa",
    9: "Nairobi"
}

# Education levels
EDUCATION_LEVELS = [
    "No Formal Education",
    "Primary Education",
    "Secondary Education",
    "Diploma",
    "Bachelor's Degree",
    "Master's Degree",
    "Doctorate"
]

# Insurance types
INSURANCE_TYPES = [
    "NHIF", "Private", "Community-Based", "Employer-Based", "None"
]

def generate_base_patient():
    """Generate a base patient profile with core demographics"""
    patient = generate_patient_record()
    # Remove visit-specific details that might change between visits
    for field in ['site_id', 'site_name', 'program_id', 'program_name', 
                 'created_at', 'updated_at', 'is_pregnant', 'is_active']:
        patient.pop(field, None)
    return patient

def _assign_health_conditions(patients):
    """Assign conditions based on KDHS statistics with county adjustments"""
    age_group = '15-49' if patients['age'] <= 49 else '50+'
    gender_key = f"{patients['gender']}_{age_group}"
    # county = patient['county_name']
    
    
    # Hypertension
    htn_prob = KDHS_2022['hypertension']['prevalence'].get(gender_key, 0)
    
    if np.random.random() < htn_prob:
        patients['has_hypertension'] = True
        patients['on_htn_meds'] = np.random.random() < KDHS_2022['hypertension']['treatment_rate']
    
    # Diabetes
    diabetes_prob = KDHS_2022['diabetes']['prevalence'].get(age_group, 0)
    
    if np.random.random() < diabetes_prob:
        patients['has_diabetes'] = True
        patients['on_diabetes_meds'] = np.random.random() < KDHS_2022['diabetes']['treatment_rate'][patients['gender']]
    
    # Mental health
    mh_prob = KDHS_2022['mental_health']['prevalence'].get(gender_key, 0)
    if np.random.random() < mh_prob:
        patients['has_mental_health_issue'] = True
        patients['on_mh_treatment'] = np.random.random() < KDHS_2022['mental_health']['treatment_rate'][patients['gender']]
    
    return patients

def generate_patient_record():
    """Generate or identify an existing (repeat) patient."""
    # Generate a new or repeat patient based on REPEAT_PATIENT_RATE
    if random.random() < REPEAT_PATIENT_RATE and repeat_patient_ids:
        # If we decide to generate a repeat patient
        patient_id = random.choice(list(repeat_patient_ids))  # Choose an existing patient ID
        existing_patient = next(p for p in generated_patients if p["patient_id"] == patient_id)
        return existing_patient  # Return the repeat patient's details

    # If it's a new patient, generate a new one
    patient = generate_new_patient()
    repeat_patient_ids.add(patient["patient_id"])  # Add new patient's ID to repeat set
    return patient

def generate_new_patient():
    # Select a random sub-county and get its county
    sub_county_name = random.choice(list(SUB_COUNTIES.keys()))
    county_name = SUB_COUNTIES[sub_county_name]
    sub_county_id = subcounty_to_idmapping[sub_county_name]
    county_id = COUNTIES[county_name]
    random_site = sites_df.sample(1).iloc[0]
    
    # Generate names with 30% chance of having middle name
    first_name = fake.first_name()
    last_name = fake.last_name()
    middle_name = fake.first_name() if random.random() < 0.3 else ""
    
    # Generate dates with realistic age range
    dob = fake.date_of_birth(minimum_age=25, maximum_age=80)
    # age = (datetime.now() - dob).days // 365
    age = (date.today() - dob).days // 365
    created_at = fake.date_time_between(start_date="-5y", end_date="now")
    updated_at = fake.date_time_between(start_date=created_at, end_date="now")
    
    # Generate phone number
    phone_category = random.choice(["Personal", "Work", "Family", "Emergency"])
    phone_number = fake.msisdn()[3:]  # Remove country code
    
    # Insurance details
    full_uuid = uuid.uuid4().int  # Get UUID as integer
    insurance_id = str(full_uuid)[:14]  # Take first 14 digits
    has_insurance = random.random() < 0.7  # 70% have insurance
    insurance_status = "Active" if has_insurance else "None"
    insurance_type = random.choice(INSURANCE_TYPES) if has_insurance else "None"
    insurance_id = insurance_id if has_insurance else ""

    # Generate 9-digit patient ID from UUID
    full_uuid = uuid.uuid4().int  # Get UUID as integer
    # Generate patient ID, national ID, and insurance ID from UUID
    patient_id = str(full_uuid)[:9]  # Take first 9 digits
    national_id = str(full_uuid)[:14]  # Take first 14 digits
    insurance_id = str(full_uuid)[:14]  # Take first 14 digits
    
    gender = random.choice(["M", "F", "Other"])
    return {
        "sub_county_id": sub_county_id,
        "sub_county_name": sub_county_name,
        "national_id": national_id,
        "initial": first_name[0],
        "occupation": fake.job(),
        "patient_id": patient_id,
        "gender": gender,
        "date_of_birth": dob.strftime("%Y-%m-%d"),
        "is_regular_smoker": random.choice([True, False]),
        "insurance_id": insurance_id,
        "country_id": "KE",  # Kenya
        "country_name": "Kenya",
        "county_id": county_id,
        "county_name": county_name,
        "level_of_education": random.choice(EDUCATION_LEVELS),
        "phone_number_category": phone_category,
        "phone_number": phone_number,
        "insurance_status": insurance_status,
        "is_pregnant": random.choice([True, False]) if gender == "F" and age >= 18 and age <= 45 else False,
        "site_id": random_site['site_id'],  # Use real site ID
        "site_name": random_site['name'],   # Use real site name
        "first_name": first_name,
        "last_name": last_name,
        "age": age,
        "middle_name": middle_name,
        "landmark": fake.street_address(),
        "program_id": str(uuid.uuid4()),
        "program_name": random.choice(["Diabetes Care", "Hypertension Management", "General Wellness"]),
        "insurance_type": insurance_type,
        "is_support_group": random.choice([True, False]),
        "is_active": random.choice([True, False]),
        "is_deleted": False,  # Typically few records would be deleted
        "tenant_id": str(uuid.uuid4()),
        "created_by": str(uuid.uuid4()),
        "updated_by": str(uuid.uuid4()),
        "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_patients(num_patients):
    """Generate patients and return as DataFrame"""
    patients_list = []
    
    for _ in range(num_patients):
        patient = generate_patient_record()
        patient = _assign_health_conditions(patient)  # Add health conditions
        patients_list.append(patient)
        generated_patients.append(patient)
        
        # Add to patient pool if needed
        if random.random() < 0.3:  # Example probability
            patient_pool.append(generate_base_patient(patient))
    
    # Convert to DataFrame with proper types
    patients_df = pd.DataFrame(patients_list)
    
    # Convert date fields
    date_cols = ['date_of_birth', 'created_at', 'updated_at']
    for col in date_cols:
        if col in patients_df.columns:
            patients_df[col] = pd.to_datetime(patients_df[col])
    
    return patients_df

def calculate_patient_summary(patients_df: pd.DataFrame):
    """
    Calculate and display patient summary statistics, and save repeat and new patients to separate CSV files.
    
    Args:
        patients_df: DataFrame containing all generated patients
    """
    patients_df['is_repeat'] = patients_df['patient_id'].isin(repeat_patient_ids) # Mark repeat patients
    
    # Separate the DataFrames
    new_patients = patients_df[~patients_df['is_repeat']]
    repeat_patients = patients_df[patients_df['is_repeat']]
    
    # Save to CSV files
    new_patients.to_csv('new_patients.csv', index=False)
    repeat_patients.to_csv('repeat_patients.csv', index=False)
    
    # Calculate statistics
    total_patients = len(patients_df)
    new_patient_count = len(new_patients)
    repeat_patient_count = len(repeat_patients)
    
    print("Patient Summary:")
    print(f"  Total Patient Records: {total_patients}")
    print(f"  New Patients: {new_patient_count}")
    print(f"  Repeat Patients: {repeat_patient_count}")
    print("\nData saved to:")
    print("  - new_patients.csv")
    print("  - repeat_patients.csv")
    