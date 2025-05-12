from pathlib import Path
import pandas as pd
import json
from datetime import datetime

# Define paths
DIAGNOSES_PATH = Path("data/raw/diagnoses.csv")
BP_LOGS_PATH = Path("data/raw/bp_logs.csv")
GLUCOSE_LOGS_PATH = Path("data/raw/glucose_logs.csv")
PREVIOUS_METRICS_PATH = Path("data/previous_metrics.json")
HISTORICAL_METRICS_PATH = Path("data/historical_metrics.json")

# Read CSVs
diagnoses_df = pd.read_csv(DIAGNOSES_PATH)
bp_logs_df = pd.read_csv(BP_LOGS_PATH)
glucose_logs_df = pd.read_csv(GLUCOSE_LOGS_PATH)

# Core calculation function
def calculate_monitoring_metrics(diagnoses_df, bp_logs_df, glucose_logs_df):
    # Calculate percentages (with division by zero protection)
    total_diagnosed = diagnoses_df["patient_track_id"].nunique()
    new_diagnoses = diagnoses_df[
        (diagnoses_df['diabetes_patient_type'] == 'Newly diagnosed') |
        (diagnoses_df['htn_patient_type'] == 'Newly diagnosed')
    ]["patient_track_id"].nunique()
    
    bp_patients = bp_logs_df["patient_track_id"].nunique()
    bp_followup_counts = bp_logs_df.groupby("patient_track_id").size()
    bp_followup = bp_followup_counts[bp_followup_counts > 1].count()
    
    bg_patients = glucose_logs_df["patient_track_id"].nunique()
    bg_followup_counts = glucose_logs_df.groupby("patient_track_id").size()
    bg_followup = bg_followup_counts[bg_followup_counts > 1].count()

    # BP control metrics (systolic/diastolic)
    bp_controlled = bp_logs_df.groupby("patient_track_id").agg({
        'avg_systolic': 'mean',
        'avg_diastolic': 'mean'
    })
    bp_controlled_count = len(bp_controlled[
        (bp_controlled['avg_systolic'] < 140) & 
        (bp_controlled['avg_diastolic'] < 90)
    ])

    # Convert numpy.bool_ to native Python bool
    new_diag_violation = bool(new_diagnoses / total_diagnosed < 0.5) if total_diagnosed > 0 else True
    bp_followup_violation = bool(bp_followup / bp_patients < 0.5) if bp_patients > 0 else True
    bg_followup_violation = bool(bg_followup / bg_patients < 0.5) if bg_patients > 0 else True
    bp_controlled_violation = bool(bp_controlled_count / bp_patients < 0.5) if bp_patients > 0 else True
    
    return {
        "percent_new_diagnoses": round((new_diagnoses / total_diagnosed * 100) if total_diagnosed > 0 else 0, 2),
        "percent_bp_followup": round((bp_followup / bp_patients * 100) if bp_patients > 0 else 0, 2),
        "percent_bg_followup": round((bg_followup / bg_patients * 100) if bg_patients > 0 else 0, 2),
        "percent_bp_controlled": round((bp_controlled_count / bp_patients * 100) if bp_patients > 0 else 0, 2),
        "performance_declined": new_diag_violation or bp_followup_violation or bg_followup_violation or bp_controlled_violation,
        "timestamp": datetime.now().isoformat()
    }
    

# Helper functions
def calculate_change_percentage(previous, current):
    return round(((current - previous) / previous * 100), 2) if previous != 0 else 0

def load_previous_metrics():
    default_metrics = {
        "percent_new_diagnoses": 0,
        "percent_bp_followup": 0,
        "percent_bg_followup": 0,
        "percent_bp_controlled": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    if not PREVIOUS_METRICS_PATH.exists():
        return default_metrics
    
    try:
        with open(PREVIOUS_METRICS_PATH, 'r') as f:
            content = f.read().strip()
            if not content:
                return default_metrics
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return default_metrics

def load_historical_data():
    default_data = {"metrics": [], "alerts": []}
    
    if not HISTORICAL_METRICS_PATH.exists():
        return default_data
    
    try:
        with open(HISTORICAL_METRICS_PATH, 'r') as f:
            content = f.read().strip()
            if not content:
                return default_data
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return default_data

def save_current_metrics(metrics):
    with open(PREVIOUS_METRICS_PATH, 'w') as f:
        json.dump({
            "percent_new_diagnoses": metrics["percent_new_diagnoses"],
            "percent_bp_followup": metrics["percent_bp_followup"],
            "percent_bg_followup": metrics["percent_bg_followup"],
            "percent_bp_controlled": metrics["percent_bp_controlled"],
            "timestamp": metrics["timestamp"]
        }, f)
        
def save_historical_metrics(previous, current):
    try:
        # Initialize default historical data structure
        historical = {"metrics": [], "alerts": []}
        
        # Load existing data if file exists and is not empty
        if HISTORICAL_METRICS_PATH.exists():
            try:
                with open(HISTORICAL_METRICS_PATH, 'r') as f:
                    content = f.read().strip()
                    if content:  # Only load if file is not empty
                        historical = json.loads(content)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load historical data, starting fresh. Error: {e}")
        
        # Ensure the loaded data has the correct structure
        if not isinstance(historical, dict):
            historical = {"metrics": [], "alerts": []}
        if "metrics" not in historical:
            historical["metrics"] = []
        if "alerts" not in historical:
            historical["alerts"] = []
        
        # Add current metrics (ensure it's a copy to avoid reference issues)
        historical["metrics"].append(current.copy())
        
        # Check for threshold violations
        if current["performance_declined"]:
            alert_data = {
                "timestamp": current["timestamp"],
                "metrics": current.copy(),
                "changes": {
                    "new_diagnoses": float(current["percent_new_diagnoses"]) - float(previous.get("percent_new_diagnoses", 0)),
                    "bp_followup": float(current["percent_bp_followup"]) - float(previous.get("percent_bp_followup", 0)),
                    "bg_followup": float(current["percent_bg_followup"]) - float(previous.get("percent_bg_followup", 0)),
                    "bp_controlled": float(current["percent_bp_controlled"]) - float(previous.get("percent_bp_controlled", 0))
                }
            }
            historical["alerts"].append(alert_data)
        
        # Trim old data
        historical["metrics"] = historical["metrics"][-90:]
        historical["alerts"] = historical["alerts"][-30:]
        
        # Ensure directory exists
        HISTORICAL_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Save back with proper error handling
        try:
            with open(HISTORICAL_METRICS_PATH, 'w') as f:
                json.dump(historical, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error writing historical data file: {e}")
            
    except Exception as e:
        print(f"Error saving historical data: {e}")
        raise  # Re-raise the exception if you want it to propagate

