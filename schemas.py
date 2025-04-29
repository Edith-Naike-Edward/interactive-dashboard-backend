from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    role: str
    organization: str
    site_id: int
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
