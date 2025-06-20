"""
FastAPI Job Application Management Backend
Main application entry point with all route configurations
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import engine, Base
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.resumes import router as resumes_router
from routers.applications import router as applications_router
from routers.services import router as services_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise HTTPException(status_code=500, detail="Database initialization failed")
    finally:
        logger.info("Application shutdown")


# Create FastAPI application
app = FastAPI(
    title="Job Application Management API",
    description="A comprehensive backend for managing job applications, resumes, and user authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/user", tags=["Users"])
app.include_router(resumes_router, prefix="/resume", tags=["Resumes"])
app.include_router(applications_router, prefix="/applications", tags=["Applications"])
app.include_router(services_router, prefix="/services", tags=["External Services"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Job Application Management API is running"}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Job Application Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 5000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
