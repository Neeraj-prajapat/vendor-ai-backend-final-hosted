
# app/main.py

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, get_db
from .routers import reports, breaches
import app.security_vulnerability as security_vulnerability
# from app.core.config import DATABASE_URL, API_KEY  # import from config
from core.config import DATABASE_URL, API_KEY  # import from config

# DATABASE_URL = os.getenv("DATABASE_URL")
# API_KEY = os.getenv("PERPLEXITY_API_KEY")

# DATABASE_URL = "postgresql://postgres:postgresql@localhost/your_dbname"
# API_KEY = "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"


if not DATABASE_URL or not API_KEY:
    raise RuntimeError("Please set DATABASE_URL and PERPLEXITY_API_KEY environment variables")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Database initialized")
    yield
    print("Application shutting down")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # In production, restrict this to specific domains
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Include routers
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(breaches.router, prefix="/breaches", tags=["breaches"])

# Register vulnerability routes
security_vulnerability.register_vulnerability_routes(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
