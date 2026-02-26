import uuid
from datetime import datetime
from sqlalchemy import Column, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import relationship
from app.database import Base


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))

    referrer_id = Column(TEXT, ForeignKey("patients.id"), nullable=False)
    referred_patient_id = Column(TEXT, ForeignKey("patients.id"), nullable=False, unique=True)

    # -------------------------
    # Completion Status
    # -------------------------
    consultation_completed = Column(Boolean, default=False)
    consultation_completed_at = Column(DateTime, nullable=True)

    medicine_completed = Column(Boolean, default=False)
    medicine_completed_at = Column(DateTime, nullable=True)

    # -------------------------
    # Billing Details (NEW)
    # -------------------------
    consultation_amount = Column(Float, nullable=True)
    medicine_amount = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True)

    # -------------------------
    # Commission Lock
    # -------------------------
    reward_generated = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    referrer = relationship("Patient", foreign_keys=[referrer_id])
    referred_patient = relationship("Patient", foreign_keys=[referred_patient_id])