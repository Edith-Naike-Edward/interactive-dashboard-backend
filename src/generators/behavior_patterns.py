import numpy as np
from datetime import time
from config.settings import FREQUENCY

def add_behavioral_patterns(metrics_df, patients_df):
    """Enhance realism with physiological patterns"""
    
    # 1. Post-meal glucose spikes (2 hours after typical meal times)
    if FREQUENCY == "hourly":
        metrics_df["glucose"] = metrics_df.apply(
            lambda row: row["glucose"] * meal_time_adjustment(row["timestamp"]), 
            axis=1
        )
    
    # 2. BP/heart rate variations by age
    metrics_df = metrics_df.merge(
        patients_df[["patient_id", "is_regular_smoker"]], 
        on="patient_id"
    )
    
    metrics_df["blood_pressure_systolic"] += metrics_df["age"].apply(
        lambda age: (age - 40) * 0.2  # +1 mmHg per 5 years over 40
    )
    
    metrics_df["heart_rate"] += metrics_df.apply(
        lambda row: 5 if row["is_regular_smoker"] else 0, 
        axis=1
    )
    
    # 3. Circadian rhythms
    metrics_df["time_of_day"] = metrics_df["timestamp"].dt.hour
    metrics_df["blood_pressure_systolic"] += metrics_df["time_of_day"].apply(
        lambda h: 3 * np.sin((h - 14)/12 * np.pi)  # Peaks in late afternoon
    )
    metrics_df["heart_rate"] += metrics_df["time_of_day"].apply(
        lambda h: 5 * np.sin((h - 14)/12 * np.pi)  # Follows BP pattern
    )
    
    return metrics_df.drop(columns=["time_of_day", "age", "is_regular_smoker"])

def meal_time_adjustment(timestamp):
    """Apply glucose spikes after meals"""
    hour = timestamp.hour
    # Meal times: 8-9am, 1-2pm, 7-8pm
    if 10 <= hour <= 11:    # 2hrs after breakfast
        return 1 + np.random.uniform(0.1, 0.3)
    elif 15 <= hour <= 16:  # 2hrs after lunch
        return 1 + np.random.uniform(0.15, 0.25)
    elif 21 <= hour <= 22:  # 2hrs after dinner
        return 1 + np.random.uniform(0.1, 0.2)
    elif 2 <= hour <= 5:    # Dawn phenomenon
        return 1 + np.random.uniform(0.05, 0.15)
    return 1