from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationOut
from typing import List

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/{patient_id}", response_model=List[NotificationOut])
def get_notifications(patient_id: str, db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.patient_id == patient_id).all()
