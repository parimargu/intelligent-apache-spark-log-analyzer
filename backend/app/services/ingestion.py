"""
Log Ingestion Service.

Handles file ingestion from multiple sources:
- Manual upload
- Folder watching
- API ingestion
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, List
from datetime import datetime

import structlog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from app.config import get_settings
from app.db import get_sync_session, SyncSessionLocal
from app.models.log import LogFile, IngestionSource


logger = structlog.get_logger()
settings = get_settings()


class LogFileHandler(FileSystemEventHandler):
    """Watchdog handler for log file changes."""
    
    def __init__(self, ingestion_service: 'IngestionService'):
        self.ingestion_service = ingestion_service
        self.supported_extensions = settings.supported_extensions_list
    
    def on_created(self, event):
        """Handle new file creation."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix.lower() in self.supported_extensions:
            logger.info("New log file detected", path=str(file_path))
            asyncio.create_task(
                self.ingestion_service.ingest_file(str(file_path))
            )


class IngestionService:
    """Service for log file ingestion."""
    
    def __init__(self):
        self.upload_dir = Path(settings.log_upload_dir)
        self.watch_dir = Path(settings.log_watch_dir)
        self.observer: Optional[Observer] = None
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create upload and watch directories if they don't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.watch_dir.mkdir(parents=True, exist_ok=True)
    
    async def ingest_file(
        self,
        file_path: str,
        source: IngestionSource = IngestionSource.FOLDER_WATCH
    ) -> Optional[int]:
        """
        Ingest a single log file.
        
        Returns the created LogFile ID or None if failed.
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error("File not found", path=str(path))
            return None
        
        try:
            file_size = path.stat().st_size
            
            # Create database record
            session = SyncSessionLocal()
            try:
                log_file = LogFile(
                    filename=path.name,
                    original_filename=path.name,
                    file_path=str(path.absolute()),
                    file_size=file_size,
                    source=source
                )
                
                session.add(log_file)
                session.commit()
                session.refresh(log_file)
                
                file_id = log_file.id
                
                logger.info(
                    "File ingested",
                    file_id=file_id,
                    filename=path.name,
                    size=file_size
                )
                
                return file_id
            finally:
                session.close()
        
        except Exception as e:
            logger.error("Failed to ingest file", path=str(path), error=str(e))
            return None
    
    def start_folder_watcher(self):
        """Start watching the configured folder for new log files."""
        if self.observer is not None:
            logger.warning("Folder watcher already running")
            return
        
        handler = LogFileHandler(self)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.watch_dir), recursive=False)
        self.observer.start()
        
        logger.info("Folder watcher started", path=str(self.watch_dir))
    
    def stop_folder_watcher(self):
        """Stop the folder watcher."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Folder watcher stopped")
    
    async def scan_watch_folder(self) -> List[int]:
        """
        Scan watch folder for existing files and ingest them.
        
        Returns list of created file IDs.
        """
        file_ids = []
        
        for ext in settings.supported_extensions_list:
            for path in self.watch_dir.glob(f"*{ext}"):
                file_id = await self.ingest_file(str(path))
                if file_id:
                    file_ids.append(file_id)
        
        logger.info("Watch folder scan complete", files_ingested=len(file_ids))
        return file_ids
    
    def get_upload_path(self, filename: str) -> Path:
        """Get the full path for a new upload."""
        return self.upload_dir / filename
