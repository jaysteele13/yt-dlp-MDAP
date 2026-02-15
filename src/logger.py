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