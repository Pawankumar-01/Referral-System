"""
wallet_router.py  — FIXED

Changes:
  - Added total_claimed and pending_amount fields to match frontend expectations.
  - Kept total_earned for backward compat.
  - All floats rounded to 2dp.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commission import CommissionTransaction
from app.models.wallet import Wallet

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/{patient_id}")
def get_wallet_summary(patient_id: str, db: Session = Depends(get_db)):

    wallet = db.query(Wallet).filter(Wallet.patient_id == patient_id).first()

    balance = round(wallet.balance, 2) if wallet else 0.0
    used_balance = round(wallet.used_balance, 2) if wallet else 0.0

    # Total across all statuses
    total_earned = db.query(
        func.coalesce(func.sum(CommissionTransaction.commission_amount), 0.0)
    ).filter(
        CommissionTransaction.earner_id == patient_id
    ).scalar()

    # Not yet approved by admin
    total_credited = db.query(
        func.coalesce(func.sum(CommissionTransaction.commission_amount), 0.0)
    ).filter(
        CommissionTransaction.earner_id == patient_id,
        CommissionTransaction.status == "credited",
    ).scalar()

    total_transactions = db.query(CommissionTransaction).filter(
        CommissionTransaction.earner_id == patient_id
    ).count()

    return {
        "balance": balance,
        "used_balance": used_balance,
        "total_earned": round(total_earned, 2),
        "total_claimed": used_balance,           # wallet.used_balance is authoritative
        "pending_amount": round(total_credited, 2),
        "total_transactions": total_transactions,
    }