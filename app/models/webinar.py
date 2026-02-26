import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import relationship
from app.database import Base


class WebinarBatch(Base):
    __tablename__ = "webinar_batches"

    id = Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_name = Column(String, nullable=False)
    webinar_date = Column(DateTime, nullable=False)
    zoom_link = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patients = relationship("Patient", back_populates="webinar_batch")
