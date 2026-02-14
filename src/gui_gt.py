#!/usr/bin/env python3
"""
gui_qt.py - Qt GUI frontend for YouTube music download workflow

This uses the abstracted modules:
- core.py: Business logic
- logger.py: Logging backends
- downloader.py: yt-dlp operations
"""

import sys
import subprocess
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
    QMessageBox, QGroupBox, QStatusBar, QFrame, QCheckBox,
    QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# Import our modules
from core import DownloadManager
from logger import create_logger, MultiLogger, FileLogger, JSONLogger
from downloader import YTDLPDownloader


class MetadataFetchThread(QThread):
    """Thread for fetching metadata without blocking UI"""
    finished = pyqtSignal(str, str)  # artist, album
    error = pyqtSignal(str)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            downloader = YTDLPDownloader()
            artist, album = downloader.suggest_artist_album(self.url)
            if artist or album:
                self.finished.emit(artist or "", album or "")
            else:
                self.error.emit("Could not extract artist/album from video")
        except Exception as e:
            self.error.emit(str(e))


class YouTubeDownloadHelperQt(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.manager = DownloadManager()
        
        # Setup logger - using both file and JSON by default
        self.logger = MultiLogger([
            FileLogger(),
            JSONLogger()
        ])
        
        # Optional: Check if yt-dlp is available
        try:
            self.downloader = YTDLPDownloader()
            self.ytdlp_available = True
        except RuntimeError:
            self.downloader = None
            self.ytdlp_available = False
        
        self.metadata_thread = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("YouTube Music Download Helper")
        self.setGeometry(100, 100, 900, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Input section
        input_group = QGroupBox("Download Information")
        input_layout = QVBoxLayout()
        
        # YouTube Link with auto-extract button
        link_layout = QHBoxLayout()
        link_label = QLabel("YouTube Link:")
        link_label.setFixedWidth(120)
        self.link_entry = QLineEdit()
        self.link_entry.setPlaceholderText("https://youtube.com/...")
        self.link_entry.returnPressed.connect(self.on_link_entered)
        
        self.extract_btn = QPushButton("Auto-Extract Info")
        self.extract_btn.setFixedWidth(130)
        self.extract_btn.setEnabled(self.ytdlp_available)
        self.extract_btn.clicked.connect(self.extract_metadata)
        
        link_layout.addWidget(link_label)
        link_layout.addWidget(self.link_entry)
        link_layout.addWidget(self.extract_btn)
        input_layout.addLayout(link_layout)
        
        # Artist
        artist_layout = QHBoxLayout()
        artist_label = QLabel("Artist:")
        artist_label.setFixedWidth(120)
        self.artist_entry = QLineEdit()
        self.artist_entry.setText(self.manager.config.get('last_artist', ''))
        self.artist_entry.setPlaceholderText("Artist name")
        self.artist_entry.returnPressed.connect(lambda: self.album_entry.setFocus())
        artist_layout.addWidget(artist_label)
        artist_layout.addWidget(self.artist_entry)
        input_layout.addLayout(artist_layout)
        
        # Album
        album_layout = QHBoxLayout()
        album_label = QLabel("Album:")
        album_label.setFixedWidth(120)
        self.album_entry = QLineEdit()
        self.album_entry.setText(self.manager.config.get('last_album', ''))
        self.album_entry.setPlaceholderText("Album name")
        self.album_entry.returnPressed.connect(self.create_and_log)
        album_layout.addWidget(album_label)
        album_layout.addWidget(self.album_entry)
        input_layout.addLayout(album_layout)
        
        # Base Directory
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Base Directory:")
        dir_label.setFixedWidth(120)
        self.dir_entry = QLineEdit()
        self.dir_entry.setText(self.manager.config['base_directory'])
        self.dir_entry.setPlaceholderText("Download directory")
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_entry)
        dir_layout.addWidget(browse_btn)
        input_layout.addLayout(dir_layout)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.create_btn = QPushButton("Create Directory && Log")
        self.create_btn.setMinimumHeight(40)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.create_btn.clicked.connect(self.create_and_log)
        
        open_dir_btn = QPushButton("Open Directory")
        open_dir_btn.setMinimumHeight(40)
        open_dir_btn.clicked.connect(self.open_directory)
        
        clear_btn = QPushButton("Clear Form")
        clear_btn.setMinimumHeight(40)
        clear_btn.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.create_btn, 2)
        button_layout.addWidget(open_dir_btn, 1)
        button_layout.addWidget(clear_btn, 1)
        
        main_layout.addLayout(button_layout)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Output section
        output_label = QLabel("Output:")
        output_label.setFont(QFont("", 10, QFont.Bold))
        main_layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(200)
        self.output_text.setFont(QFont("Monospace", 9))
        main_layout.addWidget(self.output_text)
        
        # History button
        history_btn = QPushButton("View Download History")
        history_btn.clicked.connect(self.view_history)
        main_layout.addWidget(history_btn)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        if self.ytdlp_available:
            self.status_bar.showMessage("Ready - yt-dlp detected")
        else:
            self.status_bar.showMessage("Ready - yt-dlp not found (metadata extraction disabled)")
        
        # Set focus to link entry
        self.link_entry.setFocus()
    
    def on_link_entered(self):
        """Handle when user presses Enter in link field"""
        if self.ytdlp_available:
            self.extract_metadata()
        else:
            self.artist_entry.setFocus()
    
    def extract_metadata(self):
        """Extract artist and album from YouTube URL"""
        url = self.link_entry.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube link first")
            return
        
        if not self.manager.validate_youtube_url(url):
            QMessageBox.warning(self, "Error", "Invalid YouTube URL")
            return
        
        # Disable button during extraction
        self.extract_btn.setEnabled(False)
        self.extract_btn.setText("Extracting...")
        self.status_bar.showMessage("Fetching metadata from YouTube...")
        
        # Start thread
        self.metadata_thread = MetadataFetchThread(url)
        self.metadata_thread.finished.connect(self.on_metadata_extracted)
        self.metadata_thread.error.connect(self.on_metadata_error)
        self.metadata_thread.start()
    
    def on_metadata_extracted(self, artist: str, album: str):
        """Handle successful metadata extraction"""
        if artist:
            self.artist_entry.setText(artist)
        if album:
            self.album_entry.setText(album)
        
        self.output_text.append(f"✓ Auto-extracted: {artist} - {album}\n")
        self.status_bar.showMessage("Metadata extracted successfully")
        
        # Re-enable button
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("Auto-Extract Info")
        
        # Focus on first empty field or album field
        if not artist:
            self.artist_entry.setFocus()
        elif not album:
            self.album_entry.setFocus()
        else:
            self.create_btn.setFocus()
    
    def on_metadata_error(self, error: str):
        """Handle metadata extraction error"""
        self.output_text.append(f"⚠ Could not auto-extract: {error}\n")
        self.status_bar.showMessage("Metadata extraction failed")
        
        # Re-enable button
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("Auto-Extract Info")
        
        # Focus on artist field for manual entry
        self.artist_entry.setFocus()
    
    def browse_directory(self):
        """Browse for base directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Base Directory",
            self.dir_entry.text()
        )
        if directory:
            self.dir_entry.setText(directory)
    
    def create_and_log(self):
        """Create directory and log the download using core modules"""
        link = self.link_entry.text().strip()
        artist = self.artist_entry.text().strip()
        album = self.album_entry.text().strip()
        base_dir = self.dir_entry.text().strip()
        
        # Use core.py to process
        success, entry, error = self.manager.process_download(link, artist, album, base_dir)
        
        if not success:
            QMessageBox.warning(self, "Error", error)
            return
        
        # Log using logger.py
        log_success = self.logger.log(entry)
        
        # Update output
        self.output_text.append(f"✓ Directory created: {entry['directory']}")
        if log_success:
            self.output_text.append(f"✓ Logged to file and JSON")
        else:
            self.output_text.append(f"⚠ Logging failed")
        
        self.output_text.append(f"\nyt-dlp command:")
        self.output_text.append(entry['ytdlp_command'])
        self.output_text.append(f"\n{'='*60}\n")
        
        # Update status
        self.status_bar.showMessage(f"Created: {entry['directory_name']}")
        
        # Copy command to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(entry['ytdlp_command'])
        
        # Success message
        QMessageBox.information(
            self,
            "Success",
            f"Directory created successfully!\n\n"
            f"Path: {entry['directory']}\n\n"
            f"yt-dlp command copied to clipboard!\n"
            f"Paste it in your terminal to download."
        )
        
        # Clear link for next entry
        self.link_entry.clear()
        self.link_entry.setFocus()
    
    def open_directory(self):
        """Open the created directory in file manager"""
        base_dir = self.dir_entry.text().strip()
        artist = self.artist_entry.text().strip()
        album = self.album_entry.text().strip()
        
        if not artist or not album:
            # Just open base directory
            if Path(base_dir).exists():
                subprocess.Popen(['xdg-open', base_dir])
            else:
                QMessageBox.warning(self, "Error", "Base directory doesn't exist")
            return
        
        dir_name = self.manager.create_directory_name(artist, album)
        full_path = Path(base_dir) / dir_name
        
        if full_path.exists():
            subprocess.Popen(['xdg-open', str(full_path)])
        else:
            QMessageBox.warning(self, "Error", "Directory doesn't exist yet. Create it first!")
    
    def clear_form(self):
        """Clear all input fields"""
        self.link_entry.clear()
        self.link_entry.setFocus()
    
    def view_history(self):
        """View download history"""
        # Try JSON log first (structured), fall back to text
        json_log = Path.home() / "youtube_downloads_log.json"
        text_log = Path.home() / "youtube_downloads_log.txt"
        
        if json_log.exists():
            subprocess.Popen(['xdg-open', str(json_log)])
        elif text_log.exists():
            subprocess.Popen(['xdg-open', str(text_log)])
        else:
            QMessageBox.information(self, "History", "No download history yet.")


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = YouTubeDownloadHelperQt()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()