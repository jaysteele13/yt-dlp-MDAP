"""
core.py - Core business logic for YouTube music download workflow

This module handles:
- Directory creation and management
- Data validation and sanitization
- Configuration management
- Basic logging (can be extended by logger.py)
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple, List
import logging

TEMP_BASE = Path.home() / "Music" / "temp"

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_timestamp() -> str:
    """Get current timestamp as string for directory naming."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_timestamp_dir() -> Tuple[bool, Path, Optional[str]]:
    """Create a timestamped temporary directory under Music/temp."""
    try:
        TEMP_BASE.mkdir(parents=True, exist_ok=True)
        ts = get_timestamp()
        ts_dir = TEMP_BASE / ts
        ts_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created timestamp directory: {ts_dir}")
        return True, ts_dir, None
    except Exception as e:
        logger.error(f"Failed to create timestamp directory: {e}")
        return False, None, str(e)


def move_files_to_destination(
    src: Path,
    artist: str,
    album: str,
    base_dir: Path
) -> Tuple[bool, Path, Optional[str], int]:
    """Move files from source to destination directory (Artist/Album structure)."""
    try:
        artist_safe = DownloadManager.sanitize_filename(artist)
        album_safe = DownloadManager.sanitize_filename(album)
        
        dest = base_dir / artist_safe / album_safe
        dest.mkdir(parents=True, exist_ok=True)
        
        files_in_src = [f for f in src.iterdir() if f.is_file()]
        if not files_in_src:
            logger.warning(f"No files found in {src}")
            return False, Path(), "No files found in source directory", 0
        
        moved_count = 0
        for file in files_in_src:
            dest_file = dest / file.name
            shutil.move(str(file), str(dest_file))
            moved_count += 1
            logger.debug(f"Moved: {file.name} -> {dest}")
        
        logger.info(f"Moved {moved_count} files to {dest}")
        return True, dest, None, moved_count
        
    except Exception as e:
        logger.error(f"Failed to move files to destination: {e}")
        return False, Path(), str(e), 0


def cleanup_timestamp_dir(ts_dir: Path) -> Tuple[bool, Optional[str]]:
    """
    Remove the timestamp directory after successful move.
    
    Args:
        ts_dir: Timestamp directory to remove
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        if not ts_dir.exists():
            logger.warning(f"Timestamp directory does not exist: {ts_dir}")
            return True, None
        
        shutil.rmtree(ts_dir)
        logger.info(f"Cleaned up timestamp directory: {ts_dir}")
        return True, None
    except Exception as e:
        logger.error(f"Failed to cleanup timestamp directory: {e}")
        return False, str(e)


def validate_directory_exists(directory: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate that a directory exists.
    
    Args:
        directory: Path to check
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not directory.exists():
        msg = f"Directory does not exist: {directory}"
        logger.error(msg)
        return False, msg
    if not directory.is_dir():
        msg = f"Path is not a directory: {directory}"
        logger.error(msg)
        return False, msg
    return True, None


class DownloadManager:
    """Manages the core download workflow logic"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path.home() / "Music/.config/.yt_download_helper_config.json"
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            default_config = {
                'base_directory': str(Path.home() / "Music" / "artists"),
                'last_artist': '',
                'last_album': ''
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Optional[Dict] = None) -> None:
        """Save configuration to file"""
        config_to_save = config or self.config
        with open(self.config_file, 'w') as f:
            json.dump(config_to_save, f, indent=2)
    
    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Sanitize a string for use as a filename/directory name."""
        invalid_chars = '<>:"/\\|?*'
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        return sanitized.strip()
    
    @staticmethod
    def validate_youtube_url(url: str) -> bool:
        """Basic validation for YouTube URLs."""
        url_lower = url.lower()
        return any([
            'youtube.com' in url_lower,
            'youtu.be' in url_lower,
            'music.youtube.com' in url_lower
        ])



