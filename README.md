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

