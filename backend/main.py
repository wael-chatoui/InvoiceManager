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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", "http://localhost:5173")
    ],
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
