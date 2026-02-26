import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class NotificationType(str, enum.Enum):
    sms = "sms"
    email = "email"
    in_app = "in_app"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(TEXT, ForeignKey("patients.id"), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="notifications")
