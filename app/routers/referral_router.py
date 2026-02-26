from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.patient import Patient
from app.models.referral import Referral
from app.schemas.referral import ReferralRegister, ReferralOut
from app.schemas.patient import PatientOut
from app.utils.coupon_generator import generate_coupon_code
import uuid, qrcode, os
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from app.utils.qr_generator import _generate_qr

router = APIRouter(prefix="/ref", tags=["Referral"])

QR_DIR = "qr_codes"
os.makedirs(QR_DIR, exist_ok=True)





def _unique_coupon(db: Session) -> str:
    for _ in range(10):
        code = generate_coupon_code()
        exists = db.query(Patient).filter(Patient.coupon_code == code).first()
        if not exists:
            return code
    raise HTTPException(status_code=500, detail="Could not generate unique coupon")


@router.get("/{coupon_code}")
def get_referral_info(coupon_code: str, db: Session = Depends(get_db)):
    referrer = db.query(Patient).filter(Patient.coupon_code == coupon_code).first()
    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid coupon code")
    return {
        "referrer_name": referrer.name,
        "coupon_code": coupon_code,
        "message": "Register below to be referred by this patient",
    }


@router.post("/register", response_model=PatientOut)
def register_via_referral(payload: ReferralRegister, db: Session = Depends(get_db)):
    # Find referrer
    referrer = db.query(Patient).filter(Patient.coupon_code == payload.coupon_code).first()
    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid referral coupon code")

    # Prevent self-referral
    if referrer.phone == payload.phone:
        raise HTTPException(status_code=400, detail="Self-referral is not allowed")

    # Prevent duplicate phone
    existing = db.query(Patient).filter(Patient.phone == payload.phone).first()
    if existing:
        # Check if already referred
        dup_referral = db.query(Referral).filter(Referral.referred_patient_id == existing.id).first()
        if dup_referral:
            raise HTTPException(status_code=400, detail="Patient already referred")
        raise HTTPException(status_code=400, detail="Phone already registered")

    coupon = _unique_coupon(db)
    patient_id = str(uuid.uuid4())
    qr_path = _generate_qr(coupon, patient_id)

    new_patient = Patient(
        id=patient_id,
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        coupon_code=coupon,
        qr_code_path=qr_path,
        referred_by_id=referrer.id,
    )
    db.add(new_patient)
    db.flush()

    referral = Referral(
        id=str(uuid.uuid4()),
        referrer_id=referrer.id,
        referred_patient_id=new_patient.id,
    )
    db.add(referral)
    db.commit()
    db.refresh(new_patient)

    # Notify new patient
    create_notification(
        db,
        new_patient.id,
        f"Welcome {new_patient.name}! 🎉\nYou were referred by {referrer.name}.",
        NotificationType.sms,
    )

    # Notify referrer
    create_notification(
        db,
        referrer.id,
        f"Good news! 🎉\n{new_patient.name} registered using your referral code.\nCommission will be processed after treatment.",
        NotificationType.sms,
    )

    db.commit()
    return new_patient
