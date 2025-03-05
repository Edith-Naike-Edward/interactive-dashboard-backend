from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from sklearn.linear_model import LinearRegression
import numpy as np

router = APIRouter()

# Dependency: Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def predict_trend(data: list):
    """
    Predict future health trends using Linear Regression for trend prediction.
    """
    if len(data) < 2:
        raise ValueError("Not enough data for prediction")

    X = np.arange(len(data)).reshape(-1, 1)
    y = np.array(data)

    model = LinearRegression()
    model.fit(X, y)
    
    future = np.array([len(data) + i for i in range(1, 6)]).reshape(-1, 1)
    predictions = model.predict(future)

    return predictions.tolist()

@router.get("/forecast/")
def get_forecast(db: Session = Depends(get_db)):
    """
    Retrieve glucose level data and predict future trends.
    """
    health_data = db.query(models.HealthData).all()

    if not health_data:
        raise HTTPException(status_code=404, detail="No data found")

    glucose_values = [entry.glucose_level for entry in health_data]

    try:
        predictions = predict_trend(glucose_values)
        return {"forecast": predictions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
