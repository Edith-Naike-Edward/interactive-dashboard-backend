import pandas as pd

def preprocess_health_data(file_path: str):
    """
    Reads and preprocesses health data from a CSV file.
    """
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    # Drop rows with missing values
    df.dropna(inplace=True)

    # Normalize relevant columns
    columns_to_normalize = ["insulin", "height", "weight", "ap_hi", "ap_lo", "cholesterol", "gluc", "BMI"]
    for column in columns_to_normalize:
        if column in df.columns:
            # Scale the column values to a range between 0 and 1
            df[column] = (df[column] - df[column].min()) / (df[column].max() - df[column].min())

    # Convert categorical values (if applicable)
    if "gender" in df.columns:
        # Map gender values to numerical values
        df["gender"] = df["gender"].map({"Male": 0, "Female": 1})

    return df
