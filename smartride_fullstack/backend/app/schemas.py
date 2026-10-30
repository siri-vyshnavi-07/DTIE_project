from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(default="", max_length=20)
    password: str = Field(min_length=8, max_length=100)

class LoginIn(BaseModel):
    email: str 
    password: str

class RechargeIn(BaseModel):
    amount: float = Field(gt=0, le=5000)

class JourneyIn(BaseModel):
    qr_token: str
    from_stop_id: int
    to_stop_id: int

class RegenerateQRIn(BaseModel):
    confirm: bool = True
