
from pydantic import BaseModel, EmailStr, Field


class FarmerCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str | None = None
    password: str = Field(..., min_length=8)


class FarmerResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None = None

    class Config:
        from_attributes = True
