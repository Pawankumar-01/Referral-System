"""
admin_router.py  — FIXED
Fixes applied:
  1. Removed duplicate imports (CommissionTransaction, verify_admin).
  2. verify_admin defined once, used everywhere.
  3. /claim-wallet now marks approved commissions as "claimed" (FIFO order)
     to satisfy the full credited → approved → claimed transition.
  4. /approve-commission returns earner name for frontend display.
  5. /dashboard returns consistent field names.
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commission import CommissionTransaction
from app.models.patient import Patient
from app.models.referral import Referral
from app.models.wallet import Wallet
from app.services.referral_service import complete_consultation, complete_medicine

load_dotenv()

router = APIRouter(prefix="/admin", tags=["Admin"])

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")


# ─────────────────────────────────────────
# Request Schemas
# ─────────────────────────────────────────

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


class ClaimWalletRequest(BaseModel):
    phone: str
    amount: float


# ─────────────────────────────────────────
# Admin Auth  (single definition)
# ─────────────────────────────────────────

def verify_admin(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")


# ─────────────────────────────────────────
# Consultation Completion
# ─────────────────────────────────────────

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


# ─────────────────────────────────────────
# Medicine Completion (MLM Trigger)
# ─────────────────────────────────────────

@router.post("/medicine-complete")
def mark_medicine_complete(
    payload: MedicineCompleteRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    return complete_medicine(
        db, payload.patient_id,
        payload.consultation_amount, payload.medicine_amount,
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
        db, patient.id,
        payload.consultation_amount, payload.medicine_amount,
    )


# ─────────────────────────────────────────
# Dashboard Stats
# ─────────────────────────────────────────

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    return {
        "total_patients": db.query(Patient).count(),
        "total_referrals": db.query(Referral).count(),
        "consultations_completed": db.query(Referral).filter(
            Referral.consultation_completed == True
        ).count(),
        "medicines_completed": db.query(Referral).filter(
            Referral.medicine_completed == True
        ).count(),
        # "credited" = generated but not yet approved by admin
        "pending_commissions": db.query(CommissionTransaction).filter(
            CommissionTransaction.status == "credited"
        ).count(),
        # "approved" = admin approved, sitting in wallet
        "approved_commissions": db.query(CommissionTransaction).filter(
            CommissionTransaction.status == "approved"
        ).count(),
        # "claimed" = used as discount
        "commissions_processed": db.query(CommissionTransaction).filter(
            CommissionTransaction.status == "claimed"
        ).count(),
    }


# ─────────────────────────────────────────
# Patients Overview
# ─────────────────────────────────────────

@router.get("/patients-overview")
def patients_overview(
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    patients = db.query(Patient).all()
    result = []
    for p in patients:
        referral = (
            db.query(Referral)
            .filter(Referral.referred_patient_id == p.id)
            .first()
        )
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


# ─────────────────────────────────────────
# Pending Commissions List  (for admin UI)
# ─────────────────────────────────────────

@router.get("/pending-commissions")
def pending_commissions(
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """
    Returns all commissions with status='credited' enriched with earner name,
    so the admin UI can show a meaningful label instead of a raw UUID.
    """
    rows = (
        db.query(CommissionTransaction)
        .filter(CommissionTransaction.status == "credited")
        .order_by(CommissionTransaction.created_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "earner_id": c.earner_id,
            "earner_name": c.earner.name if c.earner else "Unknown",
            "level": c.level,
            "bill_amount": c.bill_amount,
            "commission_amount": c.commission_amount,
            "status": c.status,
            "created_at": c.created_at,
        }
        for c in rows
    ]


# ─────────────────────────────────────────
# Approve Commission
# ─────────────────────────────────────────

@router.post("/approve-commission/{commission_id}")
def approve_commission(
    commission_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    commission = (
        db.query(CommissionTransaction)
        .filter(CommissionTransaction.id == commission_id)
        .first()
    )
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")

    if commission.status != "credited":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve: commission is already '{commission.status}'"
        )

    # Upsert wallet
    wallet = db.query(Wallet).filter(Wallet.patient_id == commission.earner_id).first()
    if not wallet:
        wallet = Wallet(patient_id=commission.earner_id, balance=0.0, used_balance=0.0)
        db.add(wallet)
        db.flush()

    wallet.balance += commission.commission_amount

    commission.status = "approved"
    commission.approved_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Commission approved and wallet credited",
        "earner_id": commission.earner_id,
        "amount": commission.commission_amount,
    }


# ─────────────────────────────────────────
# Claim Wallet Amount  — FIX: also marks commissions "claimed"
# ─────────────────────────────────────────

@router.post("/claim-wallet")
def claim_wallet_amount(
    payload: ClaimWalletRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    patient = db.query(Patient).filter(Patient.phone == payload.phone).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    wallet = db.query(Wallet).filter(Wallet.patient_id == patient.id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    if payload.amount > wallet.balance:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Available: ₹{wallet.balance:.2f}"
        )

    # Deduct from wallet
    wallet.balance -= payload.amount
    wallet.used_balance += payload.amount

    # ── Mark approved commissions as "claimed" in FIFO order ──────────────
    # We walk through approved commissions oldest-first and mark them claimed
    # until we've accounted for the full claimed amount.
    remaining = payload.amount
    approved_commissions = (
        db.query(CommissionTransaction)
        .filter(
            CommissionTransaction.earner_id == patient.id,
            CommissionTransaction.status == "approved",
        )
        .order_by(CommissionTransaction.approved_at.asc())
        .all()
    )

    for c in approved_commissions:
        if remaining <= 0:
            break
        c.status = "claimed"
        c.claimed_at = datetime.utcnow()
        remaining -= c.commission_amount
    # Note: remaining may go slightly negative if the last commission exceeds
    # the remainder — that's fine, the wallet balance is the source of truth.

    db.commit()

    return {
        "message": f"₹{payload.amount:.2f} claimed successfully",
        "remaining_balance": wallet.balance,
        "used_balance": wallet.used_balance,
    }