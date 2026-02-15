#!/usr/bin/env python3
"""
download_gui.py - Main entry point for MDAP with multi-screen navigation.

Replaces gui_gt.py with a modular multi-screen architecture:
- Download page for YouTube downloads
- Notion page for configuration (placeholder)

Usage:
    python src/download_gui.py
    python -m src.download_gui
"""

import sys
import logging
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from gui.base_window import BaseWindow
from gui.download_page import DownloadPage
from gui.notion_page import NotionPage

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


PAGES = [
    {'id': 'download', 'label': 'Download'},
    {'id': 'notion', 'label': 'Notion'},
]


def main():
    """Main entry point for the application."""
    logger.info("Starting MDAP application")
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    icon_path = Path(__file__).parent.parent / 'assets' / 'icon' / 'mdap-yt-dlp-gui.png'
    app.setWindowIcon(QIcon(str(icon_path)))
    
    logger.debug("Creating main window")
    window = BaseWindow(
        pages=PAGES,
        default_page='download',
        window_title='MDAP',
        geometry=(100, 100, 900, 700)
    )
    
    logger.debug("Creating DownloadPage")
    download_page = DownloadPage()
    
    logger.debug("Creating NotionPage")
    notion_page = NotionPage()
    
    logger.debug("Registering pages with window")
    window.register_page('download', download_page)
    window.register_page('notion', notion_page)
    
    logger.debug("Showing initial page")
    window.show_initial_page()
    
    logger.info("Application ready, showing window")
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
