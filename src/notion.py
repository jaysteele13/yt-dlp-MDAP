"""
notion.py - Notion API integration for MDAP.

Provides functions for interacting with Notion API including:
- Configuration management
- Database entry creation
- Connection testing
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List

logger = logging.getLogger(__name__)

CONFIG_FILE = Path.home() / ".mdap" / "notion_config.json"

NOTION_API_KEY: Optional[str] = None
NOTION_DATABASE_ID: Optional[str] = None


def load_notion_config() -> Dict[str, Any]:
    """
    Load Notion configuration from the config file.
    
    Returns:
        Dictionary containing configuration values
    """
    config = {}
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded Notion configuration from {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    
    return config


def save_notion_config(config: Dict[str, Any]) -> bool:
    """
    Save Notion configuration to the config file.
    
    Args:
        config: Dictionary containing configuration to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration saved to {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False


def get_notion_api_key() -> Optional[str]:
    """
    Get the Notion API key from configuration.
    
    Returns:
        API key string or None if not configured
    """
    global NOTION_API_KEY
    
    config = load_notion_config()
    
    NOTION_API_KEY = config.get("internal_secret") or config.get("NOTION_API_KEY")
    
    if NOTION_API_KEY:
        logger.info(f"NOTION_API_KEY loaded from config: {NOTION_API_KEY[:20]}...")
    else:
        logger.debug("NOTION_API_KEY not found in config")
    
    return NOTION_API_KEY


def refresh_config():
    """Force reload of configuration from file."""
    global NOTION_API_KEY, NOTION_DATABASE_ID
    NOTION_API_KEY = None
    NOTION_DATABASE_ID = None
    get_notion_api_key()
    get_database_id()
    logger.debug("Configuration refreshed from file")


def get_database_id() -> Optional[str]:
    """
    Get the Notion database ID from configuration.
    
    Returns:
        Database ID string or None if not configured
    """
    global NOTION_DATABASE_ID
    
    config = load_notion_config()
    NOTION_DATABASE_ID = config.get("database_id")
    
    if NOTION_DATABASE_ID:
        logger.debug("NOTION_DATABASE_ID loaded from config")
    
    return NOTION_DATABASE_ID


def is_notion_configured() -> bool:
    """
    Check if Notion API is properly configured.
    
    Returns:
        True if API key is available, False otherwise
    """
    api_key = get_notion_api_key()
    return api_key is not None and api_key != ""


def check_notion_api_configured() -> Tuple[bool, Optional[str]]:
    """
    Check if notion_api is set before proceeding.
    
    Returns:
        Tuple of (is_configured, error_message)
    """
    if not is_notion_configured():
        return False, "Notion API is not configured. Please set up your Internal Integration Secret in the Notion settings."
    
    return True, None


def test_notion_connection(api_key: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[list]]:
    """
    Test the Notion API connection.
    
    Args:
        api_key: Optional API key to test. If not provided, will load from config.
        
    Returns:
        Tuple of (success, error_message, list of available databases)
    """
    import requests
    
    if api_key is None:
        api_key = get_notion_api_key()
    
    if not api_key:
        return False, "API key not configured", None
    
    search_url = "https://api.notion.com/v1/search"
    search_payload = {
        "filter": {
            "property": "object",
            "value": "database"
        }
    }
    search_headers = {
        "Notion-Version": "2022-06-28",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(search_url, json=search_payload, headers=search_headers, timeout=10)
        
        if response.status_code == 200:
            databases = response.json()
            db_list = []
            for db in databases.get("results", []):
                title = db.get("title", [{}])[0].get("plain_text", "Untitled")
                db_id = db.get("id")
                db_list.append({"title": title, "id": db_id})
            
            return True, None, db_list
        else:
            error_msg = f"Status code: {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get("message", error_msg)
            except:
                pass
            return False, error_msg, None
            
    except requests.exceptions.Timeout:
        return False, "Connection timed out", None
    except requests.exceptions.RequestException as e:
        return False, f"Connection failed: {str(e)}", None
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", None


def create_database_entry(
    artist_name: str,
    album_name: str,
    url: str,
    song_count: int = 0,
    api_key: Optional[str] = None,
    database_id: Optional[str] = None
) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Create a new entry in the Notion database.
    
    Args:
        artist_name: Name of the artist
        album_name: Name of the album
        url: URL to the source (e.g., YouTube link)
        song_count: Number of songs in the album
        api_key: Optional API key. If not provided, will load from config.
        database_id: Optional database ID. If not provided, will load from config.
        
    Returns:
        Tuple of (success, response_data, error_message)
    """
    import requests
    from datetime import datetime
    
    if api_key is None:
        api_key = get_notion_api_key()
    
    if database_id is None:
        database_id = get_database_id()
    
    if not api_key:
        return False, None, "API key not configured"
    
    if not database_id:
        return False, None, "Database ID not configured"
    
    logger.info(f"Creating Notion entry - API key present: {bool(api_key)}, key: {api_key[:20] if api_key else 'None'}..., Database ID: {database_id}")
    
    create_url = "https://api.notion.com/v1/pages"
    
    properties = {}
    
    if album_name:
        properties["Album Name"] = {
            "title": [
                {
                    "text": {
                        "content": album_name
                    }
                }
            ]
        }
    
    if artist_name:
        properties["Artist Name"] = {
            "rich_text": [
                {
                    "text": {
                        "content": artist_name
                    }
                }
            ]
        }
    
    if url:
        properties["URL"] = {
            "url": url
        }
    
    properties["Date"] = {
        "date": {
            "start": datetime.now().isoformat()
        }
    }
    
    if song_count > 0:
        properties["Song Count"] = {
            "number": song_count
        }
    
    create_payload = {
        "parent": {
            "database_id": database_id
        },
        "properties": properties
    }
    
    headers = {
        "Notion-Version": "2022-06-28",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(create_url, json=create_payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, response.json(), None
        else:
            error_msg = f"Status code: {response.status_code}"
            error_data = None
            try:
                error_data = response.json()
                error_msg = error_data.get("message", error_msg)
            except:
                pass
            logger.error(f"Notion API error: status={response.status_code}, response={error_data}")
            return False, None, error_msg
            
    except requests.exceptions.Timeout:
        return False, None, "Request timed out"
    except requests.exceptions.RequestException as e:
        return False, None, f"Request failed: {str(e)}"
    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"


def get_recent_entries(
    limit: int = 5,
    api_key: Optional[str] = None,
    database_id: Optional[str] = None
) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
    """
    Get recent entries from the Notion database.
    
    Args:
        limit: Maximum number of entries to return
        api_key: Optional API key. If not provided, will load from config.
        database_id: Optional database ID. If not provided, will load from config.
        
    Returns:
        Tuple of (success, list of entries, error_message)
    """
    import requests
    
    if api_key is None:
        api_key = get_notion_api_key()
    
    if database_id is None:
        database_id = get_database_id()
    
    if not api_key:
        return False, None, "API key not configured"
    
    if not database_id:
        return False, None, "Database ID not configured"
    
    query_url = f"https://api.notion.com/v1/databases/{database_id}/query"
    
    query_payload = {
        "page_size": limit,
        "sorts": [
            {
                "timestamp": "created_time",
                "direction": "descending"
            }
        ]
    }
    
    headers = {
        "Notion-Version": "2022-06-28",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(query_url, json=query_payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            
            entries = []
            for page in results:
                properties = page.get("properties", {})
                
                album_name = ""
                if "Album Name" in properties:
                    title_list = properties["Album Name"].get("title", [])
                    if title_list:
                        album_name = title_list[0].get("plain_text", "")
                
                artist_name = ""
                if "Artist Name" in properties:
                    rich_text = properties["Artist Name"].get("rich_text", [])
                    if rich_text:
                        artist_name = rich_text[0].get("plain_text", "")
                
                song_count = 0
                if "Song Count" in properties:
                    song_count = properties["Song Count"].get("number", 0)
                
                date_str = ""
                if "Date" in properties:
                    date_val = properties["Date"].get("date", {})
                    if date_val:
                        date_str = date_val.get("start", "")
                
                url = ""
                if "URL" in properties:
                    url = properties["URL"].get("url", "")
                
                entries.append({
                    "album": album_name,
                    "artist": artist_name,
                    "song_count": song_count,
                    "date": date_str,
                    "url": url,
                    "id": page.get("id")
                })
            
            return True, entries, None
        else:
            error_msg = f"Status code: {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get("message", error_msg)
            except:
                pass
            return False, None, error_msg
            
    except requests.exceptions.Timeout:
        return False, None, "Request timed out"
    except requests.exceptions.RequestException as e:
        return False, None, f"Request failed: {str(e)}"
    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"
