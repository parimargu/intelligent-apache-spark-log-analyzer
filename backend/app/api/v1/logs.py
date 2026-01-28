"""
Logs API endpoints.
"""

from typing import Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db import get_async_session
from app.models.log import LogFile, LogEntry, LogLevel
from app.schemas.log import (
    LogFileResponse, LogFileListResponse,
    LogEntryResponse, LogEntryListResponse
)
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("", response_model=LogFileListResponse)
async def list_log_files(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_processed: Optional[bool] = Query(None, description="Filter by processed status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user)
):
    """List all ingested log files with pagination."""
    # Build query
    query = select(LogFile)
    count_query = select(func.count(LogFile.id))
    
    # Apply filters
    if is_processed is not None:
        query = query.where(LogFile.is_processed == is_processed)
        count_query = count_query.where(LogFile.is_processed == is_processed)
    
    if source:
        query = query.where(LogFile.source == source)
        count_query = count_query.where(LogFile.source == source)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(LogFile.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    files = result.scalars().all()
    
    # Add entry counts
    file_responses = []
    for log_file in files:
        # Get entry counts
        entry_count_result = await db.execute(
            select(func.count(LogEntry.id)).where(LogEntry.log_file_id == log_file.id)
        )
        entry_count = entry_count_result.scalar() or 0
        
        error_count_result = await db.execute(
            select(func.count(LogEntry.id)).where(
                and_(LogEntry.log_file_id == log_file.id, LogEntry.is_error == True)
            )
        )
        error_count = error_count_result.scalar() or 0
        
        warning_count_result = await db.execute(
            select(func.count(LogEntry.id)).where(
                and_(LogEntry.log_file_id == log_file.id, LogEntry.is_warning == True)
            )
        )
        warning_count = warning_count_result.scalar() or 0
        
        file_response = LogFileResponse(
            id=log_file.id,
            filename=log_file.filename,
            original_filename=log_file.original_filename,
            file_path=log_file.file_path,
            file_size=log_file.file_size,
            file_hash=log_file.file_hash,
            source=log_file.source,
            mime_type=log_file.mime_type,
            spark_mode=log_file.spark_mode,
            detected_language=log_file.detected_language,
            is_processed=log_file.is_processed,
            processed_at=log_file.processed_at,
            error_message=log_file.error_message,
            created_at=log_file.created_at,
            updated_at=log_file.updated_at,
            entry_count=entry_count,
            error_count=error_count,
            warning_count=warning_count
        )
        file_responses.append(file_response)
    
    return LogFileListResponse(
        items=file_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total > 0 else 1
    )


@router.get("/{file_id}", response_model=LogFileResponse)
async def get_log_file(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get a specific log file by ID."""
    result = await db.execute(select(LogFile).where(LogFile.id == file_id))
    log_file = result.scalar_one_or_none()
    
    if not log_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log file with id {file_id} not found"
        )
    
    # Get entry counts
    entry_count_result = await db.execute(
        select(func.count(LogEntry.id)).where(LogEntry.log_file_id == file_id)
    )
    entry_count = entry_count_result.scalar() or 0
    
    error_count_result = await db.execute(
        select(func.count(LogEntry.id)).where(
            and_(LogEntry.log_file_id == file_id, LogEntry.is_error == True)
        )
    )
    error_count = error_count_result.scalar() or 0
    
    warning_count_result = await db.execute(
        select(func.count(LogEntry.id)).where(
            and_(LogEntry.log_file_id == file_id, LogEntry.is_warning == True)
        )
    )
    warning_count = warning_count_result.scalar() or 0
    
    return LogFileResponse(
        id=log_file.id,
        filename=log_file.filename,
        original_filename=log_file.original_filename,
        file_path=log_file.file_path,
        file_size=log_file.file_size,
        file_hash=log_file.file_hash,
        source=log_file.source,
        mime_type=log_file.mime_type,
        spark_mode=log_file.spark_mode,
        detected_language=log_file.detected_language,
        is_processed=log_file.is_processed,
        processed_at=log_file.processed_at,
        error_message=log_file.error_message,
        created_at=log_file.created_at,
        updated_at=log_file.updated_at,
        entry_count=entry_count,
        error_count=error_count,
        warning_count=warning_count
    )


@router.get("/{file_id}/entries", response_model=LogEntryListResponse)
async def get_log_entries(
    file_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    level: Optional[str] = Query(None, description="Filter by log level"),
    is_error: Optional[bool] = Query(None, description="Filter errors only"),
    search: Optional[str] = Query(None, description="Search in message"),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get log entries for a specific file with filtering."""
    # Verify file exists
    file_result = await db.execute(select(LogFile).where(LogFile.id == file_id))
    if not file_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log file with id {file_id} not found"
        )
    
    # Build query
    query = select(LogEntry).where(LogEntry.log_file_id == file_id)
    count_query = select(func.count(LogEntry.id)).where(LogEntry.log_file_id == file_id)
    
    # Apply filters
    if level:
        try:
            log_level = LogLevel(level.upper())
            query = query.where(LogEntry.level == log_level)
            count_query = count_query.where(LogEntry.level == log_level)
        except ValueError:
            pass
    
    if is_error is not None:
        query = query.where(LogEntry.is_error == is_error)
        count_query = count_query.where(LogEntry.is_error == is_error)
    
    if search:
        query = query.where(LogEntry.message.ilike(f"%{search}%"))
        count_query = count_query.where(LogEntry.message.ilike(f"%{search}%"))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(LogEntry.line_number).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    return LogEntryListResponse(
        items=[LogEntryResponse.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total > 0 else 1
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log_file(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a log file and its entries."""
    result = await db.execute(select(LogFile).where(LogFile.id == file_id))
    log_file = result.scalar_one_or_none()
    
    if not log_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log file with id {file_id} not found"
        )
    
    # Delete file from filesystem
    import os
    if os.path.exists(log_file.file_path):
        os.remove(log_file.file_path)
    
    # Delete from database (cascade deletes entries)
    await db.delete(log_file)
    await db.commit()
