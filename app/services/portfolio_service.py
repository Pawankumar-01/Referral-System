from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.patient import Patient
from app.models.wallet import Wallet
from app.models.referral import Referral
from app.models.commission import CommissionTransaction


def get_patient_portfolio(db: Session, patient_id: str):

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return None

    wallet = db.query(Wallet).filter(Wallet.patient_id == patient_id).first()

    total_generated = db.query(
        func.sum(CommissionTransaction.commission_amount)
    ).filter(
        CommissionTransaction.earner_id == patient_id
    ).scalar() or 0

    total_claimed = db.query(
        func.sum(CommissionTransaction.commission_amount)
    ).filter(
        CommissionTransaction.earner_id == patient_id,
        CommissionTransaction.status == "claimed"
    ).scalar() or 0

    pending_amount = total_generated - total_claimed

    referral_count = db.query(Referral).filter(
        Referral.referrer_id == patient_id
    ).count()

    referral_link = f"https://panaceanova.com/ref?code={patient.coupon_code}"

    level_counts = {}

    for level in range(1, 7):
        count = db.query(CommissionTransaction).filter(
            CommissionTransaction.earner_id == patient_id,
            CommissionTransaction.level == level
        ).count()

        level_counts[f"level_{level}"] = count

        return {
            "patient_id": patient.id,
            "name": patient.name,
            "coupon_code": patient.coupon_code,
            "referral_link": referral_link,
            "wallet_balance": wallet.balance if wallet else 0,
            "total_generated": total_generated,
            "total_claimed": total_claimed,
            "pending_amount": pending_amount,
            "referral_count": referral_count,
            "level_counts": level_counts
        }