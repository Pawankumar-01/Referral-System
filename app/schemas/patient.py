from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class PatientCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    webinar_batch_id: Optional[str] = None


class PatientOut(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str]
    coupon_code: Optional[str]
    qr_code_path: Optional[str]
    referred_by_id: Optional[str]
    webinar_batch_id: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
