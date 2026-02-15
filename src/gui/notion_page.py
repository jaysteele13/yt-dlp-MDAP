"""
notion_page.py - Notion configuration page for MDAP.

Provides UI for configuring Notion API integration.
"""

import logging
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QMessageBox, QDialog,
    QHBoxLayout, QTextEdit, QScrollArea, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

CONFIG_FILE = Path.home() / ".mdap" / "notion_config.json"


class NotionInfoDialog(QDialog):
    """Modal dialog with Notion configuration instructions."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to Configure Notion")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        self._init_ui()
        logger.debug("NotionInfoDialog initialized")
    
    def _init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()
        
        instructions = """
<h2>Notion Integration Setup</h2>

<p>Follow these steps to configure Notion integration:</p>

<h3>Step 1: Create a Notion Integration</h3>
<ol>
<li>Go to <a href="https://www.notion.so/my-integrations">https://www.notion.so/my-integrations</a></li>
<li>Click <b>"New integration"</b></li>
<li>Give it a name (e.g., "MDAP")</li>
<li>Select the workspace where you want to use it</li>
<li>Copy the <b>Internal Integration Secret</b></li>
</ol>

<h3>Step 2: Share a Database with the Integration</h3>
<ol>
<li>Create or open a Notion database you want to use</li>
<li>Click the <b>•••</b> menu in the top-right</li>
<li>Select <b>"Connect to"</b> and choose your integration</li>
<li>Copy the <b>Database ID</b> from the URL<br>
    (e.g., notion.so/[workspace]/<b>DATABASE_ID</b>?v=...)</li>
</ol>

<h3>Step 3: Enter Credentials</h3>
<p>Enter the Internal Integration Secret and Database ID in the form.</p>

<h3>Database Schema</h3>
<p>Your database should have these properties:</p>
<ul>
<li><b>Title</b> (Title) - Song/album title</li>
<li><b>Artist</b> (Text) - Artist name</li>
<li><b>Album</b> (Text) - Album name (optional)</li>
<li><b>Date</b> (Date) - Download date</li>
<li><b>URL</b> (URL) - YouTube link</li>
</ul>
        """
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        text_widget = QTextEdit()
        text_widget.setHtml(instructions)
        text_widget.setReadOnly(True)
        text_widget.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #333;
                border: none;
                padding: 10px;
            }
        """)
        
        scroll.setWidget(text_widget)
        layout.addWidget(scroll)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #548478;
                color: white;
                font-weight: bold;
                padding: 10px 30px;
                border: 1px solid #242424;
            }
            QPushButton:hover {
                background-color: #3f645b;
            }
            QPushButton:pressed {
                background-color: #2d4d44;
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)


class NotionPage(QWidget):
    """
    Notion configuration page for MDAP.
    
    Provides UI for entering and saving Notion API credentials.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing NotionPage")
        self._config = {}
        self._load_config()
        self._init_ui()
        logger.info("NotionPage initialized")
    
    def _load_config(self):
        """Load existing configuration from file"""
        logger.debug("Loading Notion configuration")
        
        if CONFIG_FILE.exists():
            import json
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self._config = json.load(f)
                logger.info(f"Loaded configuration from {CONFIG_FILE}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                self._config = {}
        else:
            logger.debug("No existing configuration found")
            self._config = {}
    
    def _save_config_to_file(self):
        """Save configuration to file"""
        logger.debug("Saving Notion configuration")
        
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self._config, f, indent=2)
            
            logger.info(f"Configuration saved to {CONFIG_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def _init_ui(self):
        """Initialize the UI"""
        logger.debug("Setting up NotionPage UI")
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_layout = QHBoxLayout()
        
        page_title = QLabel("Notion Configuration")
        page_title.setFont(QFont("", 14, QFont.Bold))
        page_title.setStyleSheet("color: #333;")
        title_layout.addWidget(page_title)
        
        title_layout.addStretch()
        
        self.info_btn = QPushButton("ⓘ")
        self.info_btn.setToolTip("How to configure Notion")
        self.info_btn.setFixedSize(30, 30)
        self.info_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                font-size: 16px;
                font-weight: bold;
                border-radius: 50%;
            
            }
            QPushButton:hover {
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #573d9e;
            }
        """)
        self.info_btn.clicked.connect(self._show_info_dialog)
        title_layout.addWidget(self.info_btn)
        
        layout.addLayout(title_layout)
        
        desc_label = QLabel("Configure your Notion integration for logging downloads.")
        desc_label.setStyleSheet("color: #666;")
        layout.addWidget(desc_label)
        
        layout.addSpacing(10)
        
        config_group = QGroupBox("API Settings")
        config_layout = QVBoxLayout()
        config_layout.setSpacing(15)
        
        internal_secret_label = QLabel("Internal Integration Secret:")
        internal_secret_label.setStyleSheet("font-weight: bold; color: #333;")
        self.internal_secret_input = QLineEdit()
        self.internal_secret_input.setPlaceholderText("secret_...")
        self.internal_secret_input.setEchoMode(QLineEdit.Password)
        self.internal_secret_input.setMinimumHeight(35)
        self.internal_secret_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #242424;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #548478;
            }
        """)
        
        if self._config.get("internal_secret"):
            self.internal_secret_input.setText(self._config.get("internal_secret"))
        
        config_layout.addWidget(internal_secret_label)
        config_layout.addWidget(self.internal_secret_input)
        
        config_layout.addSpacing(10)
        
        database_id_label = QLabel("Database ID:")
        database_id_label.setStyleSheet("font-weight: bold; color: #333;")
        self.database_id_input = QLineEdit()
        self.database_id_input.setPlaceholderText("Enter your Notion database ID")
        self.database_id_input.setMinimumHeight(35)
        self.database_id_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #242424;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #548478;
            }
        """)
        
        if self._config.get("database_id"):
            self.database_id_input.setText(self._config.get("database_id"))
        
        config_layout.addWidget(database_id_label)
        config_layout.addWidget(self.database_id_input)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        recent_activity_group = QGroupBox("Recent Activity")
        recent_activity_layout = QVBoxLayout()
        
        self.recent_activity_list = QTextEdit()
        self.recent_activity_list.setReadOnly(True)
        self.recent_activity_list.setMaximumHeight(150)
        self.recent_activity_list.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #242424;
                padding: 8px;
                font-size: 12px;
                font-family: 'Courier New', 'Monaco', 'Consolas', monospace;
            }
        """)
        self.recent_activity_list.setPlaceholderText("No recent entries. Configure API and database to see recent activity.")
        recent_activity_layout.addWidget(self.recent_activity_list)
        
        refresh_btn_layout = QHBoxLayout()
        self.refresh_activity_btn = QPushButton("Refresh Recent Activity")
        self.refresh_activity_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #242424;
                font-weight: bold;
                font-size: 12px;
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
        self.refresh_activity_btn.clicked.connect(self._load_recent_activity)
        refresh_btn_layout.addWidget(self.refresh_activity_btn)
        refresh_btn_layout.addStretch()
        recent_activity_layout.addLayout(refresh_btn_layout)
        
        recent_activity_group.setLayout(recent_activity_layout)
        layout.addWidget(recent_activity_group)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.setMinimumHeight(40)
        self.test_btn.setStyleSheet("""
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
        self.test_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(self.test_btn)
        
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setStyleSheet("""
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
                background-color: #2d4d44;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.save_btn.clicked.connect(self._save_config)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
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
                background-color: #9785c9;
                border: 1px solid #242424
            }
        """)
        self.notion_progress_bar.setVisible(False)
        layout.addWidget(self.notion_progress_bar)
        
        self.setLayout(layout)
        logger.debug("NotionPage UI setup complete")
    
    def _show_info_dialog(self):
        """Show the Notion configuration instructions dialog"""
        logger.debug("Showing Notion info dialog")
        dialog = NotionInfoDialog(self)
        dialog.exec_()
    
    def _test_connection(self):
        """Test Notion API connection"""
        logger.info("Testing Notion connection")
        
        internal_secret = self.internal_secret_input.text().strip()
        
        if not internal_secret:
            QMessageBox.warning(
                self,
                "Missing Configuration",
                "Please enter your Internal Integration Secret"
            )
            return
        
        self.notion_progress_bar.setVisible(True)
        self.notion_progress_bar.setMaximum(0)
        self.test_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        
        from notion import test_notion_connection
        
        success, error, databases = test_notion_connection(internal_secret)
        
        self.notion_progress_bar.setVisible(False)
        self.notion_progress_bar.setMaximum(100)
        self.notion_progress_bar.setValue(100)
        self.test_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        if success:
            db_info = ""
            if databases:
                db_info = f"\nFound {len(databases)} database(s):\n"
                for db in databases:
                    db_info += f"  - {db['title']}: {db['id']}\n"
            
            QMessageBox.information(
                self,
                "Connection Successful",
                f"✓ Notion connection successful!{db_info}"
            )
        else:
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"✗ Failed to connect to Notion:\n{error}"
            )
    
    def _load_recent_activity(self):
        """Load recent activity from Notion database"""
        logger.info("Loading recent Notion activity")
        
        from notion import get_recent_entries, is_notion_configured
        
        if not is_notion_configured():
            self.recent_activity_list.setPlainText("Notion API is not configured.\nPlease enter your Internal Integration Secret and save.")
            return
        
        from notion import get_database_id
        db_id = get_database_id()
        if not db_id:
            self.recent_activity_list.setPlainText("Database ID is not configured.\nPlease enter your Database ID and save.")
            return
        
        success, entries, error = get_recent_entries(limit=5)
        
        if success:
            if not entries:
                self.recent_activity_list.setPlainText("No recent entries found in the database.")
            else:
                def format_table(entries):
                    if not entries:
                        return ""
                    
                    processed = []
                    for entry in entries:
                        album = entry.get("album", "Unknown Album")
                        artist = entry.get("artist", "Unknown Artist")
                        song_count = entry.get("song_count", 0)
                        date = entry.get("date", "")
                        
                        if date:
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
                                date = dt.strftime("%Y-%m-%d %H:%M")
                            except:
                                pass
                        
                        processed.append({
                            "album": album,
                            "artist": artist,
                            "songs": str(song_count) if song_count else "None",
                            "date": date
                        })
                    
                    col_widths = {
                        "album": max(len("Album"), 40),
                        "artist": max(len("Artist"), 40),
                        "songs": max(len("Songs"), 6),
                        "date": max(len("Date"), 16)
                    }
                    
                    def make_row(data):
                        return (
                            f"| {data['album']:<{col_widths['album']}} "
                            f"| {data['artist']:<{col_widths['artist']}} "
                            f"| {data['songs']:<{col_widths['songs']}} "
                            f"| {data['date']:<{col_widths['date']}} |"
                        )
                    
                    separator = (
                        f"|{'-' * (col_widths['album'] + 2)}"
                        f"|{'-' * (col_widths['artist'] + 2)}"
                        f"|{'-' * (col_widths['songs'] + 2)}"
                        f"|{'-' * (col_widths['date'] + 2)}|"
                    )
                    
                    header = (
                        f"| {'Album':<{col_widths['album']}} "
                        f"| {'Artist':<{col_widths['artist']}} "
                        f"| {'Songs':<{col_widths['songs']}} "
                        f"| {'Date':<{col_widths['date']}} |"
                    )
                    
                    lines = [header, separator]
                    for row in processed:
                        lines.append(make_row(row))
                    
                    return "\n".join(lines)
                
                display_text = format_table(entries)
                self.recent_activity_list.setPlainText(display_text)
        else:
            self.recent_activity_list.setPlainText(f"Failed to load recent activity:\n{error}")
    
    def _save_config(self):
        """Save Notion configuration"""
        logger.info("Saving Notion configuration")
        
        internal_secret = self.internal_secret_input.text().strip()
        database_id = self.database_id_input.text().strip()
        
        if not internal_secret:
            QMessageBox.warning(
                self,
                "Missing Configuration",
                "Please enter your Internal Integration Secret"
            )
            return
        
        self.notion_progress_bar.setVisible(True)
        self.notion_progress_bar.setMaximum(0)
        self.test_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        
        self._config["internal_secret"] = internal_secret
        self._config["NOTION_API_KEY"] = internal_secret
        self._config["database_id"] = database_id
        
        if self._save_config_to_file():
            from notion import refresh_config
            refresh_config()
            self._load_recent_activity()
            
            self.notion_progress_bar.setVisible(False)
            self.notion_progress_bar.setMaximum(100)
            self.notion_progress_bar.setValue(100)
            self.test_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            
            QMessageBox.information(
                self,
                "Configuration Saved",
                "Notion configuration saved successfully!"
            )
        else:
            self.notion_progress_bar.setVisible(False)
            self.notion_progress_bar.setMaximum(100)
            self.notion_progress_bar.setValue(100)
            self.test_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            
            QMessageBox.critical(
                self,
                "Error",
                "Failed to save configuration"
            )
    
    def on_page_close(self):
        """Called when the page is closed"""
        logger.info("NotionPage: on_page_close called")
    
    def on_page_show(self):
        """Called when the page is shown/activated"""
        logger.info("NotionPage: on_page_show called")
        self._load_recent_activity()
