"""
download_page.py - Download functionality page for MDAP.

Refactored from gui_gt.py to work as a page in the multi-screen application.
Uses dependency injection for workflow to allow reuse and testing.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QGroupBox, QProgressBar, 
    QRadioButton, QButtonGroup, QFrame, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QFontDatabase

if TYPE_CHECKING:
    from workflow import DownloadWorkflow

logger = logging.getLogger(__name__)


class DownloadThread(QThread):
    """Thread for running download workflow without blocking UI"""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str, str, int)
    error = pyqtSignal(str)
    
    def __init__(self, workflow: 'DownloadWorkflow', url: str):
        super().__init__()
        self.workflow = workflow
        self.url = url
        logger.debug(f"DownloadThread created for URL: {url}")
    
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


class EditArtistAlbumDialog(QDialog):
    """Dialog for editing artist/album values"""
    
    def __init__(self, parent, artist: str, album: str, is_album: bool):
        super().__init__(parent)
        self.is_album = is_album
        self.setWindowTitle("Edit Album / Artist")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        artist_label = QLabel("Artist:")
        self.artist_input = QLineEdit(artist)
        self.artist_input.setPlaceholderText(artist or "Enter artist name")
        layout.addWidget(artist_label)
        layout.addWidget(self.artist_input)
        
        if is_album:
            album_label = QLabel("Album:")
            self.album_input = QLineEdit(album)
            self.album_input.setPlaceholderText(album or "Enter album name")
            layout.addWidget(album_label)
            layout.addWidget(self.album_input)
        else:
            self.album_input = None
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        logger.debug("EditArtistAlbumDialog initialized")
    
    def get_values(self) -> tuple:
        artist = self.artist_input.text().strip()
        album = self.album_input.text().strip() if self.album_input else ""
        return artist, album


class ConfirmDialog(QDialog):
    """Custom dialog for confirming artist/album after download"""
    
    def __init__(self, parent, artist: str, album: str, file_count: int, is_album: bool):
        super().__init__(parent)
        self.is_album = is_album
        self.auto_artist = artist or ""
        self.auto_album = album or ""
        self.file_count = file_count
        self.setWindowTitle("Confirm Details")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout()
        
        title_label = QLabel("<b>Download Complete!</b>")
        title_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(title_label)
        
        download_type = "Album" if is_album else "Song"
        type_label = QLabel(f"Type: {download_type}")
        layout.addWidget(type_label)
        
        files_label = QLabel(f"Files downloaded: {file_count}")
        layout.addWidget(files_label)
        
        layout.addSpacing(10)
        
        artist_text = self.auto_artist or "Unknown"
        self.artist_display = QLabel(f"<b>Artist:</b> {artist_text}")
        layout.addWidget(self.artist_display)
        
        if is_album:
            album_text = self.auto_album or "Unknown"
            self.album_display = QLabel(f"<b>Album:</b> {album_text}")
            layout.addWidget(self.album_display)
        else:
            self.album_display = None
        
        self.edit_btn = QPushButton("Edit Album / Artist")
        self.edit_btn.clicked.connect(self._show_edit_dialog)
        layout.addWidget(self.edit_btn)
        
        layout.addSpacing(20)
        
        button_layout = QHBoxLayout()
        self.confirm_btn = QPushButton("Confirm & Move")
        self.confirm_btn.setDefault(True)
        self.cancel_btn = QPushButton("Cancel")
        self.confirm_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.confirm_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        logger.debug("ConfirmDialog initialized")
    
    def _show_edit_dialog(self):
        dialog = EditArtistAlbumDialog(self, self.auto_artist, self.auto_album, self.is_album)
        if dialog.exec_() == QDialog.Accepted:
            self.auto_artist, self.auto_album = dialog.get_values()
            
            artist = self.auto_artist or "Unknown"
            self.artist_display.setText(f"<b>Artist:</b> {artist}")
            
            if self.is_album and self.album_display:
                album_text = self.auto_album or "Unknown"
                self.album_display.setText(f"<b>Album:</b> {album_text}")
    
    def get_values(self) -> tuple:
        return self.auto_artist, self.auto_album


class DownloadPage(QWidget):
    """
    Download page widget for MDAP application.
    
    This page provides the YouTube download functionality and can be
    used as part of a multi-screen application.
    """
    
    def __init__(
        self, 
        workflow: Optional['DownloadWorkflow'] = None,
        default_output_dir: Optional[Path] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the download page.
        
        Args:
            workflow: DownloadWorkflow instance (created if not provided)
            default_output_dir: Default output directory for downloads
            parent: Parent widget
        """
        super().__init__(parent)
        
        logger.info("Initializing DownloadPage")
        
        self.workflow = workflow
        self.download_thread: Optional[DownloadThread] = None
        self.is_album_type = True
        self.default_output_dir = default_output_dir or Path.home() / "Music" / "artists"
        
        self.font_family_medium = None
        self.font_family_black = None
        
        self._load_custom_font()
        self._init_workflow()
        self._init_ui()
        
        logger.info("DownloadPage initialized successfully")
    
    def _init_workflow(self):
        """Initialize the download workflow"""
        if self.workflow is not None:
            logger.debug("Using provided workflow")
            return
        
        logger.debug("Creating new workflow for DownloadPage")
        
        from workflow import DownloadWorkflow
        from logger import MultiLogger, FileLogger, JSONLogger
        
        backend_logger = MultiLogger([
            FileLogger(),
            JSONLogger()
        ])
        
        self.workflow = DownloadWorkflow(
            base_output_dir=self.default_output_dir,
            logger_instance=backend_logger
        )
        
        logger.info(f"Workflow created with output dir: {self.default_output_dir}")
    
    def _init_ui(self):
        """Initialize the user interface"""
        logger.debug("Initializing DownloadPage UI")
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("Music Download Automation Pipeline")
        if self.font_family_black:
            title_label.setFont(QFont(self.font_family_black, 14, QFont.ExtraBold))
        elif self.font_family_medium:
            title_label.setFont(QFont(self.font_family_medium, 14))
        else:
            title_label.setFont(QFont("", 14, QFont.Bold))
        title_label.setStyleSheet("color: #333;")
        layout.addWidget(title_label)
        
        input_group = QGroupBox()
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
        
        self.album_radio = QRadioButton("Album / Playlist")
        self.album_radio.setChecked(True)
        self.song_radio = QRadioButton("Single Song")
        
        self.type_group.addButton(self.album_radio)
        self.type_group.addButton(self.song_radio)
        
        self.album_radio.toggled.connect(lambda checked: self._set_album_type(True) if checked else None)
        self.song_radio.toggled.connect(lambda checked: self._set_album_type(False) if checked else None)
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.album_radio)
        type_layout.addWidget(self.song_radio)
        type_layout.addStretch()
        
        input_layout.addLayout(type_layout)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("Download")
        self.download_btn.setMinimumHeight(45)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #548478;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #242424;
            }
            QPushButton:hover {
                background-color: #3f645b;
            }
            QPushButton:pressed {
                background-color: #242424;
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
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #242424;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #242424;
            }
            QPushButton:hover {
                background-color: #9785c9;
                color: #fff
            }
            QPushButton:pressed {
                background-color: #573d9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_download)
        
        button_layout.addWidget(self.download_btn, 2)
        button_layout.addWidget(self.cancel_btn, 1)
        layout.addLayout(button_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e0e0e0;
                border: 1px solid #242424
            }
            QProgressBar::chunk {
                background-color: #9785c9;
                border: 1px solid #242424
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.notion_progress_bar = QProgressBar()
        self.notion_progress_bar.setTextVisible(False)
        self.notion_progress_bar.setMaximumHeight(6)
        self.notion_progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e0e0e0;
                border: 1px solid #242424
            }
            QProgressBar::chunk {
                background-color: #548478;
                border: 1px solid #242424
            }
        """)
        self.notion_progress_bar.setVisible(False)
        layout.addWidget(self.notion_progress_bar)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        output_label = QLabel("Progress Output:")
        if self.font_family_medium:
            output_label.setFont(QFont(self.font_family_medium, 10, QFont.ExtraBold))
        else:
            output_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(250)
        if self.font_family_medium:
            self.output_text.setFont(QFont(self.font_family_medium, 8))
        else:
            self.output_text.setFont(QFont("Monospace", 8))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
        """)
        layout.addWidget(self.output_text)
        
        output_layout = QHBoxLayout()
        
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText(str(self.default_output_dir))
        self.output_dir_input.textChanged.connect(self._on_output_dir_changed)
        
        self.update_dir_btn = QPushButton("Update Output Folder")
        self.update_dir_btn.setVisible(False)
        self.update_dir_btn.clicked.connect(self._update_output_folder)
        
        self.clear_btn = QPushButton("Clear Output")
        self.clear_btn.clicked.connect(self.clear_output)
        
        output_layout.addWidget(self.output_dir_input)
        output_layout.addWidget(self.update_dir_btn)
        output_layout.addWidget(self.clear_btn)
        
        layout.addLayout(output_layout)
        
        self.setLayout(layout)
        
        self.link_entry.setFocus()
        
        logger.debug("DownloadPage UI initialized")
    
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
        self.cancel_btn.setVisible(downloading)
        self.link_entry.setEnabled(not downloading)
        self.album_radio.setEnabled(not downloading)
        self.song_radio.setEnabled(not downloading)
        
        if downloading:
            self.download_btn.setText("Downloading...")
            self.progress_bar.setMaximum(0)
        else:
            self.download_btn.setText("Download")
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(100)
    
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
        
        if dialog.exec_() == QDialog.Accepted:
            confirmed_artist, confirmed_album = dialog.get_values()
            
            if not confirmed_artist:
                QMessageBox.warning(self, "Error", "Artist name is required")
                return
            
            if self.is_album_type and not confirmed_album:
                QMessageBox.warning(self, "Error", "Album name is required")
                return
            
            self.confirm_and_move(confirmed_artist, confirmed_album)
        else:
            self.append_output("<span style='color: #CE9178;'>Download cancelled by user</span>")
            self.workflow.cancel()
            
            self.link_entry.clear()
            self.link_entry.setFocus()
    
    def confirm_and_move(self, artist: str, album: str):
        """Confirm and move files to final destination"""
        logger.info(f"Confirming move - Artist: {artist}, Album: {album}")
        
        self.append_output(f"<span style='color: #569CD6;'>Moving to: {artist} - {album}</span>")
        
        success, dest, error, file_count = self.workflow.confirm_and_move(
            artist=artist,
            album=album,
            is_album_type=self.is_album_type
        )
        
        if success:
            self.append_output(f"<span style='color: #4CAF50;'>✓ Files moved successfully!</span>")
            self.append_output(f"<span style='color: #888;'>Location: {dest}</span>")
            self.append_output(f"<span style='color: #888;'>Files: {file_count}</span>")
            
            from notion import check_notion_api_configured, create_database_entry
            
            is_configured, config_error = check_notion_api_configured()
            
            notion_success = False
            notion_error = None
            
            if is_configured:
                url = self.link_entry.text().strip()
                
                self.append_output("")
                self.append_output(f"<span style='color: #569CD6;'>Saving to Notion...</span>")
                
                self.notion_progress_bar.setVisible(True)
                self.notion_progress_bar.setMaximum(0)
                
                notion_success, _, notion_error = create_database_entry(
                    artist_name=artist,
                    album_name=album,
                    url=url,
                    song_count=file_count
                )
                
                self.notion_progress_bar.setVisible(False)
                self.notion_progress_bar.setMaximum(100)
                self.notion_progress_bar.setValue(100)
                
                if notion_success:
                    self.append_output(f"<span style='color: #4CAF50;'>✓ Notion entry created!</span>")
                else:
                    self.append_output(f"<span style='color: #F44747;'>✗ Notion save failed: {notion_error}</span>")
            
            self.append_output("")
            self.append_output(f"<span style='color: #4CAF50;'>{'='*50}</span>")
            self.append_output("")
            
            if notion_success:
                reply = QMessageBox.question(
                    self,
                    "Download and Notion Successful",
                    f"Download and Notion entry saved!\n\nSaved to:\n{dest}\n\nOpen folder?",
                    QMessageBox.Yes | QMessageBox.No
                )
            else:
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
            QMessageBox.warning(self, "Error", f"Failed to move files: {error}")
        
        self.link_entry.clear()
        self.link_entry.setFocus()
    
    def on_download_error(self, error: str):
        """Handle download error"""
        self.set_downloading(False)
        
        self.append_output("")
        self.append_output(f"<span style='color: #F44747;'>✗ Error: {error}</span>")
        self.append_output("")
        
        QMessageBox.critical(self, "Download Error", error)
        
        self.link_entry.setFocus()
    
    def _on_output_dir_changed(self, text: str):
        """Show/hide update button based on whether path changed from default"""
        input_path = text.strip()
        default_path_str = str(self.default_output_dir)
        
        if input_path and input_path != default_path_str:
            self.update_dir_btn.setVisible(True)
        else:
            self.update_dir_btn.setVisible(False)
    
    def _update_output_folder(self):
        """Update the output folder"""
        new_path = self.output_dir_input.text().strip()
        
        if not new_path:
            QMessageBox.warning(self, "Error", "Please enter a valid output path")
            return
        
        new_dir = Path(new_path)
        
        try:
            new_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not create directory: {e}")
            return
        
        self.default_output_dir = new_dir
        self.output_dir_input.setPlaceholderText(str(new_dir))
        self.output_dir_input.clear()
        self.update_dir_btn.setVisible(False)
        
        self.workflow.base_output_dir = new_dir
        logger.info(f"Output folder updated to: {new_dir}")
        
        QMessageBox.information(self, "Success", f"Output folder updated to:\n{new_dir}")
    
    def clear_output(self):
        """Clear the output text area"""
        self.output_text.clear()
        logger.debug("Output cleared")
    
    def _load_custom_font(self):
        """Load Geist Mono font from assets"""
        base_path = Path(__file__).parent.parent.parent / "assets" / "font" / "Geist_Mono"
        
        font_id_medium = QFontDatabase.addApplicationFont(
            str(base_path / "static" / "GeistMono-Medium.ttf")
        )
        font_id_black = QFontDatabase.addApplicationFont(
            str(base_path / "static" / "GeistMono-Bold.ttf")
        )
        
        self.font_family_medium = None
        self.font_family_black = None
        
        if font_id_medium != -1:
            self.font_family_medium = QFontDatabase.applicationFontFamilies(font_id_medium)[0]
            logger.debug(f"Loaded custom font: {self.font_family_medium}")
        else:
            logger.warning(f"Failed to load medium font from: {base_path}")
        
        if font_id_black != -1:
            self.font_family_black = QFontDatabase.applicationFontFamilies(font_id_black)[0]
            logger.debug(f"Loaded black font: {self.font_family_black}")
    
    def on_page_close(self):
        """Called when the page is closed or application exits"""
        logger.info("DownloadPage: on_page_close called")
