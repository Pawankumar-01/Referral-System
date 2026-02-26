
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.wallet import Wallet
from app.models.commission import CommissionTransaction
from sqlalchemy import func

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/{patient_id}")
def get_wallet_summary(patient_id: str, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.patient_id == patient_id).first()

    balance = wallet.balance if wallet else 0.0

    total_earned = db.query(
        func.coalesce(func.sum(CommissionTransaction.commission_amount), 0.0)
    ).filter(
        CommissionTransaction.earner_id == patient_id
    ).scalar()

    total_transactions = db.query(CommissionTransaction).filter(
        CommissionTransaction.earner_id == patient_id
    ).count()

    return {
        "balance": balance,
        "total_earned": total_earned,
        "total_transactions": total_transactions
    }