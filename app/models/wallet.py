from sqlalchemy import Column, Float, ForeignKey
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import relationship
from app.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    patient_id = Column(TEXT, ForeignKey("patients.id"), primary_key=True)
    balance = Column(Float, default=0.0)
    used_balance = Column(Float, default=0.0)

    patient = relationship("Patient")