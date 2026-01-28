"""
API v1 module.
"""

from fastapi import APIRouter

from app.api.v1 import auth, ingestion, logs, analysis, reports


router = APIRouter()

# Include route modules
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(ingestion.router, prefix="/ingestion", tags=["Log Ingestion"])
router.include_router(logs.router, prefix="/logs", tags=["Logs"])
router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
