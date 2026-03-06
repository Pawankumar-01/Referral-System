"""
portfolio_router.py  — NEW FILE (was completely missing)

This is the most critical missing piece.
PatientPage.jsx calls GET /portfolio/{patient_id} but no such route existed.

Returns everything the patient page needs in one call:
  - referral_link
  - wallet_balance
  - total_generated  (sum of ALL commission_amount regardless of status)
  - total_claimed    (sum where status = "claimed")
  - pending_amount   (sum where status = "credited" — not yet approved)
  - referral_count
  - level_counts     (breakdown by MLM level)
"""

import os
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.models.wallet import Wallet
from app.models.commission import CommissionTransaction
from app.models.referral import Referral

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@router.get("/{patient_id}")
def get_portfolio(patient_id: str, db: Session = Depends(get_db)):

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # ── Wallet ────────────────────────────────────────────────────────────
    wallet = db.query(Wallet).filter(Wallet.patient_id == patient_id).first()
    wallet_balance = round(wallet.balance, 2) if wallet else 0.0
    # used_balance is the authoritative total_claimed figure from the wallet
    wallet_used = round(wallet.used_balance, 2) if wallet else 0.0

    # ── Commission aggregates ─────────────────────────────────────────────

    # Total ever generated (all statuses)
    total_generated = db.query(
        func.coalesce(func.sum(CommissionTransaction.commission_amount), 0.0)
    ).filter(
        CommissionTransaction.earner_id == patient_id
    ).scalar()

    # Credited only (generated but admin hasn't approved yet)
    total_credited = db.query(
        func.coalesce(func.sum(CommissionTransaction.commission_amount), 0.0)
    ).filter(
        CommissionTransaction.earner_id == patient_id,
        CommissionTransaction.status == "credited",
    ).scalar()

    # Claimed (used as discount)
    total_claimed_commission = db.query(
        func.coalesce(func.sum(CommissionTransaction.commission_amount), 0.0)
    ).filter(
        CommissionTransaction.earner_id == patient_id,
        CommissionTransaction.status == "claimed",
    ).scalar()

    # "Pending amount" = credited (not approved) commissions
    # These are visible to patient but not yet in their wallet
    pending_amount = round(total_credited, 2)

    # Use wallet.used_balance as total_claimed (source of truth for actual usage)
    total_claimed = wallet_used

    # ── Referrals ─────────────────────────────────────────────────────────
    referral_count = db.query(Referral).filter(
        Referral.referrer_id == patient_id
    ).count()

    # ── Level breakdown ───────────────────────────────────────────────────
    level_rows = (
        db.query(
            CommissionTransaction.level,
            func.count(CommissionTransaction.id).label("count"),
        )
        .filter(CommissionTransaction.earner_id == patient_id)
        .group_by(CommissionTransaction.level)
        .all()
    )
    level_counts = {f"level_{row.level}": row.count for row in level_rows}

    # ── Referral link ─────────────────────────────────────────────────────
    referral_link = f"{FRONTEND_URL}/ref/{patient.coupon_code}"

    return {
        # Identity
        "patient_id": patient_id,
        "referral_link": referral_link,
        # Wallet
        "wallet_balance": wallet_balance,
        # Commission figures
        "total_generated": round(total_generated, 2),
        "total_claimed": total_claimed,
        "pending_amount": pending_amount,
        # Referral stats
        "referral_count": referral_count,
        "level_counts": level_counts,
    }