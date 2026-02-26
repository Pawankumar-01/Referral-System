from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.notification import NotificationType, NotificationStatus


class NotificationOut(BaseModel):
    id: str
    patient_id: str
    message: str
    notification_type: NotificationType
    status: NotificationStatus
    created_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True
