import uuid
from datetime import datetime
from sqlalchemy import Column, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import relationship
from app.database import Base

class CommissionTransaction(Base):
    __tablename__ = "commission_transactions"

    id = Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))
    earner_id = Column(TEXT, ForeignKey("patients.id"))
    source_patient_id = Column(TEXT, ForeignKey("patients.id"))
    level = Column(Integer)  # 1,2,3
    bill_amount = Column(Float)
    commission_amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    earner = relationship("Patient", foreign_keys=[earner_id])