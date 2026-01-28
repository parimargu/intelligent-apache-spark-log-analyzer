"""
Log-related Pydantic schemas (DTOs).
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class LogLevelEnum(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class IngestionSourceEnum(str, Enum):
    """Source of log ingestion."""
    UPLOAD = "upload"
    FOLDER_WATCH = "folder_watch"
    API = "api"


# Log File Schemas
class LogFileBase(BaseModel):
    """Base schema for log files."""
    filename: str
    original_filename: str
    file_size: int
    source: IngestionSourceEnum = IngestionSourceEnum.UPLOAD


class LogFileCreate(LogFileBase):
    """Schema for creating a log file entry."""
    file_path: str
    file_hash: Optional[str] = None
    mime_type: Optional[str] = None


class LogFileResponse(LogFileBase):
    """Schema for log file response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    file_path: str
    file_hash: Optional[str] = None
    mime_type: Optional[str] = None
    spark_mode: Optional[str] = None
    detected_language: Optional[str] = None
    is_processed: bool = False
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Summary counts
    entry_count: Optional[int] = Field(default=0, description="Number of log entries")
    error_count: Optional[int] = Field(default=0, description="Number of errors")
    warning_count: Optional[int] = Field(default=0, description="Number of warnings")


class LogFileListResponse(BaseModel):
    """Paginated list of log files."""
    items: List[LogFileResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Log Entry Schemas
class LogEntryBase(BaseModel):
    """Base schema for log entries."""
    timestamp: Optional[datetime] = None
    level: Optional[LogLevelEnum] = None
    component: Optional[str] = None
    message: str
    line_number: int


class LogEntryResponse(LogEntryBase):
    """Schema for log entry response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    log_file_id: int
    executor_id: Optional[str] = None
    raw_line: str
    has_stack_trace: bool = False
    stack_trace: Optional[str] = None
    exception_type: Optional[str] = None
    category: Optional[str] = None
    is_error: bool = False
    is_warning: bool = False
    created_at: datetime


class LogEntryListResponse(BaseModel):
    """Paginated list of log entries."""
    items: List[LogEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Upload Response
class UploadResponse(BaseModel):
    """Response for file upload."""
    message: str
    file_id: int
    filename: str
    file_size: int
    status: str = "uploaded"


class BatchUploadResponse(BaseModel):
    """Response for batch file upload."""
    message: str
    uploaded_files: List[UploadResponse]
    failed_files: List[dict]
    total_uploaded: int
    total_failed: int
