"""
notion_logger.py - Notion API logger implementation

To use this:
1. Install notion-client: pip install notion-client --break-system-packages
2. Get your Notion API key from https://www.notion.so/my-integrations
3. Create a database in Notion with these properties:
   - Timestamp (Date)
   - Artist (Text or Title)
   - Album (Text)
   - Link (URL)
   - Directory (Text)
4. Share the database with your integration
5. Get the database ID from the URL
"""

from typing import Dict, List, Optional
from datetime import datetime

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

from logger import Logger


class NotionLogger(Logger):
    """Logger that writes to a Notion database"""
    
    def __init__(self, api_key: str, database_id: str):
        """
        Initialize Notion logger
        
        Args:
            api_key: Notion integration API key
            database_id: ID of the Notion database to write to
        """
        if not NOTION_AVAILABLE:
            raise ImportError(
                "notion-client not installed. "
                "Install with: pip install notion-client --break-system-packages"
            )
        
        self.client = Client(auth=api_key)
        self.database_id = database_id
        
        # Verify connection
        try:
            self.client.databases.retrieve(database_id=self.database_id)
        except Exception as e:
            raise ValueError(f"Failed to connect to Notion database: {e}")
    
    def log(self, entry: Dict) -> bool:
        """
        Log entry to Notion database
        
        Args:
            entry: Download entry dictionary from core.py
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse timestamp
            timestamp = entry.get('timestamp', datetime.now().isoformat())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            # Create page properties
            properties = {
                "Artist": {
                    "title": [
                        {
                            "text": {
                                "content": entry.get('artist', 'Unknown')
                            }
                        }
                    ]
                },
                "Album": {
                    "rich_text": [
                        {
                            "text": {
                                "content": entry.get('album', 'Unknown')
                            }
                        }
                    ]
                },
                "Link": {
                    "url": entry.get('link', '')
                },
                "Directory": {
                    "rich_text": [
                        {
                            "text": {
                                "content": entry.get('directory', '')
                            }
                        }
                    ]
                },
                "Timestamp": {
                    "date": {
                        "start": timestamp.isoformat()
                    }
                }
            }
            
            # Create the page
            self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            return True
            
        except Exception as e:
            print(f"Notion logging failed: {e}")
            return False
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get download history from Notion database
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of download entry dictionaries
        """
        try:
            # Query the database
            query_params = {
                "database_id": self.database_id,
                "sorts": [
                    {
                        "timestamp": "Timestamp",
                        "direction": "descending"
                    }
                ]
            }
            
            if limit:
                query_params["page_size"] = limit
            
            results = self.client.databases.query(**query_params)
            
            # Parse results
            entries = []
            for page in results.get("results", []):
                props = page.get("properties", {})
                
                entry = {
                    'timestamp': self._get_date(props.get("Timestamp")),
                    'artist': self._get_text(props.get("Artist")),
                    'album': self._get_text(props.get("Album")),
                    'link': self._get_url(props.get("Link")),
                    'directory': self._get_text(props.get("Directory"))
                }
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            print(f"Failed to retrieve history: {e}")
            return []
    
    def _get_text(self, prop) -> str:
        """Extract text from Notion property"""
        if not prop:
            return ""
        
        prop_type = prop.get("type")
        if prop_type == "title":
            items = prop.get("title", [])
        elif prop_type == "rich_text":
            items = prop.get("rich_text", [])
        else:
            return ""
        
        if items:
            return items[0].get("text", {}).get("content", "")
        return ""
    
    def _get_url(self, prop) -> str:
        """Extract URL from Notion property"""
        if not prop:
            return ""
        return prop.get("url", "")
    
    def _get_date(self, prop) -> str:
        """Extract date from Notion property"""
        if not prop:
            return ""
        date_obj = prop.get("date")
        if date_obj:
            return date_obj.get("start", "")
        return ""


# Example usage
if __name__ == "__main__":
    # Configuration
    API_KEY = "your_notion_api_key_here"
    DATABASE_ID = "your_database_id_here"
    
    # Create logger
    try:
        logger = NotionLogger(API_KEY, DATABASE_ID)
        
        # Test log entry
        test_entry = {
            'timestamp': datetime.now().isoformat(),
            'artist': 'Test Artist',
            'album': 'Test Album',
            'link': 'https://youtube.com/watch?v=test',
            'directory': '/home/user/Music/Test Artist - Test Album'
        }
        
        success = logger.log(test_entry)
        print(f"Log success: {success}")
        
        # Get history
        history = logger.get_history(limit=5)
        print(f"Recent entries: {len(history)}")
        for entry in history:
            print(f"  - {entry['artist']} - {entry['album']}")
            
    except Exception as e:
        print(f"Error: {e}")