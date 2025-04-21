import pandas as pd
from config.settings import ANOMALY_THRESHOLDS


def detect_anomalies(health_data: dict) -> pd.DataFrame:
    """
    Detects anomalies across multiple health data tables.
    
    Args:
        health_data: Dictionary containing DataFrames for:
            - screenings: pd.DataFrame
            - bp_logs: pd.DataFrame
            - glucose_logs: pd.DataFrame
    
    Returns:
        DataFrame with all detected anomalies across all tables
    """
    anomalies = pd.DataFrame()
    
    # Check each table if it exists in the input
    if 'screenings' in health_data:
        screening_anomalies = _detect_screening_anomalies(health_data['screenings'])
        anomalies = pd.concat([anomalies, screening_anomalies], ignore_index=True)
    
    if 'bp_logs' in health_data:
        bp_anomalies = _detect_bp_anomalies(health_data['bp_logs'])
        anomalies = pd.concat([anomalies, bp_anomalies], ignore_index=True)
    
    if 'glucose_logs' in health_data:
        glucose_anomalies = _detect_glucose_anomalies(health_data['glucose_logs'])
        anomalies = pd.concat([anomalies, glucose_anomalies], ignore_index=True)
    
    # Add severity ranking
    if not anomalies.empty:
        anomalies['severity'] = anomalies['alert_type'].apply(_get_severity_score)
        anomalies = anomalies.sort_values(['severity', 'timestamp'], ascending=[False, True])
    
    return anomalies

def _detect_screening_anomalies(screenings: pd.DataFrame) -> pd.DataFrame:
    """Detects anomalies in screening data"""
    anomalies = screenings[
        (screenings["glucose_value"] > ANOMALY_THRESHOLDS["glucose"]["critical_high"]) |
        (screenings["avg_systolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["systolic"]["critical_high"]) |
        (screenings["avg_diastolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["diastolic"]["critical_high"]) |
        (screenings["phq4_risk_level"].isin(["Moderate", "Severe"])) |
        (screenings["cvd_risk_level"] == "High")
    ].copy()
    
    if not anomalies.empty:
        anomalies["alert_type"] = anomalies.apply(_classify_screening_alert, axis=1)
        anomalies["timestamp"] = pd.to_datetime(anomalies["created_at"])
        anomalies["source_table"] = "screenings"
    
    return anomalies

def _detect_bp_anomalies(bp_logs: pd.DataFrame) -> pd.DataFrame:
    """Detects anomalies in blood pressure logs"""
    anomalies = bp_logs[
        (bp_logs["avg_systolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["systolic"]["critical_high"]) |
        (bp_logs["avg_diastolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["diastolic"]["critical_high"]) |
        (bp_logs["avg_systolic"] < ANOMALY_THRESHOLDS["blood_pressure"]["systolic"]["critical_low"]) |
        (bp_logs["avg_diastolic"] < ANOMALY_THRESHOLDS["blood_pressure"]["diastolic"]["critical_low"])
    ].copy()
    
    if not anomalies.empty:
        anomalies["alert_type"] = anomalies.apply(_classify_bp_alert, axis=1)
        anomalies["timestamp"] = pd.to_datetime(anomalies["created_at"])
        anomalies["source_table"] = "bp_logs"
    
    return anomalies

def _detect_glucose_anomalies(glucose_logs: pd.DataFrame) -> pd.DataFrame:
    """Detects anomalies in glucose logs"""
    anomalies = glucose_logs[
        (glucose_logs["glucose_value"] > ANOMALY_THRESHOLDS["glucose"]["critical_high"]) |
        (glucose_logs["glucose_value"] < ANOMALY_THRESHOLDS["glucose"]["critical_low"]) |
        (glucose_logs["hba1c"] > ANOMALY_THRESHOLDS["hba1c"]["critical_high"])
    ].copy()
    
    if not anomalies.empty:
        anomalies["alert_type"] = anomalies.apply(_classify_glucose_alert, axis=1)
        anomalies["timestamp"] = pd.to_datetime(anomalies["created_at"])
        anomalies["source_table"] = "glucose_logs"
    
    return anomalies

def _classify_screening_alert(row):
    """Classifies alerts from screening data"""
    if row["glucose_value"] > ANOMALY_THRESHOLDS["glucose"]["critical_high"]:
        return "SEVERE_HYPERGLYCEMIA"
    elif row["avg_systolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["systolic"]["critical_high"]:
        return "HYPERTENSIVE_CRISIS"
    elif row["avg_diastolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["diastolic"]["critical_high"]:
        return "HYPERTENSIVE_CRISIS"
    elif row["phq4_risk_level"] in ["Moderate", "Severe"]:
        return "MENTAL_HEALTH_CONCERN"
    elif row["cvd_risk_level"] == "High":
        return "HIGH_CVD_RISK"
    else:
        return "WARNING"

def _classify_bp_alert(row):
    """Classifies alerts from blood pressure logs"""
    if row["avg_systolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["systolic"]["critical_high"]:
        return "HYPERTENSIVE_CRISIS"
    elif row["avg_diastolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["diastolic"]["critical_high"]:
        return "HYPERTENSIVE_CRISIS"
    elif row["avg_systolic"] < ANOMALY_THRESHOLDS["blood_pressure"]["systolic"]["critical_low"]:
        return "HYPOTENSIVE_CRISIS"
    elif row["avg_diastolic"] < ANOMALY_THRESHOLDS["blood_pressure"]["diastolic"]["critical_low"]:
        return "HYPOTENSIVE_CRISIS"
    else:
        return "WARNING"

def _classify_glucose_alert(row):
    """Classifies alerts from glucose logs"""
    if row["glucose_value"] > ANOMALY_THRESHOLDS["glucose"]["critical_high"]:
        return "SEVERE_HYPERGLYCEMIA"
    elif row["glucose_value"] < ANOMALY_THRESHOLDS["glucose"]["critical_low"]:
        return "HYPOGLYCEMIA"
    elif row["hba1c"] > ANOMALY_THRESHOLDS["hba1c"]["critical_high"]:
        return "POOR_GLYCEMIC_CONTROL"
    else:
        return "WARNING"

def _get_severity_score(alert_type):
    """Assigns severity score to prioritize critical alerts"""
    severity_map = {
        "SEVERE_HYPERGLYCEMIA": 4,
        "HYPOGLYCEMIA": 4,
        "HYPERTENSIVE_CRISIS": 4,
        "HYPOTENSIVE_CRISIS": 4,
        "POOR_GLYCEMIC_CONTROL": 3,
        "HIGH_CVD_RISK": 3,
        "MENTAL_HEALTH_CONCERN": 2,
        "WARNING": 1
    }
    return severity_map.get(alert_type, 0)