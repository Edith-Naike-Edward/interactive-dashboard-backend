from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db  # Your DB connection setup
from models import User  # Your User model
from security import verify_password, create_access_token  # Hashing & JWT handling
# from database import get_db # Dependency to get a database session

router = APIRouter(tags=["auth"]) 

# Request Body Model
class SignInRequest(BaseModel):
    email: str
    password: str

@router.post("/signin")
def signin(request: SignInRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()

    # if not user or not verify_password(request.password, user.password):
    #     raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")


    token = create_access_token({"sub": user.email})  # Generate JWT

    return {"access_token": token, "token_type": "bearer", "user": {"email": user.email, "role": user.role}}
