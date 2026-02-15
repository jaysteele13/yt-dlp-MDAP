"""
base_window.py - Base window class with multi-screen navigation support.

Features:
- QStackedWidget for page switching
- NavBar integration
- Page registration system
- Common styling and layout
"""

import logging
from typing import Dict, Optional, Any

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFrame, 
    QMessageBox, QStackedWidget
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QFontDatabase

from .navbar import NavBar

logger = logging.getLogger(__name__)


class BaseWindow(QMainWindow):
    """
    Base window class with navigation support.
    
    Signals:
        page_changed(str): Emitted when page changes, passes page_id
    """
    
    page_changed = pyqtSignal(str)
    
    def __init__(
        self, 
        pages: Optional[list] = None,
        default_page: str = "download",
        window_title: str = "MDAP",
        geometry: tuple = (100, 100, 900, 700)
    ):
        """
        Initialize the base window.
        
        Args:
            pages: List of page definitions
                  Example: [{'id': 'download', 'label': 'Download'}, ...]
            default_page: The page to show initially
            window_title: Window title
            geometry: Window geometry (x, y, width, height)
        """
        super().__init__()
        
        logger.info(f"Initializing BaseWindow with title: {window_title}")
        
        self._pages: Dict[str, QWidget] = {}
        self._page_configs = pages or []
        self._default_page = default_page
        self._font_family_medium = None
        self._font_family_black = None
        
        self.setWindowTitle(window_title)
        self.setGeometry(*geometry)
        
        self._load_custom_font()
        self._setup_ui()
        self._connect_signals()
        
        logger.info("BaseWindow initialized successfully")
    
    def _setup_ui(self):
        """Set up the base window UI"""
        logger.debug("Setting up BaseWindow UI")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.navbar = NavBar(pages=self._page_configs)
        main_layout.addWidget(self.navbar)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(separator)
        
        self.page_stack = QStackedWidget()
        main_layout.addWidget(self.page_stack)
        
        central_widget.setLayout(main_layout)
        
        logger.debug("BaseWindow UI setup complete")
    
    def _connect_signals(self):
        """Connect navigation signals"""
        logger.debug("Connecting BaseWindow signals")
        self.navbar.page_changed.connect(self._on_page_changed)
    
    def _on_page_changed(self, page_id: str):
        """Handle page change from navbar"""
        logger.debug(f"BaseWindow: Page change requested to: {page_id}")
        
        if page_id not in self._pages:
            logger.warning(f"BaseWindow: Page '{page_id}' not registered")
            return
        
        self.page_stack.setCurrentWidget(self._pages[page_id])
        self.navbar.set_active_page(page_id)
        self.page_changed.emit(page_id)
        
        logger.info(f"BaseWindow: Switched to page: {page_id}")
    
    def register_page(self, page_id: str, page_widget: QWidget) -> bool:
        """
        Register a page widget with the window.
        
        Args:
            page_id: Unique identifier for the page
            page_widget: QWidget instance for the page
            
        Returns:
            True if registration successful, False otherwise
        """
        logger.debug(f"BaseWindow: Registering page: {page_id}")
        
        if page_id in self._pages:
            logger.warning(f"BaseWindow: Page '{page_id}' already registered")
            return False
        
        self._pages[page_id] = page_widget
        self.page_stack.addWidget(page_widget)
        
        logger.info(f"BaseWindow: Registered page: {page_id}")
        return True
    
    def get_page(self, page_id: str) -> Optional[QWidget]:
        """
        Get a registered page widget by ID.
        
        Args:
            page_id: Page identifier
            
        Returns:
            The page widget or None if not found
        """
        return self._pages.get(page_id)
    
    def switch_to_page(self, page_id: str):
        """
        Programmatically switch to a page.
        
        Args:
            page_id: The page to switch to
        """
        logger.debug(f"BaseWindow: Programmatic switch to: {page_id}")
        self._on_page_changed(page_id)
    
    def get_current_page_id(self) -> Optional[str]:
        """Get the currently displayed page ID."""
        current_widget = self.page_stack.currentWidget()
        for pid, widget in self._pages.items():
            if widget == current_widget:
                return pid
        return None
    
    def _load_custom_font(self):
        """Load custom fonts from assets"""
        from pathlib import Path
        
        logger.debug("Loading custom fonts")
        
        base_path = Path(__file__).parent.parent.parent / "assets" / "font" / "Geist_Mono"
        
        font_id_medium = QFontDatabase.addApplicationFont(
            str(base_path / "static" / "GeistMono-Medium.ttf")
        )
        font_id_black = QFontDatabase.addApplicationFont(
            str(base_path / "static" / "GeistMono-Bold.ttf")
        )
        
        if font_id_medium != -1:
            self._font_family_medium = QFontDatabase.applicationFontFamilies(font_id_medium)[0]
            logger.debug(f"Loaded medium font: {self._font_family_medium}")
        else:
            logger.warning(f"Failed to load medium font from: {base_path}")
        
        if font_id_black != -1:
            self._font_family_black = QFontDatabase.applicationFontFamilies(font_id_black)[0]
            logger.debug(f"Loaded black font: {self._font_family_black}")
        else:
            logger.warning(f"Failed to load black font from: {base_path}")
    
    def get_font_family(self, style: str = "medium") -> Optional[str]:
        """
        Get the custom font family.
        
        Args:
            style: 'medium' or 'black'
            
        Returns:
            Font family name or None
        """
        if style == "black":
            return self._font_family_black
        return self._font_family_medium
    
    def create_font(self, size: int = 10, weight: str = "medium") -> QFont:
        """
        Create a QFont with custom font if available.
        
        Args:
            size: Font size
            weight: 'medium' or 'black'
            
        Returns:
            QFont instance
        """
        font_family = self.get_font_family(weight)
        if font_family:
            return QFont(font_family, size)
        return QFont("", size)
    
    def show_initial_page(self):
        """Show the default/initial page."""
        logger.debug(f"BaseWindow: Showing initial page: {self._default_page}")
        
        if self._default_page in self._pages:
            self._on_page_changed(self._default_page)
        elif self._pages:
            first_page_id = list(self._pages.keys())[0]
            self._on_page_changed(first_page_id)
        else:
            logger.warning("BaseWindow: No pages registered!")
    
    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("BaseWindow: Close event triggered")
        
        for page_id, page in self._pages.items():
            if hasattr(page, 'on_page_close'):
                logger.debug(f"BaseWindow: Calling on_page_close for {page_id}")
                page.on_page_close()
        
        event.accept()
        logger.info("BaseWindow: Close event accepted")
