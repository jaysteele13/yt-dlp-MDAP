"""
workflow.py - Download workflow orchestration

Orchestrates the complete download flow:
1. Create timestamp temp directory
2. Download audio with verbose output capture
3. Extract metadata from verbose output
4. Move files to destination after confirmation
5. Cleanup temp directory

Uses:
- core.py: Directory management utilities
- downloader.py: yt-dlp operations
- logger.py: Logging backends (optional)
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Callable, TYPE_CHECKING

from core import (
    TEMP_BASE,
    get_timestamp,
    create_timestamp_dir,
    get_files_in_directory,
    move_files_to_destination,
    cleanup_timestamp_dir,
    validate_directory_exists,
    DownloadManager,
)
from downloader import YTDLPDownloader

if TYPE_CHECKING:
    from logger import Logger

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class DownloadWorkflow:
    """
    Orchestrates the complete download workflow.
    
    Flow:
    1. Download to timestamp temp directory
    2. Extract Artist/Album from verbose output
    3. Return metadata for user confirmation
    4. Move files to final destination
    5. Cleanup temp directory
    """
    
    def __init__(
        self,
        base_output_dir: Optional[Path] = None,
        output_format: str = "mp3",
        output_quality: str = "320",
        logger_instance: Optional["Logger"] = None
    ):
        """
        Initialize workflow.
        
        Args:
            base_output_dir: Base directory for final output (defaults to ~/Music/artists)
            output_format: Audio format (mp3, m4a, etc.)
            output_quality: Audio quality for mp3
            logger_instance: Optional logger for recording downloads
        """
        self.base_output_dir = base_output_dir or (Path.home() / "Music" / "artists")
        self.output_format = output_format
        self.output_quality = output_quality
        self.logger_instance = logger_instance
        
        self.downloader = YTDLPDownloader()
        self.manager = DownloadManager()
        
        self._current_temp_dir: Optional[Path] = None
        self._current_url: Optional[str] = None
        self._extracted_artist: Optional[str] = None
        self._extracted_album: Optional[str] = None
        self._downloaded_files: List[Path] = []
        
        logger.info(f"Workflow initialized. Output dir: {self.base_output_dir}")
    
    def _log_to_backend(self, entry: Dict) -> None:
        """Log entry to backend logger if available."""
        if self.logger_instance:
            try:
                self.logger_instance.log(entry)
                logger.debug("Logged to backend")
            except Exception as e:
                logger.warning(f"Backend logging failed: {e}")
    
    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate YouTube URL.
        
        Args:
            url: YouTube URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        logger.debug(f"Validating URL: {url}")
        
        if not url or not url.strip():
            return False, "URL is required"
        
        if not self.manager.validate_youtube_url(url):
            return False, "Invalid YouTube URL"
        
        logger.debug("URL validation passed")
        return True, None
    
    def download(
        self,
        url: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Download audio to timestamp temp directory.
        
        Args:
            url: YouTube URL
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success, temp_directory, error_message)
        """
        logger.info(f"Starting download for: {url}")
        
        valid, error = self.validate_url(url)
        if not valid:
            logger.error(f"URL validation failed: {error}")
            return False, None, error
        
        valid, error = validate_directory_exists(TEMP_BASE.parent)
        if not valid:
            logger.warning(f"Base temp directory parent not found, creating: {TEMP_BASE.parent}")
            TEMP_BASE.parent.mkdir(parents=True, exist_ok=True)
        
        success, ts_dir, error = create_timestamp_dir()
        if not success:
            logger.error(f"Failed to create timestamp directory: {error}")
            return False, None, error
        
        self._current_temp_dir = ts_dir
        self._current_url = url
        
        logger.info(f"Downloading to: {ts_dir}")
        
        success, metadata, error = self.downloader.download_with_verbose_capture(
            url=url,
            output_dir=ts_dir,
            progress_callback=progress_callback
        )
        
        if not success:
            logger.error(f"Download failed: {error}")
            cleanup_timestamp_dir(ts_dir)
            return False, None, error
        
        self._downloaded_files = []
        for f in ts_dir.iterdir():
            if f.is_file():
                self._downloaded_files.append(f)
        logger.info(f"Download complete. Files: {len(self._downloaded_files)}")
        
        if metadata:
            self._extracted_artist = metadata[0]
            self._extracted_album = metadata[1]
            logger.info(f"Extracted metadata - Artist: {self._extracted_artist}, Album: {self._extracted_album}")
        else:
            logger.warning("No metadata extracted from verbose output")
        
        return True, ts_dir, None
    
    def get_extracted_metadata(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Get extracted artist and album from last download.
        
        Returns:
            Tuple of (artist, album)
        """
        return self._extracted_artist, self._extracted_album
    
    def get_downloaded_files(self) -> List[Path]:
        """
        Get list of downloaded files from last download.
        
        Returns:
            List of file paths
        """
        return self._downloaded_files.copy()
    
    def confirm_and_move(
        self,
        artist: str,
        album: str,
        is_album_type: bool = True
    ) -> Tuple[bool, Path, Optional[str], int]:
        """
        Move downloaded files to final destination after user confirmation.
        
        Args:
            artist: Artist name (confirmed by user)
            album: Album name (confirmed by user)
            is_album_type: True for Album, False for Song
            
        Returns:
            Tuple of (success, final_destination_path, error_message)
        """
        logger.info(f"Moving files - Artist: {artist}, Album: {album}, Type: {'Album' if is_album_type else 'Song'}")
        
        if not self._current_temp_dir or not self._current_temp_dir.exists():
            logger.error("No temp directory available for move operation")
            return False, Path(), "No temp directory available. Run download() first.", 0
        
        success, dest, error, file_count = move_files_to_destination(
            src=self._current_temp_dir,
            artist=artist,
            album=album,
            base_dir=self.base_output_dir
        )
        
        if not success:
            logger.error(f"Failed to move files: {error}")
            return False, Path(), error, 0
        
        logger.info(f"Files moved to: {dest}")
        
        cleanup_success, cleanup_error = cleanup_timestamp_dir(self._current_temp_dir)
        if not cleanup_success:
            logger.warning(f"Failed to cleanup temp directory: {cleanup_error}")
        
        entry = {
            'timestamp': get_timestamp(),
            'type': 'album' if is_album_type else 'song',
            'link': self._current_url,
            'artist': artist,
            'album': album,
            'final_directory': str(dest),
            'file_count': file_count
        }
        self._log_to_backend(entry)
        
        self._current_temp_dir = None
        self._current_url = None
        self._downloaded_files = []
        
        return True, dest, None, file_count
    
    def cancel(self) -> Tuple[bool, Optional[str]]:
        """
        Cancel current workflow and cleanup temp directory.
        
        Returns:
            Tuple of (success, error_message)
        """
        logger.info("Workflow cancelled by user")
        
        if self._current_temp_dir and self._current_temp_dir.exists():
            success, error = cleanup_timestamp_dir(self._current_temp_dir)
            if not success:
                logger.warning(f"Failed to cleanup on cancel: {error}")
                return False, error
        
        self._reset_state()
        return True, None
    
    def _reset_state(self) -> None:
        """Reset internal state."""
        self._current_temp_dir = None
        self._current_url = None
        self._extracted_artist = None
        self._extracted_album = None
        self._downloaded_files = []
    
    def get_status(self) -> Dict:
        """
        Get current workflow status.
        
        Returns:
            Dictionary with status information
        """
        return {
            'has_temp_dir': self._current_temp_dir is not None and self._current_temp_dir.exists(),
            'temp_dir': str(self._current_temp_dir) if self._current_temp_dir else None,
            'url': self._current_url,
            'extracted_artist': self._extracted_artist,
            'extracted_album': self._extracted_album,
            'file_count': len(self._downloaded_files),
            'output_dir': str(self.base_output_dir)
        }

