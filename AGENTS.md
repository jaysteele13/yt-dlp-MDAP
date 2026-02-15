# AGENTS.md - Development Guide for MDAP

MDAP (Music Download Assistant Project) is a Python application for downloading audio from YouTube with metadata management.

## Project Structure

```
MDAP/
├── src/
│   ├── core.py          # Business logic (DownloadManager)
│   ├── downloader.py   # yt-dlp operations (YTDLPDownloader)
│   ├── logger.py        # Logging backends (abstract + implementations)
│   ├── notion.py        # Notion API integration
│   ├── workflow.py      # Download workflow orchestration
│   ├── download_gui.py  # Main entry point for GUI
│   └── gui/
│       ├── __init__.py      # GUI package exports
│       ├── base_window.py   # Base window with navigation
│       ├── navbar.py        # Navigation bar widget
│       ├── download_page.py # Download page UI
│       └── notion_page.py   # Notion configuration UI
├── assets/
│   └── metadata_example.json
├── planning/
└── __pycache__/
```

## Notion Integration

### Configuration

The Notion integration uses a configuration file stored at `~/.mdap/notion_config.json`:

```json
{
  "NOTION_API_KEY": "secret_...",
  "internal_secret": "secret_...",
  "database_id": "your-database-id"
}
```

### API Functions (src/notion.py)

- `get_notion_api_key()` - Load API key from config
- `get_database_id()` - Load database ID from config
- `is_notion_configured()` - Check if API is configured
- `check_notion_api_configured()` - Returns `(is_configured, error_message)`
- `test_notion_connection(api_key)` - Test connection, returns `(success, error, databases)`
- `create_database_entry(artist_name, album_name, url, song_count)` - Add entry to Notion
- `get_recent_entries(limit)` - Get recent entries from database

### Database Schema

The Notion database should have these properties:
- **Album Name** (Title) - Album title
- **Artist Name** (Text) - Artist name
- **Date** (Date) - Download date
- **URL** (URL) - YouTube link
- **Song Count** (Number) - Number of songs (optional)

## Commands

### Running the Application

```bash
# Run GUI (requires PyQt5)
python src/download_gui.py

# Or as module
python -m src.download_gui
```

### Dependencies

- Python 3.8+
- PyQt5 (`pip install PyQt5`)
- yt-dlp (`pip install yt-dlp` or `sudo apt install yt-dlp`)

### Testing

No formal test suite exists yet. Test new code manually or add tests using `pytest`.

### Linting

No formal linter configured. Before committing, ensure:
- Python syntax is valid (`python -m py_compile src/*.py`)
- No obvious errors in code

## Code Style Guidelines

### General Principles

- Write clean, readable code with clear intent
- Keep functions focused on a single responsibility
- Use meaningful variable and function names

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `DownloadManager`, `YTDLPDownloader`)
- **Functions/variables**: `snake_case` (e.g., `create_directory_name`, `ytdlp_path`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
- **Private methods**: Prefix with `_` (e.g., `_check_ytdlp`)

### Type Hints

Always use type hints for function parameters and return types:

```python
def process_download(
    link: str, 
    artist: str, 
    album: str, 
    base_dir: Optional[str] = None
) -> Tuple[bool, Optional[Dict], Optional[str]]:
```

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def sanitize_filename(name: str) -> str:
    """
    Sanitize a string for use as a filename/directory name.

    Args:
        name: String to sanitize

    Returns:
        Sanitized string safe for filesystem
    """
```

### Import Order

Organize imports in this order (separated by blank lines):

1. Standard library
2. Third-party libraries
3. Local application imports

```python
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

import subprocess

from core import DownloadManager
from logger import create_logger
from downloader import YTDLPDownloader
```

### Error Handling

- Use explicit exception types when possible
- Return `(success, data, error)` tuples for functions that can fail
- Catch exceptions at appropriate boundaries (e.g., don't let subprocess errors crash UI)

```python
# Good pattern
try:
    result = subprocess.run(...)
    if result.returncode != 0:
        return False, None, "Download failed"
    return True, result, None
except Exception as e:
    return False, None, str(e)
```

### Class Design

- Use abstract base classes (`ABC`) for extensible interfaces (see `logger.py`)
- Use factory functions for object creation (`create_logger()`)
- Keep related functionality grouped in classes

### GUI Development (PyQt5)

- Subclass `QThread` for background operations
- Use signals/slots for thread communication
- Initialize UI components in `init_ui()` method
- Handle errors gracefully with `QMessageBox`

### File Organization

- One module per logical concern (core, downloader, logger, gui)
- Keep the GUI in a separate module from business logic
- Use `__all__` to explicitly export public APIs if needed

### Patterns to Follow

- **Return tuples** for operations that can fail: `(success, data, error_message)`
- **Static methods** for pure utility functions
- **Private methods** (prefix `_`) for internal helpers
- **Property-based configuration** in classes with sensible defaults

### Styles

We should generally have no border radius

The border should be: border: 1px solid #242424.

For Green we use this colour: #548478

For buttons we may do this:    QPushButton {
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