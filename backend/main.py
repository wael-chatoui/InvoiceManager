from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from routes.invoices import router as invoices_router
from routes.auth import router as auth_router

app = FastAPI(
    title="Invoice Generator API",
    description="API for generating invoices and estimates",
    version="1.0.0"
)

# CORS configuration - build allowed origins list
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

# Add frontend URL from environment (for production)
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    # Support comma-separated URLs for multiple frontends
    for url in frontend_url.split(","):
        url = url.strip()
        if url and url not in allowed_origins:
            allowed_origins.append(url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(invoices_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Invoice Generator API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
