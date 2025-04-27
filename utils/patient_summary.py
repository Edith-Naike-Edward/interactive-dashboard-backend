# import json
# from pathlib import Path
# import pandas as pd
# from Backend.src.generators.patient_generator import repeat_patient_ids

# # Define data paths
# DATA_PATH = Path("data/patient_counts.json")
# NEW_PATIENTS_CSV = Path("data/raw/new_patients.csv")
# REPEAT_PATIENTS_CSV = Path("data/raw/repeat_patients.csv")
# ALL_PATIENTS_CSV = Path("data/raw/patients.csv")

# def load_previous_patient_counts():
#     """Load previous patient counts from JSON file"""
#     if not DATA_PATH.exists():
#         return {"total_patients": 0, "new_patients": 0, "repeat_patients": 0}
#     with open(DATA_PATH) as f:
#         return json.load(f)

# def save_current_patient_counts(total_patients, new_patients, repeat_patients):
#     """Save current patient counts to JSON file"""
#     with open(DATA_PATH, "w") as f:
#         json.dump({
#             "total_patients": total_patients,
#             "new_patients": new_patients,
#             "repeat_patients": repeat_patients
#         }, f)

# def generate_patient_splits():
#     """If new/repeat patient files don't exist, generate them from patients.csv"""
#     if not NEW_PATIENTS_CSV.exists() or not REPEAT_PATIENTS_CSV.exists():
#         if not ALL_PATIENTS_CSV.exists():
#             raise FileNotFoundError("patients.csv not found. Cannot generate patient splits.")
        
#         # all_patients_df = pd.read_csv(ALL_PATIENTS_CSV)

#         # # new_patients_df = all_patients_df['patient_id'].isin(repeat_patient_ids) 
#         # # repeat_patients_df = all_patients_df['patient_id'].isin(repeat_patient_ids)
#         # # FIXED: Select rows, not just booleans
#         # new_patients_df = all_patients_df[~all_patients_df['patient_id'].isin(repeat_patient_ids)]
#         # repeat_patients_df = all_patients_df[all_patients_df['patient_id'].isin(repeat_patient_ids)]

#         # Read with explicit type specification
#         all_patients_df = pd.read_csv(ALL_PATIENTS_CSV, dtype={'patient_id': str})
        
#         # Ensure patient_id is string type
#         all_patients_df['patient_id'] = all_patients_df['patient_id'].astype(str)
#         repeat_patient_ids = [str(patient_id) for patient_id in repeat_patient_ids]  # Ensure comparison types match
        
#         # Generate splits
#         new_patients_df = all_patients_df[~all_patients_df['patient_id'].isin(repeat_patient_ids)]
#         repeat_patients_df = all_patients_df[all_patients_df['patient_id'].isin(repeat_patient_ids)]
        
#         # Save with index=False to avoid extra column
#         new_patients_df.to_csv(NEW_PATIENTS_CSV, index=False)
#         repeat_patients_df.to_csv(REPEAT_PATIENTS_CSV, index=False)

# def get_current_patient_counts():
#     """Get current patient counts from CSV files"""
#     try:
#         generate_patient_splits()
        
#         new_patients_df = pd.read_csv(NEW_PATIENTS_CSV)
#         repeat_patients_df = pd.read_csv(REPEAT_PATIENTS_CSV)
        
#         new_patients_count = len(new_patients_df)
#         repeat_patients_count = len(repeat_patients_df)
#         total_patients = new_patients_count + repeat_patients_count
        
#         return total_patients, new_patients_count, repeat_patients_count
#     except FileNotFoundError:
#         return 0, 0, 0

# def get_patient_summary():
#     """Get patient summary with optional limit on records returned"""
#     generate_patient_splits()

#     total_patients, new_patients_count, repeat_patients_count = get_current_patient_counts()

#     # new_patients_df = pd.read_csv(NEW_PATIENTS_CSV)
#     # repeat_patients_df = pd.read_csv(REPEAT_PATIENTS_CSV)
#     # new_patients_df = pd.read_csv(NEW_PATIENTS_CSV, dtype={'patient_id': str})
#     # repeat_patients_df = pd.read_csv(REPEAT_PATIENTS_CSV, dtype={'patient_id': str})

#     # Read with explicit type specification
#     new_patients_df = pd.read_csv(NEW_PATIENTS_CSV, dtype={'patient_id': str})
#     repeat_patients_df = pd.read_csv(REPEAT_PATIENTS_CSV, dtype={'patient_id': str})
    
#     # Convert any remaining boolean values to strings
#     new_patients_df['patient_id'] = new_patients_df['patient_id'].astype(str)
#     repeat_patients_df['patient_id'] = repeat_patients_df['patient_id'].astype(str)

            
#     # summary["new_patients_sample"] = new_patients_df
#     # summary["repeat_patients_sample"] = repeat_patients_df
    
#     summary = {
#         "total_patients": total_patients,
#         "new_patients_count": new_patients_count,
#         "repeat_patients_count": repeat_patients_count,
#         "new_patients_sample": new_patients_df.head(5).to_dict(orient="records"),  # convert DataFrame to list of dicts
#         "repeat_patients_sample": repeat_patients_df.head(5).to_dict(orient="records")
#     }



#     return summary
