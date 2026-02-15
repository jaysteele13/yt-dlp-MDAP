"""
downloader.py - Module for handling actual download operations with yt-dlp

This module provides:
- yt-dlp command execution
- Download progress tracking
- Metadata extraction from YouTube verbose output
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, Callable
import re

logger = logging.getLogger(__name__)


class YTDLPDownloader:
    """Handler for yt-dlp operations"""
    
    def __init__(self, ytdlp_path: str = "yt-dlp"):
        """Initialize downloader."""
        self.ytdlp_path = ytdlp_path
        self._check_ytdlp()
    
    def _check_ytdlp(self) -> bool:
        """Check if yt-dlp is available."""
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
    
    def parse_verbose_output(self, output: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse artist and album from yt-dlp verbose output."""
        artist = None
        album = None
        
        album_pattern = re.compile(r'\[download\]\s+Downloading playlist:\s+Album\s+-\s+(.+)$', re.MULTILINE)
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
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, Optional[Tuple[Optional[str], Optional[str]]], Optional[str]]:
        """Download audio and capture verbose output for metadata extraction."""
        try:
            cmd = [
                self.ytdlp_path,
                "--verbose",
                "--extract-audio",
                "--embed-metadata",
                "--audio-quality", "0",
                "-o", str(output_dir / "%(title)s.%(ext)s"),
                url
            ]
            
            full_output = []
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            try:
                if process.stdout:
                    for line in iter(process.stdout.readline, ''):
                        if not line:
                            break
                        
                        stripped = line.rstrip('\n\r')
                        full_output.append(stripped)
                        
                        if progress_callback and stripped:
                            progress_callback(stripped)
                
                return_code = process.wait()
                
                output_text = "\n".join(full_output)
                logger.debug(f"OUTPUT TEXT HERE: {output_text} OUTPUT END HERE!")
                
                if progress_callback:
                    progress_callback(f"\n[DEBUG] Captured {len(full_output)} lines, {len(output_text)} characters")
                
                if return_code != 0:
                    error_output = "\n".join(full_output[-20:])
                    return False, None, f"Download failed with code {return_code}: {error_output}"
                
                artist, album = self.parse_verbose_output(output_text)
                
                return True, (artist, album), None
                
            finally:
                if process.stdout:
                    process.stdout.close()
                
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
        
        except Exception as e:
            return False, None, f"Exception occurred: {str(e)}"
