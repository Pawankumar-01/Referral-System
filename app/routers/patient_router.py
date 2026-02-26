from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.patient import Patient
from app.models.webinar import WebinarBatch
from app.schemas.patient import PatientCreate, PatientOut
from app.utils.coupon_generator import generate_coupon_code
import uuid
from typing import List
import qrcode
import os
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from dotenv import load_dotenv
from app.utils.qr_generator import _generate_qr

router = APIRouter(prefix="/patients", tags=["Patients"])

QR_DIR = "qr_codes"
os.makedirs(QR_DIR, exist_ok=True)


import os
load_dotenv()
FRONTEND_URL = "http://localhost:5173"



def _unique_coupon(db: Session) -> str:
    for _ in range(10):
        code = generate_coupon_code()
        exists = db.query(Patient).filter(Patient.coupon_code == code).first()
        if not exists:
            return code
    raise HTTPException(status_code=500, detail="Could not generate unique coupon")


@router.post("/", response_model=PatientOut)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(Patient.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")

    if payload.webinar_batch_id:
        batch = db.query(WebinarBatch).filter(WebinarBatch.id == payload.webinar_batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Webinar batch not found")

    coupon = _unique_coupon(db)
    patient_id = str(uuid.uuid4())
    qr_path = _generate_qr(coupon, patient_id)

    patient = Patient(
        id=patient_id,
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        coupon_code=coupon,
        qr_code_path=qr_path,
        webinar_batch_id=payload.webinar_batch_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)


    create_notification(
        db,
        patient.id,
        f"Welcome {patient.name}! 🎉\n\nYour referral code: {patient.coupon_code}\nShare it to earn commission.",
        NotificationType.sms,
    )

    db.commit()
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/search", response_model=List[PatientOut])
def search_patients(
    phone: str | None = None,
    name: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Patient)

    if phone:
        query = query.filter(Patient.phone == phone)

    if name:
        query = query.filter(Patient.name.ilike(f"%{name}%"))

    return query.order_by(Patient.created_at.desc()).all()

@router.get("/", response_model=List[PatientOut])
def list_patients(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return (
        db.query(Patient)
        .order_by(Patient.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )