"""
navbar.py - Reusable navigation bar widget for multi-screen PyQt5 applications.

Features:
- Signal-based page switching
- Customizable buttons
- Shared styling
"""

import logging
from pathlib import Path
from typing import List, Optional

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QFontDatabase

logger = logging.getLogger(__name__)


class NavBar(QWidget):
    """
    Reusable navigation bar widget.
    
    Signals:
        page_changed(str): Emitted when a navigation button is clicked, 
                          passes the page identifier
    """
    
    page_changed = pyqtSignal(str)
    
    NAV_BUTTON_STYLE = """
        QPushButton {
            background-color: transparent;
            color: #666666;
            border: none;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #f0f0f0;
            color: #333333;
        }
        QPushButton:pressed {
            background-color: #e0e0e0;
        }
    """
    
    ACTIVE_BUTTON_STYLE = """
        QPushButton {
            background-color: transparent;
            color: #548478;
            border: none;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #f0f0f0;
            color: #548478;
        }
    """
    
    SEPARATOR_STYLE = """
        QFrame {
            background-color: #e0e0e0;
            max-width: 1px;
        }
    """
    
    def __init__(self, pages: Optional[List[dict]] = None, parent: Optional[QWidget] = None):
        """
        Initialize the navigation bar.
        
        Args:
            pages: List of dicts with 'id' and 'label' keys for each page
                   Example: [{'id': 'download', 'label': 'Download'}, ...]
            parent: Parent widget
        """
        super().__init__(parent)
        
        logger.debug("Initializing NavBar")
        
        self._buttons = {}
        self._active_page_id = None
        self._pages = pages or []
        
        self.font_family_medium = None
        self.font_family_black = None
        self._load_custom_font()
        
        self._setup_ui()
        
        logger.info(f"NavBar initialized with {len(self._pages)} pages")
    
    def _setup_ui(self):
        """Set up the navigation bar UI"""
        logger.debug("Setting up NavBar UI")
        
        self.setFixedHeight(50)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        layout.addSpacing(0)
        
        for page in self._pages:
            page_id = page.get('id')
            page_label = page.get('label', page_id)
            
            btn = QPushButton(page_label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self.NAV_BUTTON_STYLE)
            if self.font_family_medium:
                btn.setFont(QFont(self.font_family_medium, 10, QFont.Medium))
            else:
                btn.setFont(QFont("", 10, QFont.Medium))
            btn.clicked.connect(lambda checked, pid=page_id: self._on_button_clicked(pid))
            
            self._buttons[page_id] = btn
            layout.addWidget(btn)
            
            if page != self._pages[-1]:
                separator = QFrame()
                separator.setFrameShape(QFrame.VLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet(self.SEPARATOR_STYLE)
                layout.addWidget(separator)
        
        layout.addStretch()
        
        self.setLayout(layout)
    
    def _on_button_clicked(self, page_id: str):
        """Handle button click - emit page change signal"""
        logger.debug(f"NavBar: Button clicked for page: {page_id}")
        self.page_changed.emit(page_id)
    
    def set_active_page(self, page_id: str):
        """
        Set the active/selected page.
        
        Args:
            page_id: The identifier of the page to mark as active
        """
        logger.debug(f"NavBar: Setting active page to: {page_id}")
        
        if self._active_page_id == page_id:
            logger.debug(f"NavBar: Page {page_id} is already active, skipping")
            return
        
        for pid, btn in self._buttons.items():
            if pid == page_id:
                btn.setStyleSheet(self.ACTIVE_BUTTON_STYLE)
                if self.font_family_black:
                    btn.setFont(QFont(self.font_family_black, 10, QFont.DemiBold))
                elif self.font_family_medium:
                    btn.setFont(QFont(self.font_family_medium, 10, QFont.DemiBold))
                else:
                    btn.setFont(QFont("", 10, QFont.DemiBold))
            else:
                btn.setStyleSheet(self.NAV_BUTTON_STYLE)
                if self.font_family_medium:
                    btn.setFont(QFont(self.font_family_medium, 10, QFont.Medium))
                else:
                    btn.setFont(QFont("", 10, QFont.Medium))
        
        self._active_page_id = page_id
        logger.info(f"NavBar: Active page set to: {page_id}")
    
    def add_page(self, page_id: str, label: str):
        """
        Add a new page to the navigation bar dynamically.
        
        Args:
            page_id: Unique identifier for the page
            label: Display label for the button
        """
        logger.debug(f"NavBar: Adding page {page_id} with label '{label}'")
        
        if page_id in self._buttons:
            logger.warning(f"NavBar: Page {page_id} already exists, skipping")
            return
        
        btn = QPushButton(label)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self.NAV_BUTTON_STYLE)
        if self.font_family_medium:
            btn.setFont(QFont(self.font_family_medium, 10, QFont.Medium))
        else:
            btn.setFont(QFont("", 10, QFont.Medium))
        btn.clicked.connect(lambda checked, pid=page_id: self._on_button_clicked(pid))
        
        self._buttons[page_id] = btn
        
        layout = self.layout()
        insert_pos = layout.count() - 1
        
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(self.SEPARATOR_STYLE)
        
        layout.insertWidget(insert_pos, separator)
        layout.insertWidget(insert_pos + 1, btn)
        
        self._pages.append({'id': page_id, 'label': label})
        
        logger.info(f"NavBar: Added page {page_id}")
    
    def _load_custom_font(self):
        """Load custom fonts from application resources"""
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
    
    def get_active_page(self) -> Optional[str]:
        """Get the currently active page identifier."""
        return self._active_page_id
