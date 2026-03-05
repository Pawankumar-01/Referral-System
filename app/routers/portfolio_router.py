from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.portfolio_service import get_patient_portfolio

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/{patient_id}")
def patient_portfolio(patient_id: str, db: Session = Depends(get_db)):

    data = get_patient_portfolio(db, patient_id)

    if not data:
        raise HTTPException(status_code=404, detail="Patient not found")

    return data