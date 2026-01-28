"""
Analysis result models.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Index

from app.db import Base


class AnalysisReport(Base):
    """Aggregated analysis report model."""
    
    __tablename__ = "analysis_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Report type
    report_type = Column(String(50), nullable=False)  # summary, detailed, trend
    
    # Aggregated data
    total_logs_analyzed = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    total_warnings = Column(Integer, default=0)
    
    # Issue breakdown
    error_categories = Column(JSON, nullable=True)  # {"memory": 10, "oom": 5, ...}
    performance_issues = Column(JSON, nullable=True)
    config_issues = Column(JSON, nullable=True)
    
    # AI insights
    insights = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("ix_analysis_reports_report_type", "report_type"),
        Index("ix_analysis_reports_created_at", "created_at"),
    )
