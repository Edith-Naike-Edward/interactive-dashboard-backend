# auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from database import get_db
from models import User
from security import hash_password, validate_password
import pandas as pd
from typing import List
import os

router = APIRouter(tags=["auth"])

# Constants
USER_CSV_PATH = "data/raw/users.csv"
USER_ROLES = ['CHV', 'Nurse', 'Doctor', 'Data Officer', 'Lab Technician', 'Pharmacist']

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    role: str
    organisation: str
    password: str
    site_id: int

@router.get("/roles", response_model=List[str])
def get_available_roles():
    """Get list of available user roles"""
    return USER_ROLES

@router.post("/register")
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with password validation."""
    # Validate password strength
    validate_password(request.password)
    
    # Check if user already exists in database
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = hash_password(request.password)

    # Create new user instance for database
    new_user = User(
        name=request.name,
        email=request.email,
        role=request.role,
        organisation=request.organisation,
        password=hashed_password,
        site_id=request.site_id
    )

    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Also save to CSV
    save_user_to_csv({
        "id": new_user.id,
        "name": request.name,
        "email": request.email,
        "role": request.role,
        "organisation": request.organisation,
        "site_id": request.site_id,
        "password": hashed_password
        # "is_active": True
    })

    return {"message": "User registered successfully"}

def save_user_to_csv(user_data: dict):
    """Save user data to CSV file"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(USER_CSV_PATH), exist_ok=True)
    
    try:
        # Try to read existing CSV
        if os.path.exists(USER_CSV_PATH):
            df = pd.read_csv(USER_CSV_PATH)
            # Append new user
            new_df = pd.DataFrame([user_data])
            df = pd.concat([df, new_df], ignore_index=True)
        else:
            # Create new DataFrame
            df = pd.DataFrame([user_data])
        
        # Save to CSV
        df.to_csv(USER_CSV_PATH, index=False)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save user to CSV: {str(e)}"
        )
    

