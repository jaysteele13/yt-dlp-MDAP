"""
downloader.py - Module for handling actual download operations with yt-dlp

This module provides:
- yt-dlp command execution
- Download progress tracking
- Audio format extraction
- Metadata extraction from YouTube
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, Callable
import re


class YTDLPDownloader:
    """Handler for yt-dlp operations"""
    
    def __init__(self, ytdlp_path: str = "yt-dlp"):
        """
        Initialize downloader
        
        Args:
            ytdlp_path: Path to yt-dlp binary (defaults to system PATH)
        """
        self.ytdlp_path = ytdlp_path
        self._check_ytdlp()
    
    def _check_ytdlp(self) -> bool:
        """Check if yt-dlp is available"""
        try:
            result = subprocess.run(
                [self.ytdlp_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            raise RuntimeError(
                "yt-dlp not found. Install it with: sudo apt install yt-dlp "
                "or pip install yt-dlp --break-system-packages"
            )
    
    def extract_metadata(self, url: str) -> Optional[Dict]:
        """
        Extract metadata from YouTube URL without downloading
        
        Args:
            url: YouTube URL
            
        Returns:
            Dictionary with metadata (title, artist, album, etc.) or None if failed
        """
        try:
            cmd = [
                self.ytdlp_path,
                "--dump-json",
                "--no-playlist",  # Only get single video info
                url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            # Parse JSON output
            metadata = json.loads(result.stdout)
            
            # Extract useful fields
            return {
                'title': metadata.get('title', ''),
                'uploader': metadata.get('uploader', ''),
                'channel': metadata.get('channel', ''),
                'artist': metadata.get('artist') or metadata.get('creator', ''),
                'album': metadata.get('album', ''),
                'track': metadata.get('track', ''),
                'duration': metadata.get('duration', 0),
                'description': metadata.get('description', ''),
                'upload_date': metadata.get('upload_date', ''),
            }
            
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return None
    
    def parse_artist_album_from_title(self, title: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse artist and album from video title
        Common formats:
        - "Artist - Album"
        - "Artist | Album"
        - "Album by Artist"
        - "Artist: Album"
        
        Args:
            title: Video title
            
        Returns:
            Tuple of (artist, album) or (None, None) if parsing fails
        """
        if not title:
            return None, None
        
        # Pattern 1: "Artist - Album" or "Artist | Album"
        match = re.match(r'^(.+?)\s*[-|]\s*(.+?)(?:\s*\(.*\))?$', title)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Pattern 2: "Album by Artist"
        match = re.match(r'^(.+?)\s+by\s+(.+?)(?:\s*\(.*\))?$', title, re.IGNORECASE)
        if match:
            return match.group(2).strip(), match.group(1).strip()
        
        # Pattern 3: "Artist: Album"
        match = re.match(r'^(.+?):\s*(.+?)(?:\s*\(.*\))?$', title)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        return None, None
    
    def suggest_artist_album(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Suggest artist and album names from YouTube URL
        
        Args:
            url: YouTube URL
            
        Returns:
            Tuple of (artist, album) suggestions
        """
        metadata = self.extract_metadata(url)
        if not metadata:
            return None, None
        
        # Try to get from metadata fields first
        artist = metadata.get('artist') or metadata.get('uploader')
        album = metadata.get('album')
        
        # If not in metadata, try parsing the title
        if not artist or not album:
            title = metadata.get('title', '')
            parsed_artist, parsed_album = self.parse_artist_album_from_title(title)
            artist = artist or parsed_artist
            album = album or parsed_album
        
        return artist, album
    
    def parse_verbose_output(self, output: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse artist and album from yt-dlp verbose output.
        
        Parses patterns from planning doc:
        - Album: [download] Downloading playlist: Album - [Album_Name]
        - Artist: -metadata 'artist=[artist_name]'
        
        Args:
            output: Full verbose output string from yt-dlp
            
        Returns:
            Tuple of (artist, album) or (None, None) if not found
        """
        artist = None
        album = None
        
        album_pattern = re.compile(r'\[download\]\s+Downloading playlist:\s+Album\s+-\s+(.+?)(?:\s*-\s+|\s*$)')
        album_match = album_pattern.search(output)
        if album_match:
            album = album_match.group(1).strip()
        
        artist_pattern = re.compile(r"-metadata\s+'artist=(.+?)'")
        artist_match = artist_pattern.search(output)
        if artist_match:
            artist = artist_match.group(1).strip()
        
        return artist, album
    
    def download_with_verbose_capture(
        self,
        url: str,
        output_dir: Path,
        format_type: str = "mp3",
        quality: str = "320",
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, Optional[Tuple[Optional[str], Optional[str]]], Optional[str]]:
        """
        Download audio and capture verbose output for metadata extraction.
        
        Uses --verbose flag to extract Artist and Album from yt-dlp output
        as documented in planning/how_will_work.md
        
        Args:
            url: YouTube URL
            output_dir: Directory to save files
            format_type: Audio format (mp3, m4a, opus, etc.)
            quality: Audio quality for mp3 (320, 256, 192, 128)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success, (artist, album) tuple, error_message)
        """
        try:
            cmd = [
                self.ytdlp_path,
                "--verbose",
                "-x",
                "--audio-format", format_type,
                "--audio-quality", f"{quality}K" if format_type == "mp3" else "0",
                "--embed-thumbnail",
                "--embed-metadata",
                "--add-metadata",
                "-o", str(output_dir / "%(title)s.%(ext)s"),
                url
            ]
            
            full_output = []
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            if progress_callback:
                for line in process.stdout:
                    stripped = line.strip()
                    full_output.append(stripped)
                    progress_callback(stripped)
            else:
                for line in process.stdout:
                    full_output.append(line.strip())
                process.wait()
            
            if process.returncode != 0:
                return False, None, "Download failed"
            
            output_text = "\n".join(full_output)
            artist, album = self.parse_verbose_output(output_text)
            
            return True, (artist, album), None
            
        except Exception as e:
            return False, None, str(e)
    
    def download_audio(
        self,
        url: str,
        output_dir: Path,
        format_type: str = "mp3",
        quality: str = "320",
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Download audio from YouTube URL
        
        Args:
            url: YouTube URL
            output_dir: Directory to save files
            format_type: Audio format (mp3, m4a, opus, etc.)
            quality: Audio quality for mp3 (320, 256, 192, 128)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            cmd = [
                self.ytdlp_path,
                "-x",  # Extract audio
                "--audio-format", format_type,
                "--audio-quality", f"{quality}K" if format_type == "mp3" else "0",
                "--embed-thumbnail",  # Embed album art
                "--embed-metadata",  # Embed metadata
                "--add-metadata",
                "-o", str(output_dir / "%(title)s.%(ext)s"),
                url
            ]
            
            # Run the download
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output
            if progress_callback:
                for line in process.stdout:
                    progress_callback(line.strip())
            else:
                process.wait()
            
            if process.returncode != 0:
                return False, "Download failed"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def get_download_command(
        self,
        url: str,
        output_dir: Path,
        format_type: str = "mp3",
        quality: str = "320"
    ) -> str:
        """
        Generate the yt-dlp command string for manual execution
        
        Args:
            url: YouTube URL
            output_dir: Directory to save files
            format_type: Audio format
            quality: Audio quality
            
        Returns:
            Complete command string
        """
        return (
            f'cd "{output_dir}" && '
            f'yt-dlp -x --audio-format {format_type} --audio-quality {quality}K '
            f'--embed-thumbnail --embed-metadata --add-metadata '
            f'-o "%(title)s.%(ext)s" "{url}"'
        )


# Convenience functions
def quick_suggest(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Quick function to get artist/album suggestions
    
    Args:
        url: YouTube URL
        
    Returns:
        Tuple of (artist, album)
    """
    downloader = YTDLPDownloader()
    return downloader.suggest_artist_album(url)


def quick_download(url: str, output_dir: Path, format_type: str = "mp3") -> Tuple[bool, Optional[str]]:
    """
    Quick function to download audio
    
    Args:
        url: YouTube URL
        output_dir: Output directory
        format_type: Audio format
        
    Returns:
        Tuple of (success, error_message)
    """
    downloader = YTDLPDownloader()
    return downloader.download_audio(url, output_dir, format_type)