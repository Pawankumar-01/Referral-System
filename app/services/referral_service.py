from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.referral import Referral
from app.models.patient import Patient
from app.models.wallet import Wallet
from app.models.commission import CommissionTransaction
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from datetime import datetime


# -------------------------
# Helper: Credit Wallet
# -------------------------
def credit_wallet(db: Session, patient_id: str, amount: float):
    wallet = db.query(Wallet).filter(Wallet.patient_id == patient_id).first()
    if not wallet:
        wallet = Wallet(patient_id=patient_id, balance=0.0)
        db.add(wallet)
        db.flush()
    wallet.balance += amount


# -------------------------
# Consultation Completion
# -------------------------
def complete_consultation(db: Session, patient_id: str) -> dict:
    """
    Mark consultation complete.
    DOES NOT trigger MLM payout.
    """

    referral = db.query(Referral).filter(
        Referral.referred_patient_id == patient_id
    ).first()

    if not referral:
        raise HTTPException(status_code=404, detail="No referral record found")

    referral.consultation_completed = True
    referral.consultation_completed_at = datetime.utcnow()

    db.commit()
    db.refresh(referral)

    return {
        "message": "Consultation marked complete. Waiting for medicine completion.",
        "referral_id": referral.id
    }


# -------------------------
# Medicine Completion (MLM Trigger)
# -------------------------
def complete_medicine(
    db: Session,
    patient_id: str,
    consultation_amount: float,
    medicine_amount: float,
) -> dict:

    referral = db.query(Referral).filter(
        Referral.referred_patient_id == patient_id
    ).first()

    if not referral:
        raise HTTPException(status_code=404, detail="No referral record found")

    if referral.reward_generated:
        raise HTTPException(status_code=400, detail="Commission already processed")

    referral.medicine_completed = True
    referral.medicine_completed_at = datetime.utcnow()

    # Stop if consultation not completed
    if not referral.consultation_completed:
        db.commit()
        return {
            "message": "Medicine marked complete. Waiting for consultation completion.",
            "referral_id": referral.id
        }

    # -------------------------
    # FULL PAYMENT CONFIRMED
    # -------------------------

    total_bill = consultation_amount + medicine_amount

    referral.consultation_amount = consultation_amount
    referral.medicine_amount = medicine_amount
    referral.total_amount = total_bill

    source_patient = db.query(Patient).filter(
        Patient.id == referral.referred_patient_id
    ).first()

    current_patient = source_patient.referred_by
    level = 1

    # Commission structure
    FIXED_COMMISSIONS = {
        3: 100.0,
        4: 50.0,
        5: 40.0,
        6: 25.0,
    }

    while current_patient and level <= 6:

        commission = 0.0

        if level == 1:
            commission = (
                consultation_amount * 0.10 +
                medicine_amount * 0.05
            )

        elif level == 2:
            commission = total_bill * 0.015

        elif level in FIXED_COMMISSIONS:
            commission = FIXED_COMMISSIONS[level]

        # Credit wallet
        # credit_wallet(db, current_patient.id, commission)

        # Save transaction
        transaction = CommissionTransaction(
            earner_id=current_patient.id,
            source_patient_id=source_patient.id,
            level=level,
            bill_amount=total_bill,
            commission_amount=commission,
            status="credited"
        )
        db.add(transaction)

        # Notify this level earner
        create_notification(
            db,
            current_patient.id,
            f"💰 Commission Credited!\n\n"
            f"Level: {level}\n"
            f"Amount: ₹{commission:.2f}\n"
            f"Bill Amount: ₹{total_bill:.2f}",
            NotificationType.sms,
        )

        current_patient = current_patient.referred_by
        level += 1

    referral.reward_generated = True

    db.commit()
    db.refresh(referral)

    return {
        "message": "Medicine marked complete and 6-level MLM commission processed.",
        "referral_id": referral.id
    }