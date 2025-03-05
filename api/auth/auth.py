from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from schemas import RegisterRequest, LoginRequest
from database import get_db
from models import User
from security import hash_password, verify_password, create_access_token

router = APIRouter()

@router.post("/register")
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=request.name,
        email=request.email,
        role=request.role,
        organization=request.organization,
        password=hash_password(request.password)  # Hash password before saving
    )

    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}

@router.post("/signin")
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
