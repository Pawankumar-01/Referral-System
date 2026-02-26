import re
from fastapi import HTTPException

def normalize_phone(phone: str) -> str:
    """
    Convert phone into canonical format:
    India: 91XXXXXXXXXX
    """

    if not phone:
        raise HTTPException(status_code=400, detail="Phone number required")

    # Remove spaces, dashes, plus
    phone = re.sub(r"[^\d]", "", phone)

    # If starts with 0 and 10 digits after
    if phone.startswith("0") and len(phone) == 11:
        phone = phone[1:]

    # If 10 digits → assume Indian number
    if len(phone) == 10:
        phone = "91" + phone

    # If already 12 digits starting with 91 → ok
    if len(phone) == 12 and phone.startswith("91"):
        return phone

    raise HTTPException(status_code=400, detail="Invalid phone number format")