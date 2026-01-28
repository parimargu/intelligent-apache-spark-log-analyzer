"""
Log Parsing and Normalization Engine.

Parses Apache Spark logs from various sources:
- Spark Standalone
- Spark on YARN
- Spark on Kubernetes

Supports logs from multiple languages:
- Python (PySpark)
- Scala
- Java
- SQL
- R (SparkR)
"""

import re
import gzip
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass
from enum import Enum

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.log import LogFile, LogEntry, LogLevel


class SparkMode(str, Enum):
    """Spark deployment mode."""
    STANDALONE = "standalone"
    YARN = "yarn"
    KUBERNETES = "kubernetes"
    LOCAL = "local"
    UNKNOWN = "unknown"


class SparkLanguage(str, Enum):
    """Programming language used with Spark."""
    PYTHON = "python"
    SCALA = "scala"
    JAVA = "java"
    SQL = "sql"
    R = "r"
    UNKNOWN = "unknown"


@dataclass
class ParsedLogEntry:
    """Parsed log entry data structure."""
    line_number: int
    raw_line: str
    timestamp: Optional[datetime] = None
    level: Optional[LogLevel] = None
    component: Optional[str] = None
    executor_id: Optional[str] = None
    message: str = ""
    has_stack_trace: bool = False
    stack_trace: Optional[str] = None
    exception_type: Optional[str] = None
    category: Optional[str] = None
    is_error: bool = False
    is_warning: bool = False


class LogParserService:
    """Service for parsing and normalizing Spark logs."""
    
    # Log level patterns
    LOG_LEVEL_PATTERN = re.compile(
        r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|SEVERE)\b',
        re.IGNORECASE
    )
    
    # Timestamp patterns (multiple formats)
    TIMESTAMP_PATTERNS = [
        # ISO format: 2024-01-28 10:30:45,123
        re.compile(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[,\.]\d{3})'),
        # Spark default: 24/01/28 10:30:45
        re.compile(r'(\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})'),
        # Unix timestamp
        re.compile(r'timestamp[=:]\s*(\d{10,13})'),
    ]
    
    # Component patterns
    COMPONENT_PATTERNS = [
        re.compile(r'\[([A-Za-z][A-Za-z0-9_\-.]+)\]'),
        re.compile(r'(\w+Context|\w+Executor|\w+Driver|\w+Manager)'),
    ]
    
    # Executor ID pattern
    EXECUTOR_PATTERN = re.compile(r'executor[_\s-]?(\d+|driver)', re.IGNORECASE)
    
    # Exception patterns
    EXCEPTION_PATTERNS = [
        re.compile(r'([\w.]+Exception):\s*(.+)'),
        re.compile(r'([\w.]+Error):\s*(.+)'),
        re.compile(r'Caused by:\s*([\w.]+(?:Exception|Error))'),
    ]
    
    # Stack trace indicators
    STACK_TRACE_PATTERN = re.compile(r'^\s+at\s+[\w.$]+\(.*\)$')
    
    # Language detection patterns
    LANGUAGE_PATTERNS = {
        SparkLanguage.PYTHON: [
            re.compile(r'pyspark|python|\.py\b', re.IGNORECASE),
            re.compile(r'Traceback \(most recent call last\)'),
            re.compile(r'File ".*\.py"'),
        ],
        SparkLanguage.SCALA: [
            re.compile(r'scala\.|\.scala\b', re.IGNORECASE),
            re.compile(r'at scala\.'),
        ],
        SparkLanguage.JAVA: [
            re.compile(r'java\.|\.java\b', re.IGNORECASE),
            re.compile(r'at java\.'),
            re.compile(r'at org\.apache\.spark'),
        ],
        SparkLanguage.SQL: [
            re.compile(r'spark\.sql|SparkSQL', re.IGNORECASE),
            re.compile(r'SELECT|INSERT|UPDATE|CREATE TABLE', re.IGNORECASE),
        ],
        SparkLanguage.R: [
            re.compile(r'sparkR|\.r\b', re.IGNORECASE),
        ],
    }
    
    # Spark mode detection patterns
    MODE_PATTERNS = {
        SparkMode.YARN: [
            re.compile(r'yarn|ApplicationMaster|container_', re.IGNORECASE),
        ],
        SparkMode.KUBERNETES: [
            re.compile(r'kubernetes|k8s|pod_', re.IGNORECASE),
        ],
        SparkMode.STANDALONE: [
            re.compile(r'spark://|master.*standalone', re.IGNORECASE),
        ],
        SparkMode.LOCAL: [
            re.compile(r'local\[\d*\*?\]', re.IGNORECASE),
        ],
    }
    
    # Error category patterns
    ERROR_CATEGORIES = {
        'memory': [
            re.compile(r'OutOfMemory|OOM|heap space|GC overhead', re.IGNORECASE),
        ],
        'shuffle': [
            re.compile(r'shuffle|FetchFailed|ShuffleMapTask', re.IGNORECASE),
        ],
        'network': [
            re.compile(r'connection|timeout|refused|network', re.IGNORECASE),
        ],
        'serialization': [
            re.compile(r'serializ|deserializ|NotSerializable', re.IGNORECASE),
        ],
        'configuration': [
            re.compile(r'config|property|setting|parameter', re.IGNORECASE),
        ],
        'permission': [
            re.compile(r'permission|access denied|authorization', re.IGNORECASE),
        ],
        'storage': [
            re.compile(r'disk|storage|hdfs|s3|file not found', re.IGNORECASE),
        ],
        'executor': [
            re.compile(r'executor.*lost|executor.*failed|heartbeat', re.IGNORECASE),
        ],
    }
    
    def __init__(self):
        self._language_cache: Dict[str, SparkLanguage] = {}
        self._mode_cache: Dict[str, SparkMode] = {}
    
    async def parse_and_store(
        self,
        db: AsyncSession,
        log_file_id: int,
        file_path: str
    ) -> int:
        """
        Parse a log file and store entries in the database.
        
        Returns the number of entries created.
        """
        # Get log file record
        result = await db.execute(select(LogFile).where(LogFile.id == log_file_id))
        log_file = result.scalar_one_or_none()
        
        if not log_file:
            raise ValueError(f"Log file with id {log_file_id} not found")
        
        # Read and parse content
        content = await self._read_file(file_path)
        lines = content.splitlines()
        
        # Detect language and mode
        detected_language = self._detect_language(content)
        detected_mode = self._detect_spark_mode(content)
        
        # Parse entries
        entries = list(self._parse_lines(lines))
        
        # Store entries
        entry_count = 0
        for entry in entries:
            log_entry = LogEntry(
                log_file_id=log_file_id,
                timestamp=entry.timestamp,
                level=entry.level,
                component=entry.component,
                executor_id=entry.executor_id,
                message=entry.message,
                raw_line=entry.raw_line,
                line_number=entry.line_number,
                has_stack_trace=entry.has_stack_trace,
                stack_trace=entry.stack_trace,
                exception_type=entry.exception_type,
                category=entry.category,
                is_error=entry.is_error,
                is_warning=entry.is_warning
            )
            db.add(log_entry)
            entry_count += 1
        
        # Update log file metadata
        log_file.is_processed = True
        log_file.processed_at = datetime.utcnow()
        log_file.detected_language = detected_language.value
        log_file.spark_mode = detected_mode.value
        
        await db.commit()
        
        return entry_count
    
    async def _read_file(self, file_path: str) -> str:
        """Read file content, handling compression."""
        path = Path(file_path)
        
        if path.suffix == '.gz':
            with gzip.open(path, 'rt', encoding='utf-8', errors='replace') as f:
                return f.read()
        elif path.suffix == '.zip':
            with zipfile.ZipFile(path, 'r') as zf:
                # Read first file in archive
                for name in zf.namelist():
                    if not name.endswith('/'):
                        with zf.open(name) as f:
                            return f.read().decode('utf-8', errors='replace')
            return ""
        else:
            async with aiofiles.open(path, 'r', encoding='utf-8', errors='replace') as f:
                return await f.read()
    
    def _parse_lines(self, lines: List[str]) -> Generator[ParsedLogEntry, None, None]:
        """Parse log lines into structured entries."""
        current_entry: Optional[ParsedLogEntry] = None
        stack_trace_lines: List[str] = []
        collecting_stack_trace = False
        
        for line_number, line in enumerate(lines, start=1):
            line = line.rstrip()
            
            if not line:
                continue
            
            # Check if this is a stack trace continuation
            if self.STACK_TRACE_PATTERN.match(line) or (
                collecting_stack_trace and line.startswith('\t')
            ):
                collecting_stack_trace = True
                stack_trace_lines.append(line)
                continue
            
            # Check if this is a new log entry
            level_match = self.LOG_LEVEL_PATTERN.search(line)
            
            if level_match:
                # Yield previous entry if exists
                if current_entry:
                    if stack_trace_lines:
                        current_entry.has_stack_trace = True
                        current_entry.stack_trace = '\n'.join(stack_trace_lines)
                    yield current_entry
                
                # Start new entry
                current_entry = self._parse_single_line(line_number, line)
                stack_trace_lines = []
                collecting_stack_trace = False
            elif current_entry:
                # Continuation of previous entry
                current_entry.message += '\n' + line
                
                # Check for exception in continuation
                if not current_entry.exception_type:
                    for pattern in self.EXCEPTION_PATTERNS:
                        exc_match = pattern.search(line)
                        if exc_match:
                            current_entry.exception_type = exc_match.group(1)
                            break
        
        # Yield final entry
        if current_entry:
            if stack_trace_lines:
                current_entry.has_stack_trace = True
                current_entry.stack_trace = '\n'.join(stack_trace_lines)
            yield current_entry
    
    def _parse_single_line(self, line_number: int, line: str) -> ParsedLogEntry:
        """Parse a single log line."""
        entry = ParsedLogEntry(
            line_number=line_number,
            raw_line=line,
            message=line
        )
        
        # Extract log level
        level_match = self.LOG_LEVEL_PATTERN.search(line)
        if level_match:
            level_str = level_match.group(1).upper()
            if level_str == 'WARNING':
                level_str = 'WARN'
            if level_str == 'SEVERE':
                level_str = 'FATAL'
            
            try:
                entry.level = LogLevel(level_str)
                entry.is_error = level_str in ('ERROR', 'FATAL')
                entry.is_warning = level_str == 'WARN'
            except ValueError:
                pass
        
        # Extract timestamp
        for pattern in self.TIMESTAMP_PATTERNS:
            ts_match = pattern.search(line)
            if ts_match:
                entry.timestamp = self._parse_timestamp(ts_match.group(1))
                break
        
        # Extract component
        for pattern in self.COMPONENT_PATTERNS:
            comp_match = pattern.search(line)
            if comp_match:
                entry.component = comp_match.group(1)
                break
        
        # Extract executor ID
        exec_match = self.EXECUTOR_PATTERN.search(line)
        if exec_match:
            entry.executor_id = exec_match.group(1)
        
        # Check for exception
        for pattern in self.EXCEPTION_PATTERNS:
            exc_match = pattern.search(line)
            if exc_match:
                entry.exception_type = exc_match.group(1)
                entry.is_error = True
                break
        
        # Categorize errors
        if entry.is_error or entry.is_warning:
            entry.category = self._categorize_error(line)
        
        return entry
    
    def _parse_timestamp(self, ts_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime."""
        formats = [
            '%Y-%m-%d %H:%M:%S,%f',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%y/%m/%d %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue
        
        # Try unix timestamp
        try:
            ts_int = int(ts_str)
            if ts_int > 1e12:  # Milliseconds
                ts_int = ts_int / 1000
            return datetime.fromtimestamp(ts_int)
        except (ValueError, OSError):
            pass
        
        return None
    
    def _detect_language(self, content: str) -> SparkLanguage:
        """Detect the programming language from log content."""
        scores: Dict[SparkLanguage, int] = {}
        
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            score = sum(1 for p in patterns if p.search(content))
            if score > 0:
                scores[lang] = score
        
        if scores:
            return max(scores.keys(), key=lambda k: scores[k])
        
        return SparkLanguage.UNKNOWN
    
    def _detect_spark_mode(self, content: str) -> SparkMode:
        """Detect Spark deployment mode from log content."""
        for mode, patterns in self.MODE_PATTERNS.items():
            if any(p.search(content) for p in patterns):
                return mode
        
        return SparkMode.UNKNOWN
    
    def _categorize_error(self, line: str) -> Optional[str]:
        """Categorize an error line."""
        for category, patterns in self.ERROR_CATEGORIES.items():
            if any(p.search(line) for p in patterns):
                return category
        
        return None
