"""
VERIDEX API entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000

Then open http://127.0.0.1:8000/docs for interactive Swagger UI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, health, passport

app = FastAPI(
    title="VERIDEX API",
    description="OCR/MRZ extraction, document validation, tampering/forensics "
    "screening, and face-match verification for identity documents.",
    version="0.2.0",
)

# Adjust origins for your frontend's actual dev/prod URLs.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(passport.router)
