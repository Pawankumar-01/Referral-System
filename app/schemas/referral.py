from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReferralRegister(BaseModel):
    coupon_code: str  # referrer's coupon
    name: str
    phone: str
    email: Optional[str] = None


class ReferralOut(BaseModel):
    id: str
    referrer_id: str
    referred_patient_id: str
    consultation_completed: bool
    medicine_completed: bool
    reward_generated: bool
    created_at: datetime

    class Config:
        from_attributes = True
