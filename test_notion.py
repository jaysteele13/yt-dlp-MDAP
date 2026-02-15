import requests
notion_api = 'given-key'

# Step 1: Search for databases
search_url = "https://api.notion.com/v1/search"
search_payload = {
    "filter": {
        "property": "object",
        "value": "database"
    }
}
search_headers = {
    "Notion-Version": "2022-06-28",
    "Authorization": f"Bearer {notion_api}",
    "Content-Type": "application/json"
}

search_response = requests.post(search_url, json=search_payload, headers=search_headers)
databases = search_response.json()

# Print all databases to find the one you want
print("Available databases:")
for db in databases.get("results", []):
    title = db.get("title", [{}])[0].get("plain_text", "Untitled")
    db_id = db.get("id")
    print(f"  - {title}: {db_id}")

# Step 2: Select the database
if databases.get("results"):
    database_id = databases["results"][0]["id"]
    
    if database_id:
        # Step 3: Create a new page (row) in the database
        create_url = "https://api.notion.com/v1/pages"
        create_payload = {
            "parent": {
                "database_id": database_id
            },
            "properties": {
                "Album Name": {
                    "title": [
                        {
                            "text": {
                                "content": "Abbey Road"
                            }
                        }
                    ]
                },
                "Artist Name": {
                    "rich_text": [
                        {
                            "text": {
                                "content": "The Beatles"
                            }
                        }
                    ]
                },
                "URL": {
                    "url": "https://open.spotify.com/album/example"
                }
            }
        }
        
        create_response = requests.post(create_url, json=create_payload, headers=search_headers)
        print("\nNew entry created:")
        print(create_response.json())
    else:
        print("Database not found!")
else:
    print("No databases found!")


    ## Test Connection
    # Test 1: Search for databases (read-only)
search_url = "https://api.notion.com/v1/search"
search_payload = {
    "filter": {
        "property": "object",
        "value": "database"
    }
}
search_headers = {
    "Notion-Version": "2022-06-28",
    "Authorization": f"Bearer {notion_api}",
    "Content-Type": "application/json"
}

print("Testing connection...")
search_response = requests.post(search_url, json=search_payload, headers=search_headers)

if search_response.status_code == 200:
    print("✓ Connection successful!")
    databases = search_response.json()
    
    print(f"\nFound {len(databases.get('results', []))} database(s):")
    for db in databases.get("results", []):
        title = db.get("title", [{}])[0].get("plain_text", "Untitled")
        db_id = db.get("id")
        print(f"  - {title}: {db_id}")
        
        # Test 2: Retrieve specific database details (read-only)
        db_url = f"https://api.notion.com/v1/databases/{db_id}"
        db_response = requests.get(db_url, headers=search_headers)
        
        if db_response.status_code == 200:
            db_data = db_response.json()
            print(f"\n    Properties in '{title}':")
            for prop_name, prop_data in db_data.get("properties", {}).items():
                prop_type = prop_data.get("type")
                print(f"      - {prop_name} ({prop_type})")
else:
    print(f"✗ Connection failed!")
    print(f"Status code: {search_response.status_code}")
    print(f"Error: {search_response.text}")

