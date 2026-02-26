from pydantic import BaseModel
from datetime import datetime, date
from app.models.reward import RewardType
from typing import Optional


class RewardOut(BaseModel):
    id: str
    patient_id: str
    reward_type: RewardType
    referral_id: str
    used_at: Optional[datetime]
    value_percent: float
    is_used: bool
    expiry_date: date
    created_at: datetime

    class Config:
        from_attributes = True
