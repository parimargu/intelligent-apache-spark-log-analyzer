"""
Reports API endpoints.
"""

from typing import Optional
from math import ceil
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db import get_async_session
from app.models.log import LogFile, LogEntry, LogAnalysis
from app.models.analysis import AnalysisReport
from app.schemas.analysis import (
    ReportRequest, ReportResponse, ReportListResponse,
    DashboardSummary, ErrorCategory
)
from app.core.dependencies import get_current_active_user, get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get dashboard summary with key metrics."""
    # Total log files
    total_files_result = await db.execute(select(func.count(LogFile.id)))
    total_log_files = total_files_result.scalar() or 0
    
    # Processed vs pending
    processed_result = await db.execute(
        select(func.count(LogFile.id)).where(LogFile.is_processed == True)
    )
    processed_files = processed_result.scalar() or 0
    pending_files = total_log_files - processed_files
    
    # Total entries
    total_entries_result = await db.execute(select(func.count(LogEntry.id)))
    total_log_entries = total_entries_result.scalar() or 0
    
    # Total errors
    error_result = await db.execute(
        select(func.count(LogEntry.id)).where(LogEntry.is_error == True)
    )
    total_errors = error_result.scalar() or 0
    
    # Total warnings
    warning_result = await db.execute(
        select(func.count(LogEntry.id)).where(LogEntry.is_warning == True)
    )
    total_warnings = warning_result.scalar() or 0
    
    # Error trend (last 7 days)
    error_trend = []
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        day_start = datetime.combine(date, datetime.min.time())
        day_end = datetime.combine(date, datetime.max.time())
        
        day_errors_result = await db.execute(
            select(func.count(LogEntry.id)).where(
                and_(
                    LogEntry.is_error == True,
                    LogEntry.created_at >= day_start,
                    LogEntry.created_at <= day_end
                )
            )
        )
        day_errors = day_errors_result.scalar() or 0
        error_trend.append({
            "date": date.isoformat(),
            "count": day_errors
        })
    
    # Top error categories
    category_result = await db.execute(
        select(LogEntry.category, func.count(LogEntry.id).label('count'))
        .where(and_(LogEntry.is_error == True, LogEntry.category.isnot(None)))
        .group_by(LogEntry.category)
        .order_by(func.count(LogEntry.id).desc())
        .limit(5)
    )
    top_categories = []
    for row in category_result:
        if row.category:
            pct = (row.count / total_errors * 100) if total_errors > 0 else 0
            top_categories.append(ErrorCategory(
                category=row.category,
                count=row.count,
                percentage=round(pct, 1),
                examples=[]
            ))
    
    return DashboardSummary(
        total_log_files=total_log_files,
        total_log_entries=total_log_entries,
        total_errors=total_errors,
        total_warnings=total_warnings,
        processed_files=processed_files,
        pending_files=pending_files,
        error_trend=error_trend,
        top_error_categories=top_categories
    )


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """Generate a new analysis report."""
    # Build log file filter
    query = select(LogFile).where(LogFile.is_processed == True)
    
    if request.log_file_ids:
        query = query.where(LogFile.id.in_(request.log_file_ids))
    
    if request.date_from:
        query = query.where(LogFile.created_at >= request.date_from)
    
    if request.date_to:
        query = query.where(LogFile.created_at <= request.date_to)
    
    result = await db.execute(query)
    log_files = result.scalars().all()
    
    if not log_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No processed log files found matching criteria"
        )
    
    log_file_ids = [f.id for f in log_files]
    
    # Aggregate metrics
    total_errors_result = await db.execute(
        select(func.count(LogEntry.id)).where(
            and_(
                LogEntry.log_file_id.in_(log_file_ids),
                LogEntry.is_error == True
            )
        )
    )
    total_errors = total_errors_result.scalar() or 0
    
    total_warnings_result = await db.execute(
        select(func.count(LogEntry.id)).where(
            and_(
                LogEntry.log_file_id.in_(log_file_ids),
                LogEntry.is_warning == True
            )
        )
    )
    total_warnings = total_warnings_result.scalar() or 0
    
    # Error categories
    category_result = await db.execute(
        select(LogEntry.category, func.count(LogEntry.id).label('count'))
        .where(
            and_(
                LogEntry.log_file_id.in_(log_file_ids),
                LogEntry.is_error == True,
                LogEntry.category.isnot(None)
            )
        )
        .group_by(LogEntry.category)
        .order_by(func.count(LogEntry.id).desc())
    )
    
    error_categories = {}
    for row in category_result:
        error_categories[row.category] = row.count
    
    # Create report
    report = AnalysisReport(
        name=request.name,
        description=request.description,
        report_type=request.report_type,
        total_logs_analyzed=len(log_files),
        total_errors=total_errors,
        total_warnings=total_warnings,
        error_categories=error_categories
    )
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Build response with proper error category format
    error_category_list = [
        ErrorCategory(
            category=cat,
            count=cnt,
            percentage=round((cnt / total_errors * 100) if total_errors > 0 else 0, 1),
            examples=[]
        )
        for cat, cnt in error_categories.items()
    ]
    
    return ReportResponse(
        id=report.id,
        name=report.name,
        description=report.description,
        report_type=report.report_type,
        total_logs_analyzed=report.total_logs_analyzed,
        total_errors=report.total_errors,
        total_warnings=report.total_warnings,
        error_categories=error_category_list,
        created_at=report.created_at,
        updated_at=report.updated_at
    )


@router.get("", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    report_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user)
):
    """List all reports with pagination."""
    query = select(AnalysisReport)
    count_query = select(func.count(AnalysisReport.id))
    
    if report_type:
        query = query.where(AnalysisReport.report_type == report_type)
        count_query = count_query.where(AnalysisReport.report_type == report_type)
    
    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(AnalysisReport.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    return ReportListResponse(
        items=[
            ReportResponse(
                id=r.id,
                name=r.name,
                description=r.description,
                report_type=r.report_type,
                total_logs_analyzed=r.total_logs_analyzed,
                total_errors=r.total_errors,
                total_warnings=r.total_warnings,
                error_categories=[
                    ErrorCategory(
                        category=cat,
                        count=cnt,
                        percentage=round((cnt / r.total_errors * 100) if r.total_errors > 0 else 0, 1),
                        examples=[]
                    )
                    for cat, cnt in (r.error_categories or {}).items()
                ],
                created_at=r.created_at,
                updated_at=r.updated_at
            )
            for r in reports
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get a specific report by ID."""
    result = await db.execute(
        select(AnalysisReport).where(AnalysisReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with id {report_id} not found"
        )
    
    return ReportResponse(
        id=report.id,
        name=report.name,
        description=report.description,
        report_type=report.report_type,
        total_logs_analyzed=report.total_logs_analyzed,
        total_errors=report.total_errors,
        total_warnings=report.total_warnings,
        error_categories=[
            ErrorCategory(
                category=cat,
                count=cnt,
                percentage=round((cnt / report.total_errors * 100) if report.total_errors > 0 else 0, 1),
                examples=[]
            )
            for cat, cnt in (report.error_categories or {}).items()
        ],
        created_at=report.created_at,
        updated_at=report.updated_at
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a report."""
    result = await db.execute(
        select(AnalysisReport).where(AnalysisReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with id {report_id} not found"
        )
    
    await db.delete(report)
    await db.commit()
