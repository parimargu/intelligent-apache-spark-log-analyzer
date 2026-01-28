"""
Analysis API endpoints.
"""

from typing import Optional
from math import ceil
import time

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db import get_async_session
from app.models.log import LogFile, LogAnalysis
from app.schemas.analysis import (
    AnalysisRequest, AnalysisResponse, AnalysisListResponse,
    AnalysisTypeEnum, LLMProviderEnum
)
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.llm import LLMService
from app.config import get_settings


router = APIRouter()
settings = get_settings()


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger AI analysis on a log file.
    
    Uses the configured LLM provider to analyze logs and generate insights.
    """
    # Verify log file exists
    result = await db.execute(
        select(LogFile).where(LogFile.id == request.log_file_id)
    )
    log_file = result.scalar_one_or_none()
    
    if not log_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log file with id {request.log_file_id} not found"
        )
    
    if not log_file.is_processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Log file has not been processed yet. Please wait for parsing to complete."
        )
    
    # Determine LLM provider
    provider = request.llm_provider or LLMProviderEnum(settings.default_llm_provider)
    
    # Create LLM service and analyze
    start_time = time.time()
    llm_service = LLMService(provider=provider.value)
    
    try:
        analysis_result = await llm_service.analyze_logs(
            db=db,
            log_file_id=request.log_file_id,
            analysis_type=request.analysis_type.value
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM analysis failed: {str(e)}"
        )
    
    processing_time = int((time.time() - start_time) * 1000)
    
    # Store analysis result
    analysis = LogAnalysis(
        log_file_id=request.log_file_id,
        analysis_type=request.analysis_type.value,
        llm_provider=provider.value,
        llm_model=llm_service.model_name,
        summary=analysis_result.get("summary"),
        root_cause=analysis_result.get("root_cause"),
        recommendations=analysis_result.get("recommendations"),
        config_suggestions=analysis_result.get("config_suggestions"),
        severity=analysis_result.get("severity"),
        tokens_used=analysis_result.get("tokens_used"),
        processing_time_ms=processing_time
    )
    
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    
    return AnalysisResponse.model_validate(analysis)


@router.get("", response_model=AnalysisListResponse)
async def list_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    log_file_id: Optional[int] = Query(None, description="Filter by log file"),
    analysis_type: Optional[str] = Query(None, description="Filter by analysis type"),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """List all analyses with filtering and pagination."""
    # Build query
    query = select(LogAnalysis)
    count_query = select(func.count(LogAnalysis.id))
    
    if log_file_id:
        query = query.where(LogAnalysis.log_file_id == log_file_id)
        count_query = count_query.where(LogAnalysis.log_file_id == log_file_id)
    
    if analysis_type:
        query = query.where(LogAnalysis.analysis_type == analysis_type)
        count_query = count_query.where(LogAnalysis.analysis_type == analysis_type)
    
    # Get total
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(LogAnalysis.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    analyses = result.scalars().all()
    
    return AnalysisListResponse(
        items=[AnalysisResponse.model_validate(a) for a in analyses],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """Get a specific analysis by ID."""
    result = await db.execute(
        select(LogAnalysis).where(LogAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with id {analysis_id} not found"
        )
    
    return AnalysisResponse.model_validate(analysis)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an analysis."""
    result = await db.execute(
        select(LogAnalysis).where(LogAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with id {analysis_id} not found"
        )
    
    await db.delete(analysis)
    await db.commit()
