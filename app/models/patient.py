import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import relationship
from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=True)
    coupon_code = Column(String, unique=True, index=True)
    qr_code_path = Column(String, nullable=True)

    referred_by_id = Column(TEXT, ForeignKey("patients.id"), nullable=True)
    webinar_batch_id = Column(TEXT, ForeignKey("webinar_batches.id"), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Self reference for MLM chain
    referred_by = relationship(
        "Patient",
        remote_side=[id],
        foreign_keys=[referred_by_id]
    )

    webinar_batch = relationship("WebinarBatch", back_populates="patients")

    notifications = relationship("Notification", back_populates="patient")