"""
Utility functions.
"""

import hashlib
from datetime import datetime
from typing import Optional


def hash_string(value: str) -> str:
    """Generate SHA256 hash of a string."""
    return hashlib.sha256(value.encode()).hexdigest()


def format_bytes(size: int) -> str:
    """Format byte size to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse various timestamp formats to datetime."""
    formats = [
        '%Y-%m-%d %H:%M:%S,%f',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%SZ',
        '%y/%m/%d %H:%M:%S',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    
    return None


def truncate_string(value: str, max_length: int = 100) -> str:
    """Truncate string with ellipsis."""
    if len(value) <= max_length:
        return value
    return value[:max_length - 3] + "..."
