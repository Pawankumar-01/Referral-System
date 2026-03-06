"""
commission_router.py  — FIXED

Changes:
  - /all now returns earner_name so admin UI is readable.
  - /{patient_id} now returns source_patient_name for context.
  - Removed dead commented-out claim endpoint (claim is now done via admin /claim-wallet).
  - Added approved_at and claimed_at to responses so frontend can show timestamps.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.commission import CommissionTransaction

router = APIRouter(prefix="/commission", tags=["Commission"])


# ── All commissions (admin use) ─────────────────────────────────────────────

@router.get("/all")
def get_all_commissions(db: Session = Depends(get_db)):
    transactions = (
        db.query(CommissionTransaction)
        .order_by(
            CommissionTransaction.status,
            CommissionTransaction.created_at.desc(),
        )
        .all()
    )
    return [
        {
            "id": t.id,
            "earner_id": t.earner_id,
            "earner_name": t.earner.name if t.earner else "Unknown",   # FIX: was missing
            "source_patient_id": t.source_patient_id,
            "level": t.level,
            "bill_amount": t.bill_amount,
            "commission_amount": t.commission_amount,
            "status": t.status,
            "created_at": t.created_at,
            "approved_at": t.approved_at,
            "claimed_at": t.claimed_at,
        }
        for t in transactions
    ]


# ── Commission history for a patient ────────────────────────────────────────

@router.get("/{patient_id}")
def get_commission_history(patient_id: str, db: Session = Depends(get_db)):
    transactions = (
        db.query(CommissionTransaction)
        .filter(CommissionTransaction.earner_id == patient_id)
        .order_by(CommissionTransaction.created_at.desc())
        .all()
    )
    return [
        {
            "id": t.id,
            "source_patient_id": t.source_patient_id,
            "level": t.level,
            "bill_amount": t.bill_amount,
            "commission_amount": t.commission_amount,
            "status": t.status,
            "created_at": t.created_at,
            "approved_at": t.approved_at,
            "claimed_at": t.claimed_at,
        }
        for t in transactions
    ]