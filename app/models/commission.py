import uuid
from datetime import datetime
from sqlalchemy import Column, Float, Integer, DateTime, ForeignKey, String
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import relationship
from app.database import Base


class CommissionTransaction(Base):
    __tablename__ = "commission_transactions"

    id = Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))
    earner_id = Column(TEXT, ForeignKey("patients.id"))
    source_patient_id = Column(TEXT, ForeignKey("patients.id"))
    level = Column(Integer)
    bill_amount = Column(Float)
    commission_amount = Column(Float)

    status = Column(String, default="credited")  
    # credited → approved → claimed

    approved_at = Column(DateTime, nullable=True)
    claimed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    earner = relationship("Patient", foreign_keys=[earner_id])