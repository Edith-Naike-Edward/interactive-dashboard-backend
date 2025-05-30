# anomaly_detector.py
import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from config.settings import ANOMALY_THRESHOLDS

def detect_anomalies(health_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Enhanced anomaly detection across all health data tables with additional checks.
    
    Args:
        health_data: Dictionary containing DataFrames for:
            - screenings
            - bp_logs
            - glucose_logs
            - patient_diagnosis
            - patient_lifestyle
            - patient_medical_compliance
            - patient_visits
            - patient_medical_reviews
    
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
    
    if 'patient_diagnosis' in health_data:
        diagnosis_anomalies = _detect_diagnosis_anomalies(health_data['patient_diagnosis'])
        anomalies = pd.concat([anomalies, diagnosis_anomalies], ignore_index=True)
    
    if 'patient_lifestyle' in health_data:
        lifestyle_anomalies = _detect_lifestyle_anomalies(health_data['patient_lifestyle'])
        anomalies = pd.concat([anomalies, lifestyle_anomalies], ignore_index=True)
    
    if 'patient_medical_compliance' in health_data:
        compliance_anomalies = _detect_compliance_anomalies(health_data['patient_medical_compliance'])
        anomalies = pd.concat([anomalies, compliance_anomalies], ignore_index=True)
    
    if 'patient_visits' in health_data:
        visit_anomalies = _detect_visit_anomalies(health_data['patient_visits'])
        anomalies = pd.concat([anomalies, visit_anomalies], ignore_index=True)
    
    if 'patient_medical_reviews' in health_data:
        review_anomalies = _detect_medical_review_anomalies(health_data['patient_medical_reviews'])
        anomalies = pd.concat([anomalies, review_anomalies], ignore_index=True)
    
    # Add severity ranking and additional metadata
    if not anomalies.empty:
        anomalies['severity'] = anomalies['alert_type'].apply(_get_severity_score)
        anomalies['timestamp'] = pd.to_datetime(anomalies.get('timestamp', anomalies.get('created_at', datetime.now())))
        anomalies = anomalies.sort_values(['severity', 'timestamp'], ascending=[False, True])
        anomalies['patient_id'] = anomalies.get('patient_id', '')
        anomalies['patient_name'] = anomalies.apply(
            lambda row: f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
            axis=1
        )
        # Add human-readable descriptions
        anomalies['description'] = anomalies['alert_type'].apply(_get_alert_description)
    
    return anomalies


def load_health_data_from_csv(data_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Loads health data from CSV files in the specified directory.

    Args:
        data_dir: Path to the directory containing the CSV files.

    Returns:
        A dictionary of DataFrames with keys:
            - screenings
            - bp_logs
            - glucose_logs
            - patient_diagnosis
            - patient_lifestyle
            - patient_medical_compliance
            - patient_visits
            - patient_medical_reviews
            - patients
            - users
    """
    filenames = {
        "screenings": "screenings.csv",
        "bp_logs": "bp_logs.csv",
        "glucose_logs": "glucose_logs.csv",
        "patient_diagnosis": "patient_diagnosis.csv",
        "patient_lifestyle": "patient_lifestyle.csv",
        "patient_medical_compliance": "patient_medical_compliance.csv",
        "patient_visits": "patient_visits.csv",
        "patient_medical_reviews": "patient_medical_reviews.csv",
        "patients": "patients.csv",
        "users": "users.csv",
    }

    data = {}
    for key, filename in filenames.items():
        path = os.path.join(data_dir, filename)
        try:
            df = pd.read_csv(path)
            data[key] = df
        except FileNotFoundError:
            print(f"Warning: {filename} not found in {data_dir}")
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    
    return data

def _get_alert_description(alert_type: str) -> str:
    """Returns human-readable descriptions for each alert type"""
    descriptions = {
        "SEVERE_HYPERGLYCEMIA": "Severely high glucose level detected",
        "HYPOGLYCEMIA": "Dangerously low glucose level detected",
        "HYPERTENSIVE_CRISIS": "Severely high blood pressure detected",
        "HYPOTENSIVE_CRISIS": "Dangerously low blood pressure detected",
        "TACHYCARDIA": "Abnormally high heart rate detected",
        "BRADYCARDIA": "Abnormally low heart rate detected",
        "POOR_GLYCEMIC_CONTROL": "Long-term blood sugar control is poor",
        "HIGH_CVD_RISK": "Patient has high cardiovascular disease risk",
        "SEVERE_OBESITY": "Patient BMI indicates severe obesity",
        "SEVERE_UNDERWEIGHT": "Patient BMI indicates severe underweight",
        "MENTAL_HEALTH_CONCERN": "Patient shows signs of mental health concern",
        "UNDIAGNOSED_HIGH_RISK": "Patient shows high risk factors but remains undiagnosed",
        "UNCONTROLLED_CONDITION": "Patient's condition appears uncontrolled",
        "HIGH_RISK_LIFESTYLE": "Patient engages in high-risk lifestyle behaviors",
        "MEDICATION_NON_COMPLIANCE": "Patient is non-compliant with medications",
        "FREQUENT_VISITOR": "Patient has unusually high number of visits",
        "CONCERNING_CLINICAL_NOTES": "Clinical notes contain concerning language",
        "ELEVATED_FASTING_GLUCOSE": "Elevated fasting glucose level detected",
        "ELEVATED_RANDOM_GLUCOSE": "Elevated random glucose level detected",
        "WARNING": "General health warning"
    }
    return descriptions.get(alert_type, "Potential health concern detected")

# Existing detection functions (kept from original code)
def _detect_screening_anomalies(screenings: pd.DataFrame) -> pd.DataFrame:
    """Detects anomalies in screening data with additional checks"""
    anomalies = screenings[
        (screenings["glucose_value"] > ANOMALY_THRESHOLDS["glucose"]["critical_high"]) |
        (screenings["avg_systolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["systolic"]["critical_high"]) |
        (screenings["avg_diastolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["diastolic"]["critical_high"]) |
        (screenings["phq4_risk_level"].isin(["Moderate", "Severe"])) |
        (screenings["cvd_risk_level"] == "High") |
        (screenings["bmi"] > ANOMALY_THRESHOLDS["bmi"]["critical_high"]) |
        (screenings["bmi"] < ANOMALY_THRESHOLDS["bmi"]["critical_low"]) |
        (screenings["avg_pulse"] > ANOMALY_THRESHOLDS["pulse"]["critical_high"]) |
        (screenings["avg_pulse"] < ANOMALY_THRESHOLDS["pulse"]["critical_low"])
    ].copy()
    
    if not anomalies.empty:
        anomalies["alert_type"] = anomalies.apply(_classify_screening_alert, axis=1)
        anomalies["timestamp"] = pd.to_datetime(anomalies["created_at"])
        anomalies["source_table"] = "screenings"
    
    return anomalies

def _detect_bp_anomalies(bp_logs: pd.DataFrame) -> pd.DataFrame:
    """Detects anomalies in blood pressure logs with additional checks"""
    anomalies = bp_logs[
        (bp_logs["avg_systolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["systolic"]["critical_high"]) |
        (bp_logs["avg_diastolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["diastolic"]["critical_high"]) |
        (bp_logs["avg_systolic"] < ANOMALY_THRESHOLDS["blood_pressure"]["systolic"]["critical_low"]) |
        (bp_logs["avg_diastolic"] < ANOMALY_THRESHOLDS["blood_pressure"]["diastolic"]["critical_low"]) |
        (bp_logs["avg_pulse"] > ANOMALY_THRESHOLDS["pulse"]["critical_high"]) |
        (bp_logs["avg_pulse"] < ANOMALY_THRESHOLDS["pulse"]["critical_low"]) |
        (bp_logs["bmi"] > ANOMALY_THRESHOLDS["bmi"]["critical_high"]) |
        (bp_logs["bmi"] < ANOMALY_THRESHOLDS["bmi"]["critical_low"])
    ].copy()
    
    if not anomalies.empty:
        anomalies["alert_type"] = anomalies.apply(_classify_bp_alert, axis=1)
        anomalies["timestamp"] = pd.to_datetime(anomalies["created_at"])
        anomalies["source_table"] = "bp_logs"
    
    return anomalies

def _detect_glucose_anomalies(glucose_logs: pd.DataFrame) -> pd.DataFrame:
    """Detects anomalies in glucose logs with additional checks"""
    anomalies = glucose_logs[
        (glucose_logs["glucose_value"] > ANOMALY_THRESHOLDS["glucose"]["critical_high"]) |
        (glucose_logs["glucose_value"] < ANOMALY_THRESHOLDS["glucose"]["critical_low"]) |
        (glucose_logs["hba1c"] > ANOMALY_THRESHOLDS["hba1c"]["critical_high"]) |
        ((glucose_logs["glucose_type"] == "fasting") & 
         (glucose_logs["glucose_value"] > ANOMALY_THRESHOLDS["glucose"]["warning_high"])) |
        ((glucose_logs["glucose_type"] == "random") & 
         (glucose_logs["glucose_value"] > ANOMALY_THRESHOLDS["glucose"]["warning_high"] * 1.2))
    ].copy()
    
    if not anomalies.empty:
        anomalies["alert_type"] = anomalies.apply(_classify_glucose_alert, axis=1)
        anomalies["timestamp"] = pd.to_datetime(anomalies["glucose_date_time"])
        anomalies["source_table"] = "glucose_logs"
    
    return anomalies

# New detection functions for additional tables
def _detect_diagnosis_anomalies(diagnosis: pd.DataFrame) -> pd.DataFrame:
    """Detects anomalies in patient diagnosis data"""
    anomalies = pd.DataFrame()
    
    # Check for undiagnosed but high-risk patients
    if 'is_diabetes_diagnosis' in diagnosis.columns and 'is_htn_diagnosis' in diagnosis.columns:
        undiagnosed = diagnosis[
            (diagnosis["is_diabetes_diagnosis"] == False) & 
            (diagnosis["is_htn_diagnosis"] == False) &
            (diagnosis["diabetes_diagnosis"].notna() | 
             diagnosis["htn_patient_type"].notna())
        ].copy()
        
        if not undiagnosed.empty:
            undiagnosed["alert_type"] = "UNDIAGNOSED_HIGH_RISK"
            undiagnosed["timestamp"] = pd.to_datetime(undiagnosed["created_at"])
            undiagnosed["source_table"] = "patient_diagnosis"
            anomalies = pd.concat([anomalies, undiagnosed])
    
    # Check for uncontrolled conditions
    controlled_anomalies = diagnosis[
        (diagnosis["diabetes_diag_controlled_type"] == "Uncontrolled") |
        (diagnosis["htn_patient_type"] == "Uncontrolled")
    ].copy()
    
    if not controlled_anomalies.empty:
        controlled_anomalies["alert_type"] = "UNCONTROLLED_CONDITION"
        controlled_anomalies["timestamp"] = pd.to_datetime(controlled_anomalies["created_at"])
        controlled_anomalies["source_table"] = "patient_diagnosis"
        anomalies = pd.concat([anomalies, controlled_anomalies])
    
    return anomalies

def _detect_lifestyle_anomalies(lifestyle: pd.DataFrame) -> pd.DataFrame:
    """Detects anomalies in patient lifestyle data"""
    high_risk_behaviors = [
        "Smoking", "Alcohol", "Sedentary", 
        "High salt diet", "High sugar diet"
    ]
    
    anomalies = lifestyle[
        (lifestyle["lifestyle_name"].isin(high_risk_behaviors)) &
        (lifestyle["lifestyle_answer"] == "Yes")
    ].copy()
    
    if not anomalies.empty:
        anomalies["alert_type"] = "HIGH_RISK_LIFESTYLE"
        anomalies["timestamp"] = pd.to_datetime(anomalies["created_at"])
        anomalies["source_table"] = "patient_lifestyle"
    
    return anomalies

def _detect_compliance_anomalies(compliance: pd.DataFrame) -> pd.DataFrame:
    """Detects anomalies in medical compliance data"""
    non_compliant = compliance[
        (compliance["compliance_name"] == "Medication Adherence") &
        (compliance["other_compliance"].str.contains("Missed", na=False))
    ].copy()
    
    if not non_compliant.empty:
        non_compliant["alert_type"] = "MEDICATION_NON_COMPLIANCE"
        non_compliant["timestamp"] = pd.to_datetime(non_compliant["created_at"])
        non_compliant["source_table"] = "patient_medical_compliance"
    
    return non_compliant

def _detect_visit_anomalies(visits: pd.DataFrame) -> pd.DataFrame:
    """Detects anomalies in patient visit patterns"""
    # Convert to datetime if not already
    visits['visit_date'] = pd.to_datetime(visits['visit_date'])
    
    # Group by patient and count visits
    visit_counts = visits.groupby('patient_id').size().reset_index(name='visit_count')
    
    # Find frequent visitors (more than 3 visits in 30 days)
    frequent_visitors = visit_counts[visit_counts['visit_count'] > 3]
    
    if not frequent_visitors.empty:
        frequent_visitors["alert_type"] = "FREQUENT_VISITOR"
        frequent_visitors["timestamp"] = datetime.now()
        frequent_visitors["source_table"] = "patient_visits"
    
    return frequent_visitors

def _detect_medical_review_anomalies(reviews: pd.DataFrame) -> pd.DataFrame:
    """Detects anomalies in medical review notes"""
    # Look for concerning phrases in clinical notes
    concerning_phrases = [
        "worsening", "deteriorat", "emergency", "urgent",
        "severe pain", "uncontrolled", "non-compliant"
    ]
    
    anomalies = reviews[
        reviews["clinical_note"].str.contains('|'.join(concerning_phrases), na=False)
    ].copy()
    
    if not anomalies.empty:
        anomalies["alert_type"] = "CONCERNING_CLINICAL_NOTES"
        anomalies["timestamp"] = pd.to_datetime(anomalies["created_at"])
        anomalies["source_table"] = "patient_medical_reviews"
    
    return anomalies

# Enhanced alert classification
def _classify_screening_alert(row):
    """Classifies alerts from screening data with additional checks"""
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
    elif row["bmi"] > ANOMALY_THRESHOLDS["bmi"]["critical_high"]:
        return "SEVERE_OBESITY"
    elif row["bmi"] < ANOMALY_THRESHOLDS["bmi"]["critical_low"]:
        return "SEVERE_UNDERWEIGHT"
    elif row["avg_pulse"] > ANOMALY_THRESHOLDS["pulse"]["critical_high"]:
        return "TACHYCARDIA"
    elif row["avg_pulse"] < ANOMALY_THRESHOLDS["pulse"]["critical_low"]:
        return "BRADYCARDIA"
    else:
        return "WARNING"

def _classify_bp_alert(row):
    """Classifies alerts from blood pressure logs with additional checks"""
    if row["avg_systolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["systolic"]["critical_high"]:
        return "HYPERTENSIVE_CRISIS"
    elif row["avg_diastolic"] > ANOMALY_THRESHOLDS["blood_pressure"]["diastolic"]["critical_high"]:
        return "HYPERTENSIVE_CRISIS"
    elif row["avg_systolic"] < ANOMALY_THRESHOLDS["blood_pressure"]["systolic"]["critical_low"]:
        return "HYPOTENSIVE_CRISIS"
    elif row["avg_diastolic"] < ANOMALY_THRESHOLDS["blood_pressure"]["diastolic"]["critical_low"]:
        return "HYPOTENSIVE_CRISIS"
    elif row["avg_pulse"] > ANOMALY_THRESHOLDS["pulse"]["critical_high"]:
        return "TACHYCARDIA"
    elif row["avg_pulse"] < ANOMALY_THRESHOLDS["pulse"]["critical_low"]:
        return "BRADYCARDIA"
    elif row["bmi"] > ANOMALY_THRESHOLDS["bmi"]["critical_high"]:
        return "SEVERE_OBESITY"
    elif row["bmi"] < ANOMALY_THRESHOLDS["bmi"]["critical_low"]:
        return "SEVERE_UNDERWEIGHT"
    else:
        return "WARNING"

def _classify_glucose_alert(row):
    """Classifies alerts from glucose logs with additional checks"""
    if row["glucose_value"] > ANOMALY_THRESHOLDS["glucose"]["critical_high"]:
        return "SEVERE_HYPERGLYCEMIA"
    elif row["glucose_value"] < ANOMALY_THRESHOLDS["glucose"]["critical_low"]:
        return "HYPOGLYCEMIA"
    elif row["hba1c"] > ANOMALY_THRESHOLDS["hba1c"]["critical_high"]:
        return "POOR_GLYCEMIC_CONTROL"
    elif (row["glucose_type"] == "fasting") and (row["glucose_value"] > ANOMALY_THRESHOLDS["glucose"]["warning_high"]):
        return "ELEVATED_FASTING_GLUCOSE"
    elif (row["glucose_type"] == "random") and (row["glucose_value"] > ANOMALY_THRESHOLDS["glucose"]["warning_high"] * 1.2):
        return "ELEVATED_RANDOM_GLUCOSE"
    else:
        return "WARNING"

def _get_severity_score(alert_type):
    """Enhanced severity scoring with additional alert types"""
    severity_map = {
        "SEVERE_HYPERGLYCEMIA": 5,
        "HYPOGLYCEMIA": 5,
        "HYPERTENSIVE_CRISIS": 5,
        "HYPOTENSIVE_CRISIS": 5,
        "TACHYCARDIA": 4,
        "BRADYCARDIA": 4,
        "POOR_GLYCEMIC_CONTROL": 4,
        "HIGH_CVD_RISK": 4,
        "SEVERE_OBESITY": 3,
        "SEVERE_UNDERWEIGHT": 3,
        "MENTAL_HEALTH_CONCERN": 3,
        "UNDIAGNOSED_HIGH_RISK": 3,
        "UNCONTROLLED_CONDITION": 3,
        "HIGH_RISK_LIFESTYLE": 2,
        "MEDICATION_NON_COMPLIANCE": 2,
        "FREQUENT_VISITOR": 2,
        "CONCERNING_CLINICAL_NOTES": 2,
        "ELEVATED_FASTING_GLUCOSE": 2,
        "ELEVATED_RANDOM_GLUCOSE": 2,
        "WARNING": 1
    }
    return severity_map.get(alert_type, 0)
