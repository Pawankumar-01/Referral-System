"""
referral_service.py  — FIXED

Changes:
  1. MLM chain traversal now uses explicit DB queries per level instead of
     relying on SQLAlchemy lazy-loaded relationship in a loop.
     The lazy-load approach silently fails or causes DetachedInstanceError
     when the session state changes mid-loop.
  2. commission status is explicitly set to "credited" (was already correct,
     made explicit for clarity).
  3. credit_wallet helper kept but is NOT called during medicine completion —
     wallet credit happens only when admin approves (correct per spec).
"""

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.commission import CommissionTransaction
from app.models.notification import NotificationType
from app.models.patient import Patient
from app.models.referral import Referral
from app.models.wallet import Wallet
from app.services.notification_service import create_notification


# ── Helper: Credit Wallet ────────────────────────────────────────────────────

def credit_wallet(db: Session, patient_id: str, amount: float):
    """Upsert wallet and add amount to balance."""
    wallet = db.query(Wallet).filter(Wallet.patient_id == patient_id).first()
    if not wallet:
        wallet = Wallet(patient_id=patient_id, balance=0.0, used_balance=0.0)
        db.add(wallet)
        db.flush()
    wallet.balance += amount


# ── Consultation Completion ──────────────────────────────────────────────────

def complete_consultation(db: Session, patient_id: str) -> dict:
    """Mark consultation complete. Does NOT trigger MLM payout."""

    referral = (
        db.query(Referral)
        .filter(Referral.referred_patient_id == patient_id)
        .first()
    )
    if not referral:
        raise HTTPException(status_code=404, detail="No referral record found for this patient")

    if referral.consultation_completed:
        return {
            "message": "Consultation was already marked complete.",
            "referral_id": referral.id,
        }

    referral.consultation_completed = True
    referral.consultation_completed_at = datetime.utcnow()
    db.commit()
    db.refresh(referral)

    return {
        "message": "Consultation marked complete. Waiting for medicine completion.",
        "referral_id": referral.id,
    }


# ── Medicine Completion (MLM Trigger) ────────────────────────────────────────

def complete_medicine(
    db: Session,
    patient_id: str,
    consultation_amount: float,
    medicine_amount: float,
) -> dict:

    referral = (
        db.query(Referral)
        .filter(Referral.referred_patient_id == patient_id)
        .first()
    )
    if not referral:
        raise HTTPException(status_code=404, detail="No referral record found for this patient")

    if referral.reward_generated:
        raise HTTPException(status_code=400, detail="Commission already processed for this patient")

    referral.medicine_completed = True
    referral.medicine_completed_at = datetime.utcnow()

    if not referral.consultation_completed:
        db.commit()
        return {
            "message": "Medicine marked complete. Waiting for consultation completion.",
            "referral_id": referral.id,
        }

    # ── Both steps complete → generate MLM commissions ───────────────────

    total_bill = consultation_amount + medicine_amount

    referral.consultation_amount = consultation_amount
    referral.medicine_amount = medicine_amount
    referral.total_amount = total_bill

    # Commission rates
    FIXED_COMMISSIONS = {
        3: 100.0,
        4: 50.0,
        5: 40.0,
        6: 25.0,
    }

    # ── FIX: explicit DB query per level instead of lazy relationship loop ──
    # Start from the direct referrer of the source patient
    source_patient_id = referral.referred_patient_id
    current_patient_id = referral.referrer_id   # level-1 earner

    level = 1
    levels_created = []

    while current_patient_id and level <= 6:

        current_patient = (
            db.query(Patient)
            .filter(Patient.id == current_patient_id)
            .first()
        )
        if not current_patient:
            break

        # Calculate commission for this level
        if level == 1:
            commission_amount = (
                consultation_amount * 0.10 + medicine_amount * 0.05
            )
        elif level == 2:
            commission_amount = total_bill * 0.015
        else:
            commission_amount = FIXED_COMMISSIONS.get(level, 0.0)

        # Create commission record with status="credited"
        transaction = CommissionTransaction(
            earner_id=current_patient.id,
            source_patient_id=source_patient_id,
            level=level,
            bill_amount=total_bill,
            commission_amount=commission_amount,
            status="credited",       # Admin must approve before wallet is credited
        )
        db.add(transaction)

        # Notify earner
        create_notification(
            db,
            current_patient.id,
            (
                f"💰 Commission Generated!\n\n"
                f"Level: {level}\n"
                f"Amount: ₹{commission_amount:.2f}\n"
                f"Bill Amount: ₹{total_bill:.2f}\n"
                f"Status: Pending Admin Approval"
            ),
            NotificationType.sms,
        )

        levels_created.append({"level": level, "earner_id": current_patient.id, "amount": commission_amount})

        # Climb up the referral chain via explicit DB lookup
        parent_referral = (
            db.query(Referral)
            .filter(Referral.referred_patient_id == current_patient.id)
            .first()
        )
        current_patient_id = parent_referral.referrer_id if parent_referral else None
        level += 1

    referral.reward_generated = True
    db.commit()
    db.refresh(referral)

    return {
        "message": f"Medicine complete. MLM commissions generated for {len(levels_created)} levels.",
        "referral_id": referral.id,
        "commissions_created": levels_created,
    }