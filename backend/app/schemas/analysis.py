"""
Analysis and report Pydantic schemas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class AnalysisTypeEnum(str, Enum):
    """Analysis type enumeration."""
    ROOT_CAUSE = "root_cause"
    MEMORY_ISSUES = "memory_issues"
    PERFORMANCE = "performance"
    CONFIG_OPTIMIZATION = "config_optimization"
    FULL = "full"


class SeverityEnum(str, Enum):
    """Severity level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LLMProviderEnum(str, Enum):
    """LLM provider enumeration."""
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


# Analysis Request/Response
class AnalysisRequest(BaseModel):
    """Schema for analysis request."""
    log_file_id: int
    analysis_type: AnalysisTypeEnum = AnalysisTypeEnum.FULL
    llm_provider: Optional[LLMProviderEnum] = None  # Uses default if not specified
    include_recommendations: bool = True
    include_config_suggestions: bool = True


class Recommendation(BaseModel):
    """A single recommendation."""
    title: str
    description: str
    priority: SeverityEnum
    category: str
    code_example: Optional[str] = None


class ConfigSuggestion(BaseModel):
    """A Spark configuration suggestion."""
    config_key: str
    current_value: Optional[str] = None
    suggested_value: str
    reason: str
    impact: str


class AnalysisResponse(BaseModel):
    """Schema for analysis response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    log_file_id: int
    analysis_type: str
    llm_provider: str
    llm_model: str
    
    # Analysis results
    summary: Optional[str] = None
    root_cause: Optional[str] = None
    severity: Optional[SeverityEnum] = None
    recommendations: Optional[List[Recommendation]] = None
    config_suggestions: Optional[List[ConfigSuggestion]] = None
    
    # Metadata
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime


class AnalysisListResponse(BaseModel):
    """Paginated list of analyses."""
    items: List[AnalysisResponse]
    total: int
    page: int
    page_size: int


# Report Schemas
class ReportRequest(BaseModel):
    """Schema for report generation request."""
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    report_type: str = "summary"
    log_file_ids: Optional[List[int]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ErrorCategory(BaseModel):
    """Error category breakdown."""
    category: str
    count: int
    percentage: float
    examples: List[str] = Field(default_factory=list)


class ReportResponse(BaseModel):
    """Schema for report response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    report_type: str
    
    # Aggregated data
    total_logs_analyzed: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    
    # Issue breakdown
    error_categories: Optional[List[ErrorCategory]] = None
    performance_issues: Optional[Dict[str, Any]] = None
    config_issues: Optional[Dict[str, Any]] = None
    
    # AI insights
    insights: Optional[List[str]] = None
    recommendations: Optional[List[Recommendation]] = None
    
    created_at: datetime
    updated_at: datetime


class ReportListResponse(BaseModel):
    """Paginated list of reports."""
    items: List[ReportResponse]
    total: int
    page: int
    page_size: int


# Dashboard Summary
class DashboardSummary(BaseModel):
    """Summary data for dashboard."""
    total_log_files: int = 0
    total_log_entries: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    processed_files: int = 0
    pending_files: int = 0
    
    # Trends (last 7 days)
    error_trend: List[Dict[str, Any]] = Field(default_factory=list)
    log_volume_trend: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Top issues
    top_error_categories: List[ErrorCategory] = Field(default_factory=list)
    recent_critical_issues: List[Dict[str, Any]] = Field(default_factory=list)
