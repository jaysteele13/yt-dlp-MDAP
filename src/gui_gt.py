#!/usr/bin/env python3
"""
gui_gt.py - Qt GUI frontend for YouTube music download workflow

Simplified UI that:
- Accepts only a URL
- Downloads to temp directory
- Extracts metadata from verbose output
- Prompts for confirmation
- Moves files to final destination

Uses:
- workflow.py: DownloadWorkflow orchestration
- logger.py: Logging backends
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
    QMessageBox, QGroupBox, QStatusBar, QFrame,
    QProgressBar, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from workflow import DownloadWorkflow
from logger import MultiLogger, FileLogger, JSONLogger
from core import DownloadManager
from core import TEMP_BASE

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class DownloadThread(QThread):
    """Thread for running download workflow without blocking UI"""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str, str, int)
    error = pyqtSignal(str)
    
    def __init__(self, workflow: DownloadWorkflow, url: str):
        super().__init__()
        self.workflow = workflow
        self.url = url
    
    def run(self):
        try:
            logger.info(f"Starting download thread for: {self.url}")
            
            def progress_callback(line: str):
                self.progress.emit(line)
            
            success, temp_dir, error = self.workflow.download(self.url, progress_callback)
            
            if not success:
                logger.error(f"Download failed: {error}")
                self.error.emit(error)
                return
            
            artist, album = self.workflow.get_extracted_metadata()
            files = self.workflow.get_downloaded_files()
            file_count = len(files)
            
            logger.info(f"Download complete. Artist: {artist}, Album: {album}, Files: {file_count}")
            self.finished.emit(True, artist or "", album or "", str(temp_dir), file_count)
            
        except Exception as e:
            logger.exception(f"Download thread error: {e}")
            self.error.emit(str(e))


class ConfirmDialog(QMessageBox):
    """Custom dialog for confirming artist/album after download"""
    
    def __init__(self, parent, artist: str, album: str, file_count: int, is_album: bool):
        super().__init__(parent)
        self.setWindowTitle("Confirm Details")
        self.setIcon(QMessageBox.Question)
        
        artist = artist or "Unknown"
        album = album or "Unknown"
        
        download_type = "Album" if is_album else "Song"
        
        self.setText(
            f"<b>Download Complete!</b><br><br>"
            f"Type: {download_type}<br>"
            f"Files downloaded: {file_count}<br><br>"
            f"Please confirm or correct the details:"
        )
        
        self.artist_input = QLineEdit(artist)
        self.album_input = QLineEdit(album)
        
        self.setDetailedText(f"Artist: {artist}\nAlbum: {album}")
        
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        self.button(QMessageBox.Ok).setText("Confirm & Move")
        self.button(QMessageBox.Cancel).setText("Cancel")
    
    def get_values(self) -> tuple:
        return self.artist_input.text().strip(), self.album_input.text().strip()


class YouTubeDownloadHelperQt(QMainWindow):
    def __init__(self):
        super().__init__()
        
        logger.info("Initializing GUI")
        
        self.workflow: Optional[DownloadWorkflow] = None
        self.download_thread: Optional[DownloadThread] = None
        self.is_album_type = True
        
        self.init_workflow()
        self.init_ui()
        
        logger.info("GUI initialized successfully")
    
    def init_workflow(self):
        """Initialize the download workflow with logging"""
        backend_logger = MultiLogger([
            FileLogger(),
            JSONLogger()
        ])
        
        base_output = Path.home() / "Music" / "artists"
        
        self.workflow = DownloadWorkflow(
            base_output_dir=base_output,
            logger_instance=backend_logger
        )
        
        logger.debug(f"Workflow created with output dir: {base_output}")
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Music Download Assistant")
        self.setGeometry(100, 100, 900, 650)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("Music Download Assistant")
        title_label.setFont(QFont("", 14, QFont.Bold))
        title_label.setStyleSheet("color: #333;")
        main_layout.addWidget(title_label)
        
        input_group = QGroupBox("Download")
        input_layout = QVBoxLayout()
        
        link_layout = QHBoxLayout()
        link_label = QLabel("YouTube URL:")
        link_label.setFixedWidth(100)
        self.link_entry = QLineEdit()
        self.link_entry.setPlaceholderText("https://youtube.com/watch?v=... or https://youtu.be/...")
        self.link_entry.returnPressed.connect(self.start_download)
        link_layout.addWidget(link_label)
        link_layout.addWidget(self.link_entry, 1)
        input_layout.addLayout(link_layout)
        
        type_layout = QHBoxLayout()
        type_label = QLabel("Download Type:")
        type_label.setFixedWidth(100)
        
        self.type_group = QButtonGroup(self)
        
        self.album_radio = QRadioButton("Album")
        self.album_radio.setChecked(True)
        self.song_radio = QRadioButton("Single Song")
        
        self.type_group.addButton(self.album_radio)
        self.type_group.addButton(self.song_radio)
        
        self.album_radio.toggled.connect(lambda: self._set_album_type(True))
        self.song_radio.toggled.connect(lambda: self._set_album_type(False))
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.album_radio)
        type_layout.addWidget(self.song_radio)
        type_layout.addStretch()
        
        input_layout.addLayout(type_layout)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("Download")
        self.download_btn.setMinimumHeight(45)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.download_btn.clicked.connect(self.start_download)
        
        self.cancel_btn = QPushButton("Cancel Download")
        self.cancel_btn.setMinimumHeight(45)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_download)
        
        button_layout.addWidget(self.download_btn, 2)
        button_layout.addWidget(self.cancel_btn, 1)
        main_layout.addLayout(button_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e0e0e0;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        output_label = QLabel("Progress Output:")
        output_label.setFont(QFont("", 10, QFont.Bold))
        main_layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(250)
        self.output_text.setFont(QFont("Monospace", 8))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.output_text)
        
        button_layout = QHBoxLayout()
        
        self.open_dir_btn = QPushButton("Open Output Folder")
        self.open_dir_btn.clicked.connect(self.open_output_folder)
        
        self.clear_btn = QPushButton("Clear Output")
        self.clear_btn.clicked.connect(self.clear_output)
        
        button_layout.addWidget(self.open_dir_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(button_layout)
        
        central_widget.setLayout(main_layout)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_bar.showMessage("Ready - Enter a YouTube URL to download")
        
        self.link_entry.setFocus()
    
    def _set_album_type(self, is_album: bool):
        """Set download type"""
        self.is_album_type = is_album
        logger.debug(f"Download type set to: {'Album' if is_album else 'Song'}")
    
    def append_output(self, text: str):
        """Append text to output area"""
        self.output_text.append(text)
    
    def set_downloading(self, downloading: bool):
        """Enable/disable download controls during download"""
        self.download_btn.setEnabled(not downloading)
        self.cancel_btn.setEnabled(downloading)
        self.link_entry.setEnabled(not downloading)
        self.album_radio.setEnabled(not downloading)
        self.song_radio.setEnabled(not downloading)
        
        if downloading:
            self.download_btn.setText("Downloading...")
            self.status_bar.showMessage("Downloading...")
        else:
            self.download_btn.setText("Download")
            self.progress_bar.setValue(0)
    
    def cancel_download(self):
        """Cancel the current download"""
        logger.info("Cancel requested by user")
        
        if self.download_thread and self.download_thread.isRunning():
            self.append_output("")
            self.append_output("<span style='color: #FF9800;'>! Cancelling download...</span>")
            
            self.download_thread.terminate()
            self.download_thread.wait()
            
            if self.workflow:
                self.workflow.cancel()
            
            self.set_downloading(False)
            self.append_output("<span style='color: #FF9800;'>! Download cancelled</span>")
            self.status_bar.showMessage("Download cancelled")
            
            self.link_entry.clear()
            self.link_entry.setFocus()
    
    def start_download(self):
        """Start the download process"""
        url = self.link_entry.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
            return
        
        valid, error = self.workflow.validate_url(url)
        if not valid:
            QMessageBox.warning(self, "Error", error)
            return
        
        logger.info(f"Starting download for URL: {url}")
        
        self.append_output(f"<span style='color: #4CAF50;'>>> Starting download...</span>")
        self.append_output(f"<span style='color: #888;'>URL: {url}</span>")
        self.append_output("")
        
        self.set_downloading(True)
        self.progress_bar.setMaximum(0)
        
        self.download_thread = DownloadThread(self.workflow, url)
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()
    
    def on_download_progress(self, line: str):
        """Handle download progress output"""
        if "[download]" in line or "[metadata]" in line:
            self.append_output(f"<span style='color: #888;'>{line}</span>")
    
    def on_download_finished(self, success: bool, artist: str, album: str, temp_dir: str, file_count: int):
        """Handle download completion"""
        self.set_downloading(False)
        
        if not success:
            return
        
        self.append_output("")
        self.append_output(f"<span style='color: #4CAF50;'>✓ Download complete! ({file_count} files)</span>")
        
        self.append_output("")
        self.append_output(f"<span style='color: #569CD6;'>--- Confirm Details ---</span>")
        
        dialog = ConfirmDialog(self, artist, album, file_count, self.is_album_type)
        
        if dialog.exec_() == QMessageBox.Ok:
            confirmed_artist, confirmed_album = dialog.get_values()
            
            if not confirmed_artist:
                QMessageBox.warning(self, "Error", "Artist name is required")
                self.status_bar.showMessage("Artist name required")
                return
            
            if not confirmed_album:
                QMessageBox.warning(self, "Error", "Album name is required")
                self.status_bar.showMessage("Album name required")
                return
            
            self.confirm_and_move(confirmed_artist, confirmed_album)
        else:
            self.append_output("<span style='color: #CE9178;'>Download cancelled by user</span>")
            self.workflow.cancel()
            self.status_bar.showMessage("Cancelled")
            
            self.link_entry.clear()
            self.link_entry.setFocus()
    
    def confirm_and_move(self, artist: str, album: str):
        """Confirm and move files to final destination"""
        logger.info(f"Confirming move - Artist: {artist}, Album: {album}")
        
        self.append_output(f"<span style='color: #569CD6;'>Moving to: {artist} - {album}</span>")
        self.status_bar.showMessage("Moving files...")
        
        success, dest, error = self.workflow.confirm_and_move(
            artist=artist,
            album=album,
            is_album_type=self.is_album_type
        )
        
        if success:
            self.append_output(f"<span style='color: #4CAF50;'>✓ Files moved successfully!</span>")
            self.append_output(f"<span style='color: #888;'>Location: {dest}</span>")
            self.append_output("")
            self.append_output(f"<span style='color: #4CAF50;'>{'='*50}</span>")
            self.append_output("")
            
            self.status_bar.showMessage(f"Saved to: {dest}")
            
            reply = QMessageBox.question(
                self,
                "Download Complete",
                f"Download complete!\n\nSaved to:\n{dest}\n\nOpen folder?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    import subprocess
                    subprocess.Popen(['xdg-open', str(dest)])
                except Exception as e:
                    logger.error(f"Failed to open directory: {e}")
        else:
            self.append_output(f"<span style='color: #F44747;'>✗ Failed to move files: {error}</span>")
            self.status_bar.showMessage(f"Error: {error}")
            QMessageBox.warning(self, "Error", f"Failed to move files: {error}")
        
        self.link_entry.clear()
        self.link_entry.setFocus()
    
    def on_download_error(self, error: str):
        """Handle download error"""
        self.set_downloading(False)
        
        self.append_output("")
        self.append_output(f"<span style='color: #F44747;'>✗ Error: {error}</span>")
        self.append_output("")
        
        self.status_bar.showMessage(f"Error: {error}")
        
        QMessageBox.critical(self, "Download Error", error)
        
        self.link_entry.setFocus()
    
    def open_output_folder(self):
        """Open the output folder in file manager"""
        output_dir = Path.home() / "Music" / "artists"
        
        if output_dir.exists():
            try:
                import subprocess
                subprocess.Popen(['xdg-open', str(output_dir)])
                logger.debug(f"Opened output folder: {output_dir}")
            except Exception as e:
                logger.error(f"Failed to open folder: {e}")
                QMessageBox.warning(self, "Error", f"Could not open folder: {e}")
        else:
            QMessageBox.information(self, "Info", "Output folder doesn't exist yet. Complete a download first.")
    
    def clear_output(self):
        """Clear the output text area"""
        self.output_text.clear()
    
    def view_history(self):
        """View download history from log files"""
        logger.info("Opening download history")
        
        json_log = Path.home() / "youtube_downloads_log.json"
        
        if json_log.exists():
            try:
                import subprocess
                subprocess.Popen(['xdg-open', str(json_log)])
            except Exception as e:
                logger.error(f"Failed to open history file: {e}")
                QMessageBox.warning(self, "Error", f"Could not open history: {e}")
        else:
            QMessageBox.information(self, "History", "No download history found yet.")
    
    def closeEvent(self, event):
        """Handle application close - cleanup if needed"""
        logger.info("Application closing")
        
        temp_dir = TEMP_BASE
        if temp_dir.exists():
            subdirs = [d for d in temp_dir.iterdir() if d.is_dir()]
            if subdirs:
                logger.warning(f"Found {len(subdirs)} temp directories on close")
                reply = QMessageBox.question(
                    self,
                    "Cleanup",
                    f"Found {len(subdirs)} temporary download directories.\nClean them up?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    import shutil
                    for d in subdirs:
                        try:
                            shutil.rmtree(d)
                            logger.info(f"Cleaned up: {d}")
                        except Exception as e:
                            logger.error(f"Failed to cleanup {d}: {e}")
        
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = YouTubeDownloadHelperQt()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
