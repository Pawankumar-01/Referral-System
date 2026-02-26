# QR-Based Patient Referral Management System

A standalone FastAPI application for managing hospital patient referrals via QR codes.

## Features

- Unique QR code generation per patient after webinar enrollment
- New patient registration via referral QR code
- Referral tracking with consultation and medicine completion
- Automatic reward generation (10% consultation + 3% medicine discounts, 90-day expiry)
- In-DB notification records on successful referral
- Admin dashboard and completion endpoints
- Token-based admin authentication

## Tech Stack

- **FastAPI** – API framework
- **SQLAlchemy** – ORM
- **SQLite** – Development database
- **Pydantic** – Schema validation
- **UUID** – Primary keys
- **qrcode** – QR image generation

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

Database tables are **auto-created** on startup. No migration needed for development.

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/patients/` | Register a new patient (webinar enrollment) |
| GET | `/patients/{id}` | Get patient details |
| GET | `/ref/{coupon_code}` | Get referrer info by coupon |
| POST | `/ref/register` | Register new patient via referral QR |
| POST | `/admin/consultation-complete/{patient_id}` | Mark consultation done |
| POST | `/admin/medicine-complete/{patient_id}` | Mark medicine done |
| GET | `/admin/dashboard` | View referral stats |
| GET | `/rewards/{patient_id}` | List rewards for a patient |
| POST | `/rewards/use/{reward_id}` | Mark a reward as used |
| GET | `/notifications/{patient_id}` | List notifications for a patient |

## Admin Auth

Pass the admin token as a header:

```
X-Admin-Token: admin-secret-token-2024
```

Change this in `app/routers/admin_router.py` → `ADMIN_TOKEN` before production.

## Business Rules

- Self-referral is blocked (same phone = rejected)
- Each referred patient can only be referred once
- Rewards are generated **once** per referral on consultation completion
- Rewards expire 90 days from generation
- No external SMS; notifications stored with `status=pending`

## QR Codes

QR code images are saved to `./qr_codes/{patient_id}.png`. Each QR encodes `/ref/{coupon_code}`.

## Interactive Docs

Visit [http://localhost:8000/docs](http://localhost:8000/docs) after running the server.
