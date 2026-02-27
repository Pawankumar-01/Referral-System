from fastapi import FastAPI
from app.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware 
from app.routers import wallet_router, commission_router

from fastapi.staticfiles import StaticFiles




# Import all models to ensure they're registered before create_all
from app.models import patient, webinar, referral, notification  # noqa: F401

from app.routers import (
    patient_router,
    referral_router,
    admin_router,
    notification_router,

)


# Auto-create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QR-Based Patient Referral Management System",
    version="1.0.0",
    description="Standalone referral management system with QR code generation and reward tracking.",
)
app.mount("/qr", StaticFiles(directory="qr_codes"), name="qr")


origins =[
    "http://localhost:5173",
    "https://panaceanova.com"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # Allows specific origins
    allow_credentials=True,        # Allows cookies/authorization headers to be sent cross-origin
    allow_methods=["*"],           # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],           # Allows all headers
)


app.include_router(patient_router.router)
app.include_router(referral_router.router)
app.include_router(admin_router.router)
app.include_router(notification_router.router)
app.include_router(wallet_router.router)
app.include_router(commission_router.router)


@app.get("/")
def root():
    return {"message": "Referral Management System is running. Visit /docs for API documentation."}
