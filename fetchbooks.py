import os
import requests
import json

# --- Configuration ---
# Hardcover API Endpoint
API_URL = "https://api.hardcover.app/v1/graphql"

# Read Token from GitHub Secrets securely
BEARER_TOKEN = 'hc_pat_EUgrUC2k8MPZsAsb6iwT2Xm4ZA63QV1PcHaxWvMcetXL'

OUTPUT_FILE = 'bookshelf.json'

HEADERS = {
    'Authorization': f'Bearer {BEARER_TOKEN}',
    'Content-Type': 'application/json',
    'User-Agent': 'GitHubPagesBookshelfScraper/1.0 (YourName/YourRepo)'
}

# Unified GraphQL query to fetch all books in your library
GRAPHQL_QUERY = """
query GetUserLibrary {
  user_books(order_by: { updated_at: desc }) {
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

def generate_bookshelf_json():
    if not BEARER_TOKEN:
        print("[Error] HARDCOVER_TOKEN environment variable is missing.")
        return

    payload = {"query": GRAPHQL_QUERY}
    
    try:
        print("Fetching library data from Hardcover API...")
        response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Error] Failed to connect to Hardcover: {e}")
        return

    # Check for GraphQL structural errors
    if "errors" in data:
        print(f"[Error] GraphQL syntax error: {data['errors']}")
        return

    user_books = data.get("data", {}).get("user_books", [])
    print(f"Retrieved {len(user_books)} library entries.")

    # Rebuilding your original target JSON schema
    all_books_data = {
        'currentlyReading': [],
        'readBooksByYear': {}
    }

    for item in user_books:
        status_id = item.get("status_id")
        book_obj = item.get("book") or {}
        
        # Format core variables to match your original Goodreads layout structure
        title = book_obj.get("title", "N/A")
        
        # Parse out authors from Hardcover contribution arrays
        contributions = book_obj.get("contributions", [])
        author = contributions[0].get("author", {}).get("name", "N/A") if contributions else "N/A"
        
        link = f"https://hardcover.app{book_obj.get('slug', '')}" if book_obj.get('slug') else "#"
        image_url = (book_obj.get("image") or {}).get("url", "")
        
        # Hardcover stores specific reading iterations here
        reads = item.get("user_book_reads", [])
        read_at = reads[0].get("started_at") if reads else item.get("date_added")
        
        # Map values safely into your schema format
        book_payload = {
            'title': title,
            'author': author,
            'link': link,
            'imageUrl': image_url,
            'shelves': [], # Handled dynamically below
            'readAt': read_at
        }

        # Status Mapping: 2 = Currently Reading, 3 = Read
        if status_id == 2:
            book_payload['shelves'] = ['currently-reading']
            all_books_data['currentlyReading'].append(book_payload)
            
        elif status_id == 3:
            # Safely extract the read year format out of timestamps like '2024-05-12...'
            if read_at:
                year_str = str(read_at[:4])
                book_payload['shelves'] = [year_str]
                
                if year_str not in all_books_data['readBooksByYear']:
                    all_books_data['readBooksByYear'][year_str] = []
                all_books_data['readBooksByYear'][year_str].append(book_payload)

    # Output structural write
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_books_data, f, indent=2, ensure_ascii=False)
        print(f"Success! Rebuilt {OUTPUT_FILE} using your custom Hardcover pipeline.")
    except IOError as e:
        print(f"Error writing output array to file: {e}")

if __name__ == "__main__":
    generate_bookshelf_json()
