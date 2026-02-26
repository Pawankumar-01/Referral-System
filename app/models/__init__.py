# Models package - ensures all models are importable
# Import all models so SQLAlchemy registers them properly

from app.models.patient import Patient
from app.models.referral import Referral
from app.models.webinar import WebinarBatch
from app.models.notification import Notification
from app.models.wallet import Wallet
from app.models.commission import CommissionTransaction

# Optional: if you're keeping Reward temporarily
# from app.models.reward import Reward

__all__ = [
    "Patient",
    "Referral",
    "WebinarBatch",
    "Notification",
    "Wallet",
    "CommissionTransaction",
]