from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from database import get_db
from models import User
from security import hash_password
from security import validate_password 

# router = APIRouter()
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Pydantic model for request validation
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    role: str
    organisation: str
    password: str

@router.post("/register")
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with password validation."""
    validate_password(request.password)  # Check if the password is strong
    # hashed_password = hash_password(request.password)
    # user = User(username=request.username, email=request.email, password=hashed_password)
    # db.add(user)
    # db.commit()
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = hash_password(request.password)

    # Create new user instance
    new_user = User(
        name=request.name,
        email=request.email,
        role=request.role,
        organisation=request.organisation,
        password=hashed_password
    )

    # Save user to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully"}
