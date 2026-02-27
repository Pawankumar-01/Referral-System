from fastapi import APIRouter, Depends, HTTPException
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
            "status": t.status,
            "created_at": t.created_at
        })

    return result



from datetime import datetime


@router.post("/claim/{commission_id}")
def claim_commission(commission_id: str, db: Session = Depends(get_db)):

    commission = db.query(CommissionTransaction).filter(
        CommissionTransaction.id == commission_id
    ).first()

    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")

    if commission.status != "approved":
        raise HTTPException(status_code=400, detail="Commission not approved yet")

    commission.status = "claimed"
    commission.claimed_at = datetime.utcnow()

    db.commit()

    return {"message": "Commission marked as claimed"}


@router.get("/all")
def get_all_commissions(db: Session = Depends(get_db)):
    transactions = db.query(CommissionTransaction)\
        .order_by(CommissionTransaction.created_at.desc()).all()

    return [
        {
            "id": t.id,
            "earner_id": t.earner_id,
            "level": t.level,
            "bill_amount": t.bill_amount,
            "commission_amount": t.commission_amount,
            "status": t.status,
            "created_at": t.created_at
        }
        for t in transactions
    ]