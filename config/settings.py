# Simulation parameters
FREQUENCY = "hourly"  # or "daily"
NUM_PATIENTS = 500  # Number of patients to simulate
DAYS_TO_SIMULATE = 30
ANOMALY_RATE = 0.05  # 5% of records will be anomalies
# Simulation settings
REPEAT_PATIENT_RATE = 0.7  # 70% of patients will be repeat visits
MAX_VISITS_PER_REPEAT_PATIENT = 5  # Maximum number of visits per repeat patient


# Kenya Demographic and Health Survey 2022 Data
KDHS_2022 = {
    'hypertension': {
        'prevalence': {
            'F_15-49': 0.09,  # 9% of women
            'M_15-49': 0.03    # 3% of men
        },
        'treatment_rate': 0.32  # 32% on medication
    },
    'diabetes': {
        'prevalence': 0.01,  # 1% both genders
        'treatment_rate': {
            'F': 0.63,  # 63% women
            'M': 0.73    # 73% men
        }
    },
    'heart_disease': {
        'prevalence': 0.01,  # 1% both genders
        'treatment_rate': {
            'F': 0.43,  # 43% women
            'M': 0.30    # 30% men
        }
    },
    'mental_health': {
        'prevalence': {
            'F_15-49': 0.04,  # 4% women
            'M_15-49': 0.03    # 3% men
        },
        'treatment_rate': {
            'F': 0.27,  # 27% women
            'M': 0.21    # 21% men
        }
    }
}

# Age group adjustments
AGE_GROUP_RISK_FACTORS = {
    '15-49': {
        'hypertension_adj': 1.0,
        'diabetes_adj': 1.0
    },
    '50+': {
        'hypertension_adj': 2.5,  # 2.5x higher risk
        'diabetes_adj': 3.0
    }
}

# Normal ranges (mean, std dev)
HEALTH_METRICS = {
    "glucose": (100, 20),    # mg/dL
    "blood_pressure_systolic": (120, 10),  # mmHg
    "blood_pressure_diastolic": (80, 5),   # mmHg
    "heart_rate": (75, 8)     # BPM
}

# ALERT_THRESHOLDS = {
#     "glucose": 180,
#     "blood_pressure_systolic": 140,
#     "blood_pressure_diastolic": 90,
#     "heart_rate": 100
# }

# config/settings.py
ANOMALY_THRESHOLDS = {
    "glucose": {
        "critical_high": 300,
        "critical_low": 70,
        "warning_high": 180,
        "warning_low": 90
    },
    "blood_pressure": {
        "systolic": {
            "critical_high": 180,
            "warning_high": 140,
            "critical_low": 90,
            "warning_low": 100
        },
        "diastolic": {
            "critical_high": 120,
            "warning_high": 90,
            "critical_low": 60,
            "warning_low": 70
        }
    },
    "hba1c": {
        "critical_high": 9.0,
        "warning_high": 6.5
    },
    "pulse": {
        "critical_high": 120,
        "warning_high": 100,
        "critical_low": 40,
        "warning_low": 50
    },
    "bmi": {
        "critical_high": 35,
        "warning_high": 30,
        "critical_low": 16,
        "warning_low": 18.5
    }
}

# Database configuration
DATABASE_URL = "postgresql://postgres:1234@localhost/health_dashboard"

# # Other settings
# NUM_PATIENTS = 100  # Default number of patients to generate