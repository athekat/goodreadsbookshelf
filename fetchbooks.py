import os
import requests
import json
import time

# --- Configuration ---
API_URL = "https://api.hardcover.app/v1/graphql"
BEARER_TOKEN = 'hc_pat_EUgrUC2k8MPZsAsb6iwT2Xm4ZA63QV1PcHaxWvMcetXL'
OUTPUT_FILE = 'bookshelf.json'

if not BEARER_TOKEN:
    print("[Error] HARDCOVER_TOKEN environment variable is missing.")
    exit(1)

HEADERS = {
    'Authorization': f'Bearer {BEARER_TOKEN}',
    'Content-Type': 'application/json',
    'User-Agent': 'GitHubPagesBookshelfScraper/1.0'
}

# Paginated GraphQL query using limit and offset
GRAPHQL_QUERY = """
query GetUserLibrary($limit: Int!, $offset: Int!) {
  user_books(order_by: { updated_at: desc }, limit: $limit, offset: $offset) {
    status_id
    rating
    date_added
    book {
      title
      slug
      image {
        url
      }
      contributions {
        author {
          name
        }
      }
    }
    user_book_reads {
      id
      started_at
    }
  }
}
"""

def fetch_all_user_books():
    """Pages through the user's library safely to avoid API timeouts."""
    all_entries = []
    limit = 50
    offset = 0
    
    while True:
        print(f"Fetching books {offset} to {offset + limit}...")
        payload = {
            "query": GRAPHQL_QUERY,
            "variables": {
                "limit": limit,
                "offset": offset
            }
        }
        
        try:
            # 30 seconds is the maximum allowed timeout for Hardcover API
            response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"[Error] Network issue or timeout at offset {offset}: {e}")
            break

        if "errors" in data:
            print(f"[Error] GraphQL syntax error: {data['errors']}")
            break

        user_books = data.get("data", {}).get("user_books", [])
        if not user_books:
            # No more books left to fetch
            break
            
        all_entries.extend(user_books)
        offset += limit
        
        # Micro-pause to be nice to Hardcover's beta servers
        time.sleep(0.5)
        
    return all_entries

def generate_bookshelf_json():
    user_books = fetch_all_user_books()
    print(f"\nTotal entries retrieved: {len(user_books)}")

    if not user_books:
        print("[Warning] No data collected. Output file will not be updated.")
        return

    # Rebuilding your original target JSON schema
    all_books_data = {
        'currentlyReading': [],
        'readBooksByYear': {}
    }

    for item in user_books:
        status_id = item.get("status_id")
        book_obj = item.get("book") or {}
        
        title = book_obj.get("title", "N/A")
        link = f"https://hardcover.app{book_obj.get('slug', '')}" if book_obj.get('slug') else "#"
        image_url = (book_obj.get("image") or {}).get("url", "")
        
        # Safely parse authors from Hardcover's contribution array
        contributions = book_obj.get("contributions", [])
        if contributions and isinstance(contributions, list):
            author = contributions[0].get("author", {}).get("name", "N/A")
        else:
            author = "N/A"
        
        reads = item.get("user_book_reads", [])
        read_at = reads[0].get("started_at") if reads and isinstance(reads, list) else item.get("date_added")
        
        book_payload = {
            'title': title,
            'author': author,
            'link': link,
            'imageUrl': image_url,
            'shelves': [],
            'readAt': read_at
        }

        # Status Mapping: 2 = Currently Reading, 3 = Read
        if status_id == 2:
            book_payload['shelves'] = ['currently-reading']
            all_books_data['currentlyReading'].append(book_payload)
            
        elif status_id == 3:
            if read_at:
                year_str = str(read_at[:4])
                book_payload['shelves'] = [year_str]
                
                if year_str not in all_books_data['readBooksByYear']:
                    all_books_data['readBooksByYear'][year_str] = []
                all_books_data['readBooksByYear'][year_str].append(book_payload)

    # Save to your static file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_books_data, f, indent=2, ensure_ascii=False)
        print(f"Success! Rebuilt {OUTPUT_FILE} using paginated Hardcover data pipeline.")
    except IOError as e:
        print(f"Error writing output array to file: {e}")

if __name__ == "__main__":
    generate_bookshelf_json()
