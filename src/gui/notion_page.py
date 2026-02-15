"""
notion_page.py - Notion configuration page for MDAP.

Provides UI for configuring Notion API integration.
"""

import logging
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QMessageBox, QDialog,
    QHBoxLayout, QTextEdit, QScrollArea
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
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
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
        
        QMessageBox.information(
            self,
            "Notion Connection",
            "Notion integration is not yet implemented.\n\nThis is a placeholder for future Notion API integration."
        )
    
    def _save_config(self):
        """Save Notion configuration"""
        logger.info("Saving Notion configuration")
        
        internal_secret = self.internal_secret_input.text().strip()
        
        if not internal_secret:
            QMessageBox.warning(
                self,
                "Missing Configuration",
                "Please enter your Internal Integration Secret"
            )
            return
        
        self._config["internal_secret"] = internal_secret
        
        if self._save_config_to_file():
            QMessageBox.information(
                self,
                "Configuration Saved",
                "Notion configuration saved successfully!"
            )
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to save configuration"
            )
    
    def on_page_close(self):
        """Called when the page is closed"""
        logger.info("NotionPage: on_page_close called")
