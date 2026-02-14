"""
core.py - Core business logic for YouTube music download workflow

This module handles:
- Directory creation and management
- Data validation and sanitization
- Configuration management
- Basic logging (can be extended by logger.py)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple


class DownloadManager:
    """Manages the core download workflow logic"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize the download manager
        
        Args:
            config_file: Path to config file (defaults to ~/.yt_download_helper_config.json)
        """
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
        """
        Save configuration to file
        
        Args:
            config: Configuration dict to save (uses self.config if None)
        """
        config_to_save = config or self.config
        with open(self.config_file, 'w') as f:
            json.dump(config_to_save, f, indent=2)
    
    def update_config(self, **kwargs) -> None:
        """
        Update specific config values
        
        Args:
            **kwargs: Key-value pairs to update in config
        """
        self.config.update(kwargs)
        self.save_config()
    
    @staticmethod
    def sanitize_filename(name: str) -> str:
        """
        Sanitize a string for use as a filename/directory name
        
        Args:
            name: String to sanitize
            
        Returns:
            Sanitized string safe for filesystem
        """
        invalid_chars = '<>:"/\\|?*'
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        return sanitized.strip()
    
    @staticmethod
    def validate_youtube_url(url: str) -> bool:
        """
        Basic validation for YouTube URLs
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL looks like a YouTube link
        """
        url_lower = url.lower()
        return any([
            'youtube.com' in url_lower,
            'youtu.be' in url_lower,
            'music.youtube.com' in url_lower
        ])
    
    def validate_input(self, link: str, artist: str, album: str, base_dir: str) -> Tuple[bool, Optional[str]]:
        """
        Validate all input fields
        
        Args:
            link: YouTube URL
            artist: Artist name
            album: Album name
            base_dir: Base directory path
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not link or not link.strip():
            return False, "YouTube link is required"
        
        if not self.validate_youtube_url(link):
            return False, "Invalid YouTube URL"
        
        if not artist or not artist.strip():
            return False, "Artist name is required"
        
        if not album or not album.strip():
            return False, "Album name is required"
        
        if not base_dir or not base_dir.strip():
            return False, "Base directory is required"
        
        return True, None
    
    def create_directory_name(self, artist: str, album: str) -> str:
        """
        Create a sanitized directory name from artist and album
        
        Args:
            artist: Artist name
            album: Album name
            
        Returns:
            Sanitized directory name in format "Artist - Album"
        """
        artist_safe = self.sanitize_filename(artist)
        album_safe = self.sanitize_filename(album)
        return f"{artist_safe}/{album_safe}"
    
    def create_download_directory(self, artist: str, album: str, base_dir: str) -> Tuple[bool, Path, Optional[str]]:
        """
        Create the download directory
        
        Args:
            artist: Artist name
            album: Album name
            base_dir: Base directory path
            
        Returns:
            Tuple of (success, directory_path, error_message)
        """
        try:
            dir_name = self.create_directory_name(artist, album)
            full_path = Path(base_dir) / dir_name
            full_path.mkdir(parents=True, exist_ok=True)
            return True, full_path, None
        except Exception as e:
            return False, None, str(e)
    
    def generate_ytdlp_command(self, directory: Path, link: str) -> str:
        """
        Generate the yt-dlp command
        
        Args:
            directory: Target directory
            link: YouTube URL
            
        Returns:
            Complete yt-dlp command string
        """
        return f'cd "{directory}" && yt-dlp --extract-audio --audio-quality 0  "{link}"'
    
    def create_download_entry(self, link: str, artist: str, album: str, 
                            directory: Path) -> Dict:
        """
        Create a download entry data structure
        
        Args:
            link: YouTube URL
            artist: Artist name
            album: Album name
            directory: Created directory path
            
        Returns:
            Dictionary with download entry information
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'link': link,
            'artist': artist,
            'album': album,
            'directory': str(directory),
            'directory_name': directory.name,
            'ytdlp_command': self.generate_ytdlp_command(directory, link)
        }
    
    def process_download(self, link: str, artist: str, album: str, 
                        base_dir: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Main workflow: validate input, create directory, and prepare download entry
        
        Args:
            link: YouTube URL
            artist: Artist name
            album: Album name
            base_dir: Base directory (uses config default if None)
            
        Returns:
            Tuple of (success, download_entry_dict, error_message)
        """
        # Use config base directory if not provided
        if base_dir is None:
            base_dir = self.config['base_directory']
        
        # Validate input
        valid, error = self.validate_input(link, artist, album, base_dir)
        if not valid:
            return False, None, error
        
        # Create directory
        success, directory, error = self.create_download_directory(artist, album, base_dir)
        if not success:
            return False, None, f"Failed to create directory: {error}"
        
        # Create download entry
        entry = self.create_download_entry(link, artist, album, directory)
        
        # Update config with last used values
        self.update_config(
            last_artist=artist,
            last_album=album,
            base_directory=base_dir
        )
        
        return True, entry, None


# Convenience function for simple usage
def quick_process(link: str, artist: str, album: str, 
                 base_dir: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Quick one-line function to process a download
    
    Args:
        link: YouTube URL
        artist: Artist name
        album: Album name
        base_dir: Base directory (optional)
        
    Returns:
        Tuple of (success, download_entry_dict, error_message)
    """
    manager = DownloadManager()
    return manager.process_download(link, artist, album, base_dir)



