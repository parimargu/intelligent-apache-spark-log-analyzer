"""
Log-related database models.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum, 
    ForeignKey, Boolean, JSON, Index
)
from sqlalchemy.orm import relationship

from app.db import Base


class LogLevel(str, PyEnum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class IngestionSource(str, PyEnum):
    """Source of log ingestion."""
    UPLOAD = "upload"
    FOLDER_WATCH = "folder_watch"
    API = "api"


class LogFile(Base):
    """Model for ingested log files."""
    
    __tablename__ = "log_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_hash = Column(String(64), nullable=True)  # SHA256 hash
    
    source = Column(Enum(IngestionSource), default=IngestionSource.UPLOAD)
    mime_type = Column(String(100), nullable=True)
    
    # Metadata
    spark_mode = Column(String(50), nullable=True)  # standalone, yarn, kubernetes
    detected_language = Column(String(20), nullable=True)  # python, scala, java, sql, r
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entries = relationship("LogEntry", back_populates="log_file", cascade="all, delete-orphan")
    analyses = relationship("LogAnalysis", back_populates="log_file", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_log_files_created_at", "created_at"),
        Index("ix_log_files_is_processed", "is_processed"),
    )


class LogEntry(Base):
    """Model for individual parsed log entries."""
    
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    log_file_id = Column(Integer, ForeignKey("log_files.id"), nullable=False)
    
    # Log content
    timestamp = Column(DateTime, nullable=True)
    level = Column(Enum(LogLevel), nullable=True)
    component = Column(String(100), nullable=True)  # e.g., "SparkContext", "Executor"
    executor_id = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    raw_line = Column(Text, nullable=False)
    line_number = Column(Integer, nullable=False)
    
    # Stack trace (if applicable)
    has_stack_trace = Column(Boolean, default=False)
    stack_trace = Column(Text, nullable=True)
    exception_type = Column(String(200), nullable=True)
    
    # Classification
    category = Column(String(100), nullable=True)  # memory, performance, config, etc.
    is_error = Column(Boolean, default=False)
    is_warning = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    log_file = relationship("LogFile", back_populates="entries")
    
    # Indexes
    __table_args__ = (
        Index("ix_log_entries_log_file_id", "log_file_id"),
        Index("ix_log_entries_level", "level"),
        Index("ix_log_entries_timestamp", "timestamp"),
        Index("ix_log_entries_is_error", "is_error"),
    )


class LogAnalysis(Base):
    """Model for AI-generated log analysis."""
    
    __tablename__ = "log_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    log_file_id = Column(Integer, ForeignKey("log_files.id"), nullable=False)
    
    # Analysis type
    analysis_type = Column(String(50), nullable=False)  # root_cause, memory, performance, config
    
    # LLM provider used
    llm_provider = Column(String(50), nullable=False)
    llm_model = Column(String(100), nullable=False)
    
    # Analysis results
    summary = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    config_suggestions = Column(JSON, nullable=True)  # Spark config suggestions
    severity = Column(String(20), nullable=True)  # low, medium, high, critical
    
    # Metadata
    tokens_used = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    log_file = relationship("LogFile", back_populates="analyses")
    
    # Indexes
    __table_args__ = (
        Index("ix_log_analyses_log_file_id", "log_file_id"),
        Index("ix_log_analyses_analysis_type", "analysis_type"),
    )
