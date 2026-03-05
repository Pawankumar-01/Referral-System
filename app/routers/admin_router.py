from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.referral import Referral
from app.models.patient import Patient
from app.services.referral_service import complete_consultation, complete_medicine
import os
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(prefix="/admin", tags=["Admin"])

ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')

from pydantic import BaseModel


# -----------------------------
# Request Schemas
# -----------------------------

class PhoneRequest(BaseModel):
    phone: str


class MedicineCompleteRequest(BaseModel):
    patient_id: str
    consultation_amount: float
    medicine_amount: float


class MedicineCompleteByPhoneRequest(BaseModel):
    phone: str
    consultation_amount: float
    medicine_amount: float


# -----------------------------
# Admin Verification
# -----------------------------

def verify_admin(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")


# -----------------------------
# Consultation Completion
# -----------------------------

@router.post("/consultation-complete/{patient_id}")
def mark_consultation_complete(
    patient_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    return complete_consultation(db, patient_id)


@router.post("/consultation-complete-by-phone")
def mark_consultation_complete_by_phone(
    payload: PhoneRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    patient = db.query(Patient).filter(Patient.phone == payload.phone).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return complete_consultation(db, patient.id)


# -----------------------------
# Medicine Completion (MLM Trigger)
# -----------------------------

@router.post("/medicine-complete")
def mark_medicine_complete(
    payload: MedicineCompleteRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    return complete_medicine(
        db,
        payload.patient_id,
        payload.consultation_amount,
        payload.medicine_amount,
    )


@router.post("/medicine-complete-by-phone")
def mark_medicine_complete_by_phone(
    payload: MedicineCompleteByPhoneRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    patient = db.query(Patient).filter(Patient.phone == payload.phone).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return complete_medicine(
        db,
        patient.id,
        payload.consultation_amount,
        payload.medicine_amount,
    )


# -----------------------------
# Admin Dashboard
# -----------------------------

from app.models.commission import CommissionTransaction


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: None = Depends(verify_admin)):

    total_patients = db.query(Patient).count()

    total_referrals = db.query(Referral).count()

    consultations_done = db.query(Referral).filter(
        Referral.consultation_completed == True
    ).count()

    medicines_done = db.query(Referral).filter(
        Referral.medicine_completed == True
    ).count()

    commissions_processed = db.query(CommissionTransaction).filter(
        CommissionTransaction.status == "claimed"
    ).count()

    pending_commissions = db.query(CommissionTransaction).filter(
        CommissionTransaction.status == "credited"
    ).count()

    approved_commissions = db.query(CommissionTransaction).filter(
        CommissionTransaction.status == "approved"
    ).count()

    return {
        "total_patients": total_patients,
        "total_referrals": total_referrals,
        "consultations_completed": consultations_done,
        "medicines_completed": medicines_done,
        "commissions_processed": commissions_processed,
        "pending_commissions": pending_commissions,
        "approved_commissions": approved_commissions
    }


# -----------------------------
# Patients Overview
# -----------------------------

@router.get("/patients-overview")
def patients_overview(
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    patients = db.query(Patient).all()
    result = []

    for p in patients:
        referral = db.query(Referral).filter(
            Referral.referred_patient_id == p.id
        ).first()

        result.append({
            "id": p.id,
            "name": p.name,
            "phone": p.phone,
            "referred_by": referral.referrer.name if referral and referral.referrer else None,
            "consultation_completed": referral.consultation_completed if referral else False,
            "medicine_completed": referral.medicine_completed if referral else False,
            "commission_processed": referral.reward_generated if referral else False,
        })

    return result


from app.models.commission import CommissionTransaction
from app.models.wallet import Wallet
from datetime import datetime
from app.dependencies.admin_auth import verify_admin


@router.post("/approve-commission/{commission_id}")
def approve_commission(
    commission_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):

    commission = db.query(CommissionTransaction).filter(
        CommissionTransaction.id == commission_id
    ).first()

    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")

    if commission.status != "credited":
        raise HTTPException(status_code=400, detail="Commission already processed")

    wallet = db.query(Wallet).filter(
        Wallet.patient_id == commission.earner_id
    ).first()

    if not wallet:
        wallet = Wallet(patient_id=commission.earner_id, balance=0)
        db.add(wallet)
        db.flush()

    wallet.balance += commission.commission_amount

    commission.status = "approved"
    commission.approved_at = datetime.utcnow()

    db.commit()

    return {"message": "Commission approved and credited"}



class ClaimWalletRequest(BaseModel):
    phone: str
    amount: float


@router.post("/claim-wallet")
def claim_wallet_amount(
    payload: ClaimWalletRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):

    patient = db.query(Patient).filter(
        Patient.phone == payload.phone
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    wallet = db.query(Wallet).filter(
        Wallet.patient_id == patient.id
    ).first()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    if payload.amount > wallet.balance:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    wallet.balance -= payload.amount
    wallet.used_balance += payload.amount

    db.commit()

    return {
        "message": f"₹{payload.amount} claimed",
        "remaining_balance": wallet.balance
    }