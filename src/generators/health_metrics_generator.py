import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config.settings import HEALTH_METRICS, ANOMALY_RATE, FREQUENCY
from .behavior_patterns import add_behavioral_patterns 
# import screeninglog_generator

def generate_health_metrics(patients_df, start_date=None, days=30, frequency="hourly"):
    """Generate time-series health metrics for each patient"""
    if not start_date:
        start_date = datetime.now() - timedelta(days=days)
    
    records = []
    for _, patient in patients_df.iterrows():
        # Generate timestamps (hourly/daily)
        timestamps = pd.date_range(
            start=start_date,
            periods=days*(24 if frequency == "hourly" else 1),
            freq="H" if frequency == "hourly" else "D"
        )
        
        # Get patient-specific baseline adjustments
        age = (datetime.now() - datetime.strptime(patient["date_of_birth"], "%Y-%m-%d")).days // 365
        is_diabetic = patient.get("is_before_diabetes_diagnosis", False)
        is_hypertensive = patient.get("is_before_htn_diagnosis", False)
        
        for ts in timestamps:
            record = {
                "patient_id": patient["patient_id"],
                "timestamp": ts,
                "age": age
            }
            
            # Generate each metric with possible anomalies
            for metric, (mean, std) in HEALTH_METRICS.items():
                # Adjust baselines for conditions
                if metric == "glucose":
                    adj_mean = mean + (20 if is_diabetic else 0)
                elif "blood_pressure" in metric:
                    adj_mean = mean + (15 if is_hypertensive else 0)
                else:
                    adj_mean = mean
                
                value = np.random.normal(adj_mean, std)
                
                # Inject anomalies
                if np.random.random() < ANOMALY_RATE:
                    if metric == "glucose":
                        value = min(500, max(70, value * 1.8))  # Hyperglycemia
                    elif "blood_pressure" in metric:
                        value = min(220 if "systolic" in metric else 120, 
                                   value * 1.4)  # Hypertensive crisis
                    elif metric == "heart_rate":
                        value = value * (1.5 if np.random.random() > 0.5 else 0.7)  # Tachy/Bradycardia
                
                record[metric] = round(value, 1)
            
            records.append(record)
    
    metrics_df = pd.DataFrame(records)
    return add_behavioral_patterns(metrics_df, patients_df)