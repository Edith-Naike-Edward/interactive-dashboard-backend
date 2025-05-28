from pathlib import Path
import pandas as pd
import json
from datetime import datetime, timedelta
import time
from fastapi import HTTPException
from fastapi.responses import JSONResponse

# Define paths
DIAGNOSES_PATH = Path("data/raw/diagnoses.csv")
BP_LOGS_PATH = Path("data/raw/bp_logs.csv")
GLUCOSE_LOGS_PATH = Path("data/raw/glucose_logs.csv")
HISTORICAL_METRICS_PATH = Path("data/historical_metrics.json")

# Configuration
MIN_COMPARISON_INTERVAL = 300  # 5 minutes in seconds
MAX_HISTORICAL_METRICS = 1000
MAX_HISTORICAL_ALERTS = 100

def load_data_safely(file_path, required_columns=None):
    """Safe data loading with validation"""
    try:
        df = pd.read_csv(file_path)
        if required_columns:
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def get_most_recent_comparable_metrics():
    """Get metrics that are old enough for comparison"""
    historical_data = load_historical_data()
    if not historical_data or not historical_data.get("metrics"):
        return None
    
    now = datetime.now()
    comparable_metrics = [
        m for m in historical_data["metrics"]
        if (now - datetime.fromisoformat(m["timestamp"])).total_seconds() > MIN_COMPARISON_INTERVAL
    ]
    
    return max(comparable_metrics, key=lambda x: x["timestamp"]) if comparable_metrics else None

def calculate_monitoring_metrics():
    """Calculate metrics with robust error handling"""
    metrics = {
        "percent_new_diagnoses": 0,
        "percent_bp_followup": 0,
        "percent_bg_followup": 0,
        "percent_bp_controlled": 0,
        "performance_declined": True,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Load data with validation
        diagnoses_df = load_data_safely(DIAGNOSES_PATH, ["patient_track_id", "diabetes_patient_type", "htn_patient_type"])
        bp_logs_df = load_data_safely(BP_LOGS_PATH, ["patient_track_id", "avg_systolic", "avg_diastolic"])
        glucose_logs_df = load_data_safely(GLUCOSE_LOGS_PATH, ["patient_track_id"])
        
        if diagnoses_df is None or bp_logs_df is None or glucose_logs_df is None:
            return metrics
        
        # Calculate metrics with division protection
        total_diagnosed = diagnoses_df["patient_track_id"].nunique()
        new_diagnoses = diagnoses_df[
            (diagnoses_df['diabetes_patient_type'] == 'Newly diagnosed') |
            (diagnoses_df['htn_patient_type'] == 'Newly diagnosed')
        ]["patient_track_id"].nunique()
        
        bp_patients = bp_logs_df["patient_track_id"].nunique()
        bp_followup_counts = bp_logs_df.groupby("patient_track_id").size()
        bp_followup = bp_followup_counts[bp_followup_counts > 1].count() if bp_patients > 0 else 0
        
        bg_patients = glucose_logs_df["patient_track_id"].nunique()
        bg_followup_counts = glucose_logs_df.groupby("patient_track_id").size()
        bg_followup = bg_followup_counts[bg_followup_counts > 1].count() if bg_patients > 0 else 0

        # BP control metrics
        bp_controlled_count = 0
        if bp_patients > 0:
            bp_controlled = bp_logs_df.groupby("patient_track_id").agg({
                'avg_systolic': 'mean',
                'avg_diastolic': 'mean'
            })
            bp_controlled_count = len(bp_controlled[
                (bp_controlled['avg_systolic'] < 140) & 
                (bp_controlled['avg_diastolic'] < 90)
            ])

        # Calculate percentages and threshold violations
        new_diag_percent = round((new_diagnoses / total_diagnosed * 100) if total_diagnosed > 0 else 0, 2)
        bp_followup_percent = round((bp_followup / bp_patients * 100) if bp_patients > 0 else 0, 2)
        bg_followup_percent = round((bg_followup / bg_patients * 100) if bg_patients > 0 else 0, 2)
        bp_controlled_percent = round((bp_controlled_count / bp_patients * 100) if bp_patients > 0 else 0, 2)

        new_diag_violation = (new_diag_percent < 50) if total_diagnosed > 0 else True
        bp_followup_violation = (bp_followup_percent < 50) if bp_patients > 0 else True
        bg_followup_violation = (bg_followup_percent < 50) if bg_patients > 0 else True
        bp_controlled_violation = (bp_controlled_percent < 50) if bp_patients > 0 else True

        metrics.update({
            "percent_new_diagnoses": new_diag_percent,
            "percent_bp_followup": bp_followup_percent,
            "percent_bg_followup": bg_followup_percent,
            "percent_bp_controlled": bp_controlled_percent,
            "performance_declined": new_diag_violation or bp_followup_violation or bg_followup_violation or bp_controlled_violation,
            "threshold_violations": {
                "new_diagnoses": new_diag_violation,
                "bp_followup": bp_followup_violation,
                "bg_followup": bg_followup_violation,
                "bp_controlled": bp_controlled_violation
            }
        })
        
    except Exception as e:
        print(f"Error calculating metrics: {e}")
    
    return metrics

def calculate_percentage_change(previous, current):
    """Safe percentage change calculation"""
    if previous is None or previous == 0:
        return 0
    return round(((current - previous) / previous) * 100, 2)

def load_historical_data():
    """Load historical data with validation"""
    default_data = {"metrics": [], "alerts": []}
    
    if not HISTORICAL_METRICS_PATH.exists():
        return default_data
    
    try:
        with open(HISTORICAL_METRICS_PATH, 'r') as f:
            content = f.read().strip()
            if not content:
                return default_data
            
            data = json.loads(content)
            # Validate structure
            if not isinstance(data, dict):
                return default_data
            if "metrics" not in data:
                data["metrics"] = []
            if "alerts" not in data:
                data["alerts"] = []
                
            return data
            
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading historical data: {e}")
        return default_data

def save_historical_data(current_metrics):
    """Save metrics to historical data with proper comparison"""
    try:
        historical_data = load_historical_data()
        previous_metrics = get_most_recent_comparable_metrics()
        
        # Add current metrics
        historical_data["metrics"].append(current_metrics)
        
        # Calculate changes if we have previous metrics to compare with
        if previous_metrics:
            changes = {
                "new_diagnoses": calculate_percentage_change(
                    previous_metrics["percent_new_diagnoses"],
                    current_metrics["percent_new_diagnoses"]
                ),
                "bp_followup": calculate_percentage_change(
                    previous_metrics["percent_bp_followup"],
                    current_metrics["percent_bp_followup"]
                ),
                "bg_followup": calculate_percentage_change(
                    previous_metrics["percent_bg_followup"],
                    current_metrics["percent_bg_followup"]
                ),
                "bp_controlled": calculate_percentage_change(
                    previous_metrics["percent_bp_controlled"],
                    current_metrics["percent_bp_controlled"]
                )
            }
            
            current_metrics["changes"] = changes
            
            # Create alert if performance declined
            if current_metrics["performance_declined"]:
                alert = {
                    "timestamp": current_metrics["timestamp"],
                    "metrics": current_metrics.copy(),
                    "changes": changes
                }
                historical_data["alerts"].append(alert)
        
        # Trim data to maintain size limits
        historical_data["metrics"] = historical_data["metrics"][-MAX_HISTORICAL_METRICS:]
        historical_data["alerts"] = historical_data["alerts"][-MAX_HISTORICAL_ALERTS:]
        
        # Save back to file
        HISTORICAL_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORICAL_METRICS_PATH, 'w') as f:
            json.dump(historical_data, f, indent=2)
            
        return current_metrics
        
    except Exception as e:
        print(f"Error saving historical data: {e}")
        return None

def main():
    """Main monitoring workflow"""
    # Calculate current metrics
    current_metrics = calculate_monitoring_metrics()

    # If calculate_monitoring_metrics failed severely, return a default
    if not current_metrics or "percent_new_diagnoses" not in current_metrics:
        print("Warning: Invalid metrics, returning defaults.")
        return current_metrics
    
    # Save to historical data and get enhanced metrics with changes
    enhanced_metrics = save_historical_data(current_metrics)
    
    if enhanced_metrics:
        return enhanced_metrics
    return current_metrics
# from pathlib import Path
# import pandas as pd
# import json
# from datetime import datetime, timedelta
# import time

# # Define paths
# DIAGNOSES_PATH = Path("data/raw/diagnoses.csv")
# BP_LOGS_PATH = Path("data/raw/bp_logs.csv")
# GLUCOSE_LOGS_PATH = Path("data/raw/glucose_logs.csv")
# HISTORICAL_METRICS_PATH = Path("data/historical_metrics.json")

# # Configuration
# MIN_COMPARISON_INTERVAL = 300  # 5 minutes in seconds
# MAX_HISTORICAL_METRICS = 1000
# MAX_HISTORICAL_ALERTS = 100

# def load_data_safely(file_path, required_columns=None):
#     """Safe data loading with validation"""
#     try:
#         df = pd.read_csv(file_path)
#         if required_columns:
#             missing_cols = [col for col in required_columns if col not in df.columns]
#             if missing_cols:
#                 raise ValueError(f"Missing required columns: {missing_cols}")
#         return df
#     except Exception as e:
#         print(f"Error loading {file_path}: {e}")
#         return None

# def get_most_recent_comparable_metrics():
#     """Get metrics that are old enough for comparison"""
#     historical_data = load_historical_data()
#     if not historical_data or not historical_data.get("metrics"):
#         return None
    
#     now = datetime.now()
#     comparable_metrics = [
#         m for m in historical_data["metrics"]
#         if (now - datetime.fromisoformat(m["timestamp"])).total_seconds() > MIN_COMPARISON_INTERVAL
#     ]
    
#     return max(comparable_metrics, key=lambda x: x["timestamp"]) if comparable_metrics else None

# def calculate_monitoring_metrics():
#     """Calculate metrics with robust error handling"""
#     metrics = {
#         "percent_new_diagnoses": 0,
#         "percent_bp_followup": 0,
#         "percent_bg_followup": 0,
#         "percent_bp_controlled": 0,
#         "performance_declined": True,
#         "timestamp": datetime.now().isoformat()
#     }
    
#     try:
#         # Load data with validation
#         diagnoses_df = load_data_safely(DIAGNOSES_PATH, ["patient_track_id", "diabetes_patient_type", "htn_patient_type"])
#         bp_logs_df = load_data_safely(BP_LOGS_PATH, ["patient_track_id", "avg_systolic", "avg_diastolic"])
#         glucose_logs_df = load_data_safely(GLUCOSE_LOGS_PATH, ["patient_track_id"])
        
#         if diagnoses_df is None or bp_logs_df is None or glucose_logs_df is None:
#             return metrics
        
#         # Calculate metrics with division protection
#         total_diagnosed = diagnoses_df["patient_track_id"].nunique()
#         new_diagnoses = diagnoses_df[
#             (diagnoses_df['diabetes_patient_type'] == 'Newly diagnosed') |
#             (diagnoses_df['htn_patient_type'] == 'Newly diagnosed')
#         ]["patient_track_id"].nunique()
        
#         bp_patients = bp_logs_df["patient_track_id"].nunique()
#         bp_followup_counts = bp_logs_df.groupby("patient_track_id").size()
#         bp_followup = bp_followup_counts[bp_followup_counts > 1].count() if bp_patients > 0 else 0
        
#         bg_patients = glucose_logs_df["patient_track_id"].nunique()
#         bg_followup_counts = glucose_logs_df.groupby("patient_track_id").size()
#         bg_followup = bg_followup_counts[bg_followup_counts > 1].count() if bg_patients > 0 else 0

#         # BP control metrics
#         bp_controlled_count = 0
#         if bp_patients > 0:
#             bp_controlled = bp_logs_df.groupby("patient_track_id").agg({
#                 'avg_systolic': 'mean',
#                 'avg_diastolic': 'mean'
#             })
#             bp_controlled_count = len(bp_controlled[
#                 (bp_controlled['avg_systolic'] < 140) & 
#                 (bp_controlled['avg_diastolic'] < 90)
#             ])

#         # Calculate percentages
#         metrics.update({
#             "percent_new_diagnoses": round((new_diagnoses / total_diagnosed * 100) if total_diagnosed > 0 else 0, 2),
#             "percent_bp_followup": round((bp_followup / bp_patients * 100) if bp_patients > 0 else 0, 2),
#             "percent_bg_followup": round((bg_followup / bg_patients * 100) if bg_patients > 0 else 0, 2),
#             "percent_bp_controlled": round((bp_controlled_count / bp_patients * 100) if bp_patients > 0 else 0, 2),
#             "performance_declined": (
#                 (new_diagnoses / total_diagnosed < 0.5 if total_diagnosed > 0 else True) or
#                 (bp_followup / bp_patients < 0.5 if bp_patients > 0 else True) or
#                 (bg_followup / bg_patients < 0.5 if bg_patients > 0 else True) or
#                 (bp_controlled_count / bp_patients < 0.5 if bp_patients > 0 else True)
#             )
#         })
        
#     except Exception as e:
#         print(f"Error calculating metrics: {e}")
    
#     return metrics

# def calculate_percentage_change(previous, current):
#     """Safe percentage change calculation"""
#     if previous is None or previous == 0:
#         return 0
#     return round(((current - previous) / previous) * 100, 2)

# def load_historical_data():
#     """Load historical data with validation"""
#     default_data = {"metrics": [], "alerts": []}
    
#     if not HISTORICAL_METRICS_PATH.exists():
#         return default_data
    
#     try:
#         with open(HISTORICAL_METRICS_PATH, 'r') as f:
#             content = f.read().strip()
#             if not content:
#                 return default_data
            
#             data = json.loads(content)
#             # Validate structure
#             if not isinstance(data, dict):
#                 return default_data
#             if "metrics" not in data:
#                 data["metrics"] = []
#             if "alerts" not in data:
#                 data["alerts"] = []
                
#             return data
            
#     except (json.JSONDecodeError, IOError) as e:
#         print(f"Error loading historical data: {e}")
#         return default_data

# def save_historical_data(current_metrics):
#     """Save metrics to historical data with proper comparison"""
#     try:
#         historical_data = load_historical_data()
#         previous_metrics = get_most_recent_comparable_metrics()
        
#         # Add current metrics
#         historical_data["metrics"].append(current_metrics)
        
#         # Calculate changes if we have previous metrics to compare with
#         if previous_metrics:
#             changes = {
#                 "new_diagnoses": calculate_percentage_change(
#                     previous_metrics["percent_new_diagnoses"],
#                     current_metrics["percent_new_diagnoses"]
#                 ),
#                 "bp_followup": calculate_percentage_change(
#                     previous_metrics["percent_bp_followup"],
#                     current_metrics["percent_bp_followup"]
#                 ),
#                 "bg_followup": calculate_percentage_change(
#                     previous_metrics["percent_bg_followup"],
#                     current_metrics["percent_bg_followup"]
#                 ),
#                 "bp_controlled": calculate_percentage_change(
#                     previous_metrics["percent_bp_controlled"],
#                     current_metrics["percent_bp_controlled"]
#                 )
#             }
            
#             current_metrics["changes"] = changes
            
#             # Create alert if performance declined
#             if current_metrics["performance_declined"]:
#                 alert = {
#                     "timestamp": current_metrics["timestamp"],
#                     "metrics": current_metrics.copy(),
#                     "changes": changes
#                 }
#                 historical_data["alerts"].append(alert)
        
#         # Trim data to maintain size limits
#         historical_data["metrics"] = historical_data["metrics"][-MAX_HISTORICAL_METRICS:]
#         historical_data["alerts"] = historical_data["alerts"][-MAX_HISTORICAL_ALERTS:]
        
#         # Save back to file
#         HISTORICAL_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
#         with open(HISTORICAL_METRICS_PATH, 'w') as f:
#             json.dump(historical_data, f, indent=2)
            
#         return current_metrics
        
#     except Exception as e:
#         print(f"Error saving historical data: {e}")
#         return None

# def main():
#     """Main monitoring workflow"""
#     # Calculate current metrics
#     current_metrics = calculate_monitoring_metrics()
    
#     # Save to historical data and get enhanced metrics with changes
#     enhanced_metrics = save_historical_data(current_metrics)
    
#     if enhanced_metrics:
#         return enhanced_metrics
#     return current_metrics

# if __name__ == "__main__":
#     results = main()
#     print(json.dumps(results, indent=2))

# from pathlib import Path
# import pandas as pd
# import json
# from datetime import datetime

# # Define paths
# DIAGNOSES_PATH = Path("data/raw/diagnoses.csv")
# BP_LOGS_PATH = Path("data/raw/bp_logs.csv")
# GLUCOSE_LOGS_PATH = Path("data/raw/glucose_logs.csv")
# PREVIOUS_METRICS_PATH = Path("data/previous_metrics.json")
# HISTORICAL_METRICS_PATH = Path("data/historical_metrics.json")

# # Read CSVs
# diagnoses_df = pd.read_csv(DIAGNOSES_PATH)
# bp_logs_df = pd.read_csv(BP_LOGS_PATH)
# glucose_logs_df = pd.read_csv(GLUCOSE_LOGS_PATH)

# # Core calculation function
# def calculate_monitoring_metrics(diagnoses_df, bp_logs_df, glucose_logs_df):
#     # Calculate percentages (with division by zero protection)
#     total_diagnosed = diagnoses_df["patient_track_id"].nunique()
#     new_diagnoses = diagnoses_df[
#         (diagnoses_df['diabetes_patient_type'] == 'Newly diagnosed') |
#         (diagnoses_df['htn_patient_type'] == 'Newly diagnosed')
#     ]["patient_track_id"].nunique()
    
#     bp_patients = bp_logs_df["patient_track_id"].nunique()
#     bp_followup_counts = bp_logs_df.groupby("patient_track_id").size()
#     bp_followup = bp_followup_counts[bp_followup_counts > 1].count()
    
#     bg_patients = glucose_logs_df["patient_track_id"].nunique()
#     bg_followup_counts = glucose_logs_df.groupby("patient_track_id").size()
#     bg_followup = bg_followup_counts[bg_followup_counts > 1].count()

#     # BP control metrics (systolic/diastolic)
#     bp_controlled = bp_logs_df.groupby("patient_track_id").agg({
#         'avg_systolic': 'mean',
#         'avg_diastolic': 'mean'
#     })
#     bp_controlled_count = len(bp_controlled[
#         (bp_controlled['avg_systolic'] < 140) & 
#         (bp_controlled['avg_diastolic'] < 90)
#     ])

#     # Convert numpy.bool_ to native Python bool
#     new_diag_violation = bool(new_diagnoses / total_diagnosed < 0.5) if total_diagnosed > 0 else True
#     bp_followup_violation = bool(bp_followup / bp_patients < 0.5) if bp_patients > 0 else True
#     bg_followup_violation = bool(bg_followup / bg_patients < 0.5) if bg_patients > 0 else True
#     bp_controlled_violation = bool(bp_controlled_count / bp_patients < 0.5) if bp_patients > 0 else True
    
#     return {
#         "percent_new_diagnoses": round((new_diagnoses / total_diagnosed * 100) if total_diagnosed > 0 else 0, 2),
#         "percent_bp_followup": round((bp_followup / bp_patients * 100) if bp_patients > 0 else 0, 2),
#         "percent_bg_followup": round((bg_followup / bg_patients * 100) if bg_patients > 0 else 0, 2),
#         "percent_bp_controlled": round((bp_controlled_count / bp_patients * 100) if bp_patients > 0 else 0, 2),
#         "performance_declined": new_diag_violation or bp_followup_violation or bg_followup_violation or bp_controlled_violation,
#         "timestamp": datetime.now().isoformat()
#     }

# def calculate_change_percentage(previous, current):
#     if previous == 0:
#         return 0 if current == 0 else 100
#     return round(((previous - current) / previous) * 100, 2)



# # Helper functions
# def calculate_change_percentage(previous, current):
#     return round(((current - previous) / previous * 100), 2) if previous != 0 else 0

# def load_previous_metrics():
#     default_metrics = {
#         "percent_new_diagnoses": 0,
#         "percent_bp_followup": 0,
#         "percent_bg_followup": 0,
#         "percent_bp_controlled": 0,
#         "timestamp": datetime.now().isoformat()
#     }
    
#     if not PREVIOUS_METRICS_PATH.exists():
#         return default_metrics
    
#     try:
#         with open(PREVIOUS_METRICS_PATH, 'r') as f:
#             content = f.read().strip()
#             if not content:
#                 return default_metrics
#             return json.loads(content)
#     except (json.JSONDecodeError, IOError):
#         return default_metrics
    
# # Load previous metrics
# previous_metrics = load_previous_metrics()

# metrics = calculate_monitoring_metrics(diagnoses_df, bp_logs_df, glucose_logs_df)

# # Calculate percentage drops
# drop_new_diagnoses = calculate_change_percentage(previous_metrics["percent_new_diagnoses"], metrics["percent_new_diagnoses"])
# drop_bp_followup = calculate_change_percentage(previous_metrics["percent_bp_followup"], metrics["percent_bp_followup"])
# drop_bg_followup = calculate_change_percentage(previous_metrics["percent_bg_followup"], metrics["percent_bg_followup"])
# drop_bp_controlled = calculate_change_percentage(previous_metrics["percent_bp_controlled"], metrics["percent_bp_controlled"])

# # Add to metrics output
# metrics.update({
#     "drop_new_diagnoses": drop_new_diagnoses,
#     "drop_bp_followup": drop_bp_followup,
#     "drop_bg_followup": drop_bg_followup,
#     "drop_bp_controlled": drop_bp_controlled
# })

# def load_historical_data():
#     default_data = {"metrics": [], "alerts": []}
    
#     if not HISTORICAL_METRICS_PATH.exists():
#         return default_data
    
#     try:
#         with open(HISTORICAL_METRICS_PATH, 'r') as f:
#             content = f.read().strip()
#             if not content:
#                 return default_data
#             return json.loads(content)
#     except (json.JSONDecodeError, IOError):
#         return default_data

# def save_current_metrics(metrics):
#     with open(PREVIOUS_METRICS_PATH, 'w') as f:
#         json.dump({
#             "percent_new_diagnoses": metrics["percent_new_diagnoses"],
#             "percent_bp_followup": metrics["percent_bp_followup"],
#             "percent_bg_followup": metrics["percent_bg_followup"],
#             "percent_bp_controlled": metrics["percent_bp_controlled"],
#             "timestamp": metrics["timestamp"]
#         }, f)
        
# def save_historical_metrics(previous, current):
#     try:
#         # Initialize default historical data structure
#         historical = {"metrics": [], "alerts": []}
        
#         # Load existing data if file exists and is not empty
#         if HISTORICAL_METRICS_PATH.exists():
#             try:
#                 with open(HISTORICAL_METRICS_PATH, 'r') as f:
#                     content = f.read().strip()
#                     if content:  # Only load if file is not empty
#                         historical = json.loads(content)
#             except (json.JSONDecodeError, IOError) as e:
#                 print(f"Warning: Failed to load historical data, starting fresh. Error: {e}")
        
#         # Ensure the loaded data has the correct structure
#         if not isinstance(historical, dict):
#             historical = {"metrics": [], "alerts": []}
#         if "metrics" not in historical:
#             historical["metrics"] = []
#         if "alerts" not in historical:
#             historical["alerts"] = []
        
#         # Add current metrics (ensure it's a copy to avoid reference issues)
#         historical["metrics"].append(current.copy())
        
#         # Check for threshold violations
#         if current["performance_declined"]:
#             alert_data = {
#                 "timestamp": current["timestamp"],
#                 "metrics": current.copy(),
#                 "changes": {
#                     "new_diagnoses": float(current["percent_new_diagnoses"]) - float(previous.get("percent_new_diagnoses", 0)),
#                     "bp_followup": float(current["percent_bp_followup"]) - float(previous.get("percent_bp_followup", 0)),
#                     "bg_followup": float(current["percent_bg_followup"]) - float(previous.get("percent_bg_followup", 0)),
#                     "bp_controlled": float(current["percent_bp_controlled"]) - float(previous.get("percent_bp_controlled", 0))
#                 }
#             }
#             historical["alerts"].append(alert_data)
        
#         # Trim old data
#         historical["metrics"] = historical["metrics"][-90:]
#         historical["alerts"] = historical["alerts"][-30:]
        
#         # Ensure directory exists
#         HISTORICAL_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        
#         # Save back with proper error handling
#         try:
#             with open(HISTORICAL_METRICS_PATH, 'w') as f:
#                 json.dump(historical, f, indent=2, ensure_ascii=False)
#         except IOError as e:
#             print(f"Error writing historical data file: {e}")
            
#     except Exception as e:
#         print(f"Error saving historical data: {e}")
#         raise  # Re-raise the exception if you want it to propagate

