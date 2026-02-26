from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.commission import CommissionTransaction

router = APIRouter(prefix="/commission", tags=["Commission"])


@router.get("/{patient_id}")
def get_commission_history(patient_id: str, db: Session = Depends(get_db)):
    transactions = db.query(CommissionTransaction).filter(
        CommissionTransaction.earner_id == patient_id
    ).order_by(CommissionTransaction.created_at.desc()).all()

    result = []

    for t in transactions:
        result.append({
            "id": t.id,
            "source_patient_id": t.source_patient_id,
            "level": t.level,
            "bill_amount": t.bill_amount,
            "commission_amount": t.commission_amount,
            "created_at": t.created_at
        })

    return result