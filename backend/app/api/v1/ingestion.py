"""
Log Ingestion API endpoints.
"""

import os
import hashlib
import gzip
import zipfile
from pathlib import Path
from typing import List
from datetime import datetime

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_async_session
from app.models.log import LogFile, IngestionSource
from app.schemas.log import LogFileResponse, UploadResponse, BatchUploadResponse
from app.core.dependencies import require_ingestion_permission
from app.services.ingestion import IngestionService
from app.services.parser import LogParserService


router = APIRouter()
settings = get_settings()


def get_file_hash(content: bytes) -> str:
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def is_valid_extension(filename: str) -> bool:
    """Check if file extension is supported."""
    ext = Path(filename).suffix.lower()
    return ext in settings.supported_extensions_list


@router.post("/upload", response_model=UploadResponse)
async def upload_log_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_session),
    _: bool = Depends(require_ingestion_permission)
):
    """
    Upload a single log file.
    
    Supports .log, .txt, .gz, and .zip files.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    if not is_valid_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {settings.supported_extensions}"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Check file size
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB"
        )
    
    # Generate unique filename
    file_hash = get_file_hash(content)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file_hash[:8]}_{file.filename}"
    
    # Save file
    upload_path = Path(settings.log_upload_dir) / safe_filename
    async with aiofiles.open(upload_path, 'wb') as f:
        await f.write(content)
    
    # Create database record
    log_file = LogFile(
        filename=safe_filename,
        original_filename=file.filename,
        file_path=str(upload_path),
        file_size=file_size,
        file_hash=file_hash,
        source=IngestionSource.UPLOAD,
        mime_type=file.content_type
    )
    
    db.add(log_file)
    await db.commit()
    await db.refresh(log_file)
    
    # Schedule background parsing
    background_tasks.add_task(
        parse_log_file_background,
        log_file.id,
        str(upload_path)
    )
    
    return UploadResponse(
        message="File uploaded successfully",
        file_id=log_file.id,
        filename=log_file.original_filename,
        file_size=log_file.file_size,
        status="uploaded"
    )


@router.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_session),
    _: bool = Depends(require_ingestion_permission)
):
    """
    Upload multiple log files at once.
    """
    uploaded = []
    failed = []
    
    for file in files:
        try:
            if not file.filename:
                failed.append({"filename": "unknown", "error": "No filename"})
                continue
            
            if not is_valid_extension(file.filename):
                failed.append({
                    "filename": file.filename,
                    "error": f"Unsupported file type"
                })
                continue
            
            # Process file
            content = await file.read()
            file_size = len(content)
            
            max_size = settings.max_upload_size_mb * 1024 * 1024
            if file_size > max_size:
                failed.append({
                    "filename": file.filename,
                    "error": f"File too large (max {settings.max_upload_size_mb}MB)"
                })
                continue
            
            # Save file
            file_hash = get_file_hash(content)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file_hash[:8]}_{file.filename}"
            upload_path = Path(settings.log_upload_dir) / safe_filename
            
            async with aiofiles.open(upload_path, 'wb') as f:
                await f.write(content)
            
            # Create database record
            log_file = LogFile(
                filename=safe_filename,
                original_filename=file.filename,
                file_path=str(upload_path),
                file_size=file_size,
                file_hash=file_hash,
                source=IngestionSource.UPLOAD,
                mime_type=file.content_type
            )
            
            db.add(log_file)
            await db.commit()
            await db.refresh(log_file)
            
            # Schedule background parsing
            background_tasks.add_task(
                parse_log_file_background,
                log_file.id,
                str(upload_path)
            )
            
            uploaded.append(UploadResponse(
                message="File uploaded successfully",
                file_id=log_file.id,
                filename=log_file.original_filename,
                file_size=log_file.file_size,
                status="uploaded"
            ))
            
        except Exception as e:
            failed.append({
                "filename": file.filename or "unknown",
                "error": str(e)
            })
    
    return BatchUploadResponse(
        message=f"Processed {len(files)} files",
        uploaded_files=uploaded,
        failed_files=failed,
        total_uploaded=len(uploaded),
        total_failed=len(failed)
    )


@router.post("/api-ingest", response_model=UploadResponse)
async def api_ingest_log(
    content: str,
    filename: str = "api_log.log",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_session),
    _: bool = Depends(require_ingestion_permission)
):
    """
    Programmatic log ingestion via API.
    
    Send raw log content as text.
    """
    content_bytes = content.encode('utf-8')
    file_size = len(content_bytes)
    file_hash = get_file_hash(content_bytes)
    
    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file_hash[:8]}_{filename}"
    upload_path = Path(settings.log_upload_dir) / safe_filename
    
    # Save file
    async with aiofiles.open(upload_path, 'wb') as f:
        await f.write(content_bytes)
    
    # Create database record
    log_file = LogFile(
        filename=safe_filename,
        original_filename=filename,
        file_path=str(upload_path),
        file_size=file_size,
        file_hash=file_hash,
        source=IngestionSource.API,
        mime_type="text/plain"
    )
    
    db.add(log_file)
    await db.commit()
    await db.refresh(log_file)
    
    # Schedule background parsing
    background_tasks.add_task(
        parse_log_file_background,
        log_file.id,
        str(upload_path)
    )
    
    return UploadResponse(
        message="Log ingested successfully",
        file_id=log_file.id,
        filename=log_file.original_filename,
        file_size=log_file.file_size,
        status="uploaded"
    )


async def parse_log_file_background(log_file_id: int, file_path: str):
    """Background task to parse uploaded log file."""
    from app.db import async_session_context
    
    async with async_session_context() as db:
        try:
            parser_service = LogParserService()
            await parser_service.parse_and_store(db, log_file_id, file_path)
        except Exception as e:
            # Update file with error
            from sqlalchemy import select
            result = await db.execute(
                select(LogFile).where(LogFile.id == log_file_id)
            )
            log_file = result.scalar_one_or_none()
            if log_file:
                log_file.error_message = str(e)
                await db.commit()
