"""
notion_page.py - Placeholder Notion configuration page.

This is a placeholder for future Notion integration.
"""

import logging

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class NotionPage(QWidget):
    """
    Notion configuration page for MDAP.
    
    Placeholder for future Notion API integration.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Initializing NotionPage")
        self._init_ui()
        logger.info("NotionPage initialized")
    
    def _init_ui(self):
        """Initialize the UI"""
        logger.debug("Setting up NotionPage UI")
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Notion Configuration")
        title_label.setFont(QFont("", 14, QFont.Bold))
        title_label.setStyleSheet("color: #333;")
        layout.addWidget(title_label)
        
        desc_label = QLabel("Configure your Notion integration for logging downloads.")
        desc_label.setStyleSheet("color: #666;")
        layout.addWidget(desc_label)
        
        layout.addSpacing(10)
        
        config_group = QGroupBox("API Settings")
        config_layout = QVBoxLayout()
        config_layout.setSpacing(10)
        
        api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("secret_...")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        config_layout.addWidget(api_key_label)
        config_layout.addWidget(self.api_key_input)
        
        db_key_label = QLabel("Database ID:")
        self.db_key_input = QLineEdit()
        self.db_key_input.setPlaceholderText("Enter your Notion database ID")
        config_layout.addWidget(db_key_label)
        config_layout.addWidget(self.db_key_input)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        button_layout = QVBoxLayout()
        
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #548478;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: 1px solid #242424;
            }
            QPushButton:hover {
                background-color: #3f645b;
            }
        """)
        self.test_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(self.test_btn)
        
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #548478;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: 1px solid #242424;
            }
            QPushButton:hover {
                background-color: #3f645b;
            }
        """)
        self.save_btn.clicked.connect(self._save_config)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()
        
        self.setLayout(layout)
        logger.debug("NotionPage UI setup complete")
    
    def _test_connection(self):
        """Test Notion API connection"""
        logger.info("Testing Notion connection")
        
        api_key = self.api_key_input.text().strip()
        db_key = self.db_key_input.text().strip()
        
        if not api_key or not db_key:
            QMessageBox.warning(
                self, 
                "Missing Configuration",
                "Please enter both API Key and Database ID"
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
        
        api_key = self.api_key_input.text().strip()
        db_key = self.db_key_input.text().strip()
        
        if not api_key or not db_key:
            QMessageBox.warning(
                self,
                "Missing Configuration",
                "Please enter both API Key and Database ID"
            )
            return
        
        QMessageBox.information(
            self,
            "Configuration Saved",
            "Notion configuration saved!\n\n(Note: Notion integration is not yet implemented)"
        )
    
    def on_page_close(self):
        """Called when the page is closed"""
        logger.info("NotionPage: on_page_close called")
