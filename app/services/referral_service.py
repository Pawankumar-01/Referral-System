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

    # If consultation not completed yet, stop
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

    # Get the referred patient (source)
    source_patient = db.query(Patient).filter(
        Patient.id == referral.referred_patient_id
    ).first()

    current_patient = source_patient.referred_by
    level = 1

    while current_patient and level <= 3:

        if level == 1:
            # Direct referrer
            commission = (
                consultation_amount * 0.10 +
                medicine_amount * 0.03
            )

        elif level == 2:
            commission = total_bill * 0.01

        elif level == 3:
            commission = total_bill * 0.01

        credit_wallet(db, current_patient.id, commission)

        transaction = CommissionTransaction(
            earner_id=current_patient.id,
            source_patient_id=source_patient.id,
            level=level,
            bill_amount=total_bill,
            commission_amount=commission,
        )

        db.add(transaction)

        current_patient = current_patient.referred_by
        level += 1

    # Lock commission
    referral.reward_generated = True

    # Optional notification to direct referrer
    if referral.referrer_id:
        create_notification(
            db,
            referral.referrer_id,
            "Your referral has completed full payment. Commission credited to your wallet.",
            NotificationType.sms,
        )

    db.commit()
    db.refresh(referral)
    create_notification(
        db,
        current_patient.id,
        f"💰 Commission Credited!\n\nAmount: ₹{commission:.2f}\nLevel: {level}\nBill Amount: ₹{total_bill:.2f}",
        NotificationType.sms,
    )

    return {
        "message": "Medicine marked complete and MLM commission processed.",
        "referral_id": referral.id
    }