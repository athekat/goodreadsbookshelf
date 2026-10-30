import os
import requests
import json

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

# The query must be nested inside 'me' so Hardcover limits the lookup to your library
GRAPHQL_QUERY = """
query GetUserLibrary {
  me {
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
}
"""

def generate_bookshelf_json():
    payload = {"query": GRAPHQL_QUERY}
    
    try:
        print("Fetching library data securely from Hardcover API...")
        response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Error] Failed to connect to Hardcover: {e}")
        return

    if "errors" in data:
        print(f"[Error] GraphQL syntax error: {data['errors']}")
        return

    # Extract data out of the new 'me' root wrapper safely
    me_data = data.get("data", {}).get("me", [])
    if not me_data:
        print("[Error] Could not resolve 'me' profile. Verify your API token is valid.")
        return
        
    user_books = me_data[0].get("user_books", []) if isinstance(me_data, list) and me_data else me_data.get("user_books", [])
    print(f"Successfully retrieved {len(user_books)} library entries.")

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
        
        # Safely parse structural author fields from list blocks
        contributions = book_obj.get("contributions", [])
        author = "N/A"
        if contributions and isinstance(contributions, list):
            first_contribution = contributions[0]
            if isinstance(first_contribution, dict):
                author = first_contribution.get("author", {}).get("name", "N/A")

        reads = item.get("user_book_reads", [])
        read_at = None
        if reads and isinstance(reads, list):
            read_at = reads[0].get("started_at")
        
        if not read_at:
            read_at = item.get("date_added")
        
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

    # Save to file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_books_data, f, indent=2, ensure_ascii=False)
        print(f"Bookshelf data successfully migrated and saved to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error writing JSON file: {e}")

if __name__ == "__main__":
    generate_bookshelf_json()
