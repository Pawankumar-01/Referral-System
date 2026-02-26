import os
import qrcode
from dotenv import load_dotenv

load_dotenv()

QR_DIR = "qr_codes"
os.makedirs(QR_DIR, exist_ok=True)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

def _generate_qr(coupon_code: str, patient_id: str) -> str:
    referral_link = f"{FRONTEND_URL}/ref?code={coupon_code}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(referral_link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    filename = f"{patient_id}.png"
    path = os.path.join(QR_DIR, filename)
    img.save(path)

    return filename