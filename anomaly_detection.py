import numpy as np

def detect_anomalies(data: list, threshold: float = 2.0):
    """
    Detects anomalies based on standard deviation.
    Any value beyond 'threshold' standard deviations from the mean is flagged as an anomaly.
    Model used: Univariate method based on standard deviation/ Simple Statistical Anomaly Detection (Z-score)
    """
    if not data:
        # Return an empty list if the input data is empty
        return []

    # Convert the input data list to a numpy array
    values = np.array(data)
    
    # Calculate the mean of the values
    mean = np.mean(values)
    
    # Calculate the standard deviation of the values
    std_dev = np.std(values)

    # Identify values that are beyond the threshold standard deviations from the mean
    anomalies = [v for v in values if abs(v - mean) > threshold * std_dev]
    
    # Return the list of anomalies
    return anomalies
