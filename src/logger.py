"""
logger.py - Logging module for download entries

Supports multiple logging backends:
- File logging (text files)
- Notion API logging (implement in notion_logger.py)
- Custom loggers via Logger interface
"""

from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class Logger(ABC):
    """Abstract base class for loggers"""
    
    @abstractmethod
    def log(self, entry: Dict) -> bool:
        """
        Log a download entry
        
        Args:
            entry: Download entry dictionary from core.py
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve download history
        
        Args:
            limit: Maximum number of entries to return (None for all)
            
        Returns:
            List of download entry dictionaries
        """
        pass


class FileLogger(Logger):
    """File-based logger - writes to a text file"""
    
    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize file logger
        
        Args:
            log_file: Path to log file (defaults to ~/youtube_downloads_log.txt)
        """
        self.log_file = log_file or Path.home() / "youtube_downloads_log.txt"
    
    def log(self, entry: Dict) -> bool:
        """Log entry to text file"""
        try:
            timestamp = entry.get('timestamp', datetime.now().isoformat())
            artist = entry.get('artist', 'Unknown')
            album = entry.get('album', 'Unknown')
            link = entry.get('link', '')
            directory = entry.get('directory', '')
            
            log_entry = (
                f"[{timestamp}] {artist} - {album}\n"
                f"Link: {link}\n"
                f"Path: {directory}\n"
                f"{'-'*80}\n"
            )
            
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
            
            return True
        except Exception as e:
            print(f"File logging failed: {e}")
            return False
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Read history from log file (basic parsing)
        Note: This is a simple implementation - for structured data, use JSON logger
        """
        if not self.log_file.exists():
            return []
        
        # Simple implementation - just return raw text for now
        # For structured queries, consider using JSONLogger instead
        try:
            with open(self.log_file, 'r') as f:
                content = f.read()
            return [{'raw_content': content}]
        except Exception:
            return []


class JSONLogger(Logger):
    """JSON-based logger - writes structured data"""
    
    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize JSON logger
        
        Args:
            log_file: Path to JSON log file (defaults to ~/youtube_downloads_log.json)
        """
        self.log_file = log_file or Path.home() / "youtube_downloads_log.json"
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Ensure log file exists with valid JSON"""
        if not self.log_file.exists():
            self._write_logs([])
    
    def _read_logs(self) -> List[Dict]:
        """Read all logs from file"""
        try:
            with open(self.log_file, 'r') as f:
                import json
                return json.load(f)
        except Exception:
            return []
    
    def _write_logs(self, logs: List[Dict]):
        """Write logs to file"""
        import json
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def log(self, entry: Dict) -> bool:
        """Log entry to JSON file"""
        try:
            logs = self._read_logs()
            logs.append(entry)
            self._write_logs(logs)
            return True
        except Exception as e:
            print(f"JSON logging failed: {e}")
            return False
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get download history"""
        logs = self._read_logs()
        if limit:
            return logs[-limit:]
        return logs


class MultiLogger(Logger):
    """Logger that writes to multiple backends simultaneously"""
    
    def __init__(self, loggers: List[Logger]):
        """
        Initialize multi-logger
        
        Args:
            loggers: List of Logger instances to use
        """
        self.loggers = loggers
    
    def log(self, entry: Dict) -> bool:
        """Log to all configured loggers"""
        results = [logger.log(entry) for logger in self.loggers]
        return all(results)  # True only if all succeed
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get history from first available logger"""
        for logger in self.loggers:
            history = logger.get_history(limit)
            if history:
                return history
        return []


# Notion logger stub - implement in notion_logger.py
class NotionLogger(Logger):
    """
    Notion API logger - to be implemented
    
    This is a stub. Create notion_logger.py with the actual implementation:
    
    from notion_client import Client
    
    class NotionLogger(Logger):
        def __init__(self, api_key: str, database_id: str):
            self.client = Client(auth=api_key)
            self.database_id = database_id
        
        def log(self, entry: Dict) -> bool:
            # Create a new page in Notion database
            # with entry data
            pass
        
        def get_history(self, limit: Optional[int] = None) -> List[Dict]:
            # Query Notion database
            pass
    """
    
    def __init__(self, api_key: str, database_id: str):
        """
        Initialize Notion logger
        
        Args:
            api_key: Notion API key
            database_id: Notion database ID
        """
        self.api_key = api_key
        self.database_id = database_id
        raise NotImplementedError(
            "NotionLogger needs to be implemented in notion_logger.py. "
            "Install notion-client: pip install notion-client"
        )
    
    def log(self, entry: Dict) -> bool:
        raise NotImplementedError("Implement in notion_logger.py")
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        raise NotImplementedError("Implement in notion_logger.py")


# Factory function for easy logger creation
def create_logger(logger_type: str = "file", **kwargs) -> Logger:
    """
    Factory function to create loggers
    
    Args:
        logger_type: Type of logger ("file", "json", "multi")
        **kwargs: Arguments for logger constructor
        
    Returns:
        Logger instance
        
    Examples:
        logger = create_logger("file")
        logger = create_logger("json", log_file=Path("custom.json"))
        logger = create_logger("multi", loggers=[file_logger, json_logger])
    """
    if logger_type == "file":
        return FileLogger(**kwargs)
    elif logger_type == "json":
        return JSONLogger(**kwargs)
    elif logger_type == "multi":
        return MultiLogger(**kwargs)
    elif logger_type == "notion":
        return NotionLogger(**kwargs)
    else:
        raise ValueError(f"Unknown logger type: {logger_type}")