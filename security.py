# from passlib.context import CryptContext
# from datetime import datetime, timedelta
# from jose import JWTError, jwt

# # Secret key for JWT encoding & decoding
# SECRET_KEY = "your_secret_key_here"  # 🔹 Replace with a secure value
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60

# # Password hashing setup
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # Hash password
# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)

# # Verify password
# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)

# # Create JWT token
# def create_access_token(data: dict, expires_delta: timedelta = None):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# from passlib.context import CryptContext
# from datetime import datetime, timedelta
# from jose import JWTError, jwt

# # Secret key for encoding and decoding tokens
# SECRET_KEY = "your_secret_key"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expiry time

# # Password hashing configuration
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # Function to hash passwords
# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)

# # Function to verify passwords
# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)

# # Function to create JWT access token
# def create_access_token(data: dict, expires_delta: timedelta | None = None):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import re
from fastapi import HTTPException

# Secret key for encoding and decoding tokens
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expiry time

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to hash passwords
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Function to verify passwords
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Function to create JWT access token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Function to validate password strength
def validate_password(password: str):
    """Check if the password meets security requirements."""
    # if len(password) < 8:
    #     raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
    # if not re.search(r"[A-Z]", password):
    #     raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter.")
    # if not re.search(r"[a-z]", password):
    #     raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter.")
    # if not re.search(r"\d", password):
    #     raise HTTPException(status_code=400, detail="Password must contain at least one digit.")
    # if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
    #     raise HTTPException(status_code=400, detail="Password must contain at least one special character.")
    pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')

    # Check if the password matches the required pattern
    if not pattern.match(password):
        raise HTTPException(
            status_code=400, 
            detail="Password must be at least 8 characters long, contain at least one uppercase letter, one lowercase letter, and one number."
        )
