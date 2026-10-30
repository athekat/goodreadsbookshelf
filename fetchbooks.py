import requests
from bs4 import BeautifulSoup
import json
import time

# --- Configuration ---
GOODREADS_USER_ID = '39570859' 
OUTPUT_FILE = 'bookshelf.json'

# Target the standard HTML list view, forcing 100 items per page
URL_TEMPLATE = f'https://goodreads.com{GOODREADS_USER_ID}?shelf={{shelf}}&per_page=100'

YEARS_TO_FETCH = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

def fetch_and_parse_shelf(shelf_name):
    """Fetches a Goodreads shelf HTML page and parses book elements."""
    url = URL_TEMPLATE.format(shelf=shelf_name)
    print(f"Fetching shelf: {shelf_name}...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  [Error] Failed to fetch shelf '{shelf_name}': {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Goodreads displays items as table rows with a 'review' class
    review_rows = soup.find_all('tr', class_='review')
    
    # Check if we were redirected or hit an empty block
    if not review_rows:
        print(f"  [Info] No books found or shelf is private on shelf: {shelf_name}")
        return []

    books = []
    for row in review_rows:
        try:
            # 1. Extract Title & Book URL
            title_td = row.find('td', class_='field title')
            title_a = title_td.find('div', class_='value').find('a') if title_td else None
            title = title_a.get_text(strip=True) if title_a else 'N/A'
            link = f"https://goodreads.com{title_a['href']}" if title_a else '#'

            # 2. Extract Author
            author_td = row.find('td', class_='field author')
            author_a = author_td.find('div', class_='value').find('a') if author_td else None
            author = author_a.get_text(strip=True) if author_a else 'N/A'

            # 3. Extract Image URL (Strip out the small thumb modifiers if possible)
            cover_td = row.find('td', class_='field cover')
            img_tag = cover_td.find('img') if cover_td else None
            image_url = img_tag['src'] if img_tag else ''
            # Clean Goodreads thumbnail strings to get higher res covers if desired
            image_url = image_url.replace('._SX50_', '').replace('._SY75_', '')

            # 4. Extract Date Read (Optional placeholder fallback)
            date_td = row.find('td', class_='field date_read')
            read_at = None
            if date_td:
                date_span = date_td.find('span', class_='date_read_value')
                if date_span:
                    read_at = date_span.get_text(strip=True)

            books.append({
                'title': title,
                'author': author,
                'link': link,
                'imageUrl': image_url,
                'shelves': [shelf_name],
                'readAt': read_at
            })
            
        except Exception as e:
            # Keep processing other books if one row fails to parse
            continue

    print(f"  [Success] Successfully parsed {len(books)} books.")
    return books

def generate_bookshelf_json():
    all_books_data = {
        'currentlyReading': [],
        'readBooksByYear': {}
    }

    # 1. Fetch Currently Reading books
    all_books_data['currentlyReading'] = fetch_and_parse_shelf('currently-reading')
    
    # Politeness delay after first request
    print("Waiting 3 seconds to stay under anti-bot limits...")
    time.sleep(3)

    # 2. Fetch Read books by year
    for year in YEARS_TO_FETCH:
        year_str = str(year)
        shelf_books = fetch_and_parse_shelf(year_str)
        
        if shelf_books:
            all_books_data['readBooksByYear'][year_str] = shelf_books
            
        # Politeness delay between yearly loop pages
        print("Waiting 3 seconds before next request...")
        time.sleep(3)

    # Write combined data to JSON
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_books_data, f, indent=2, ensure_ascii=False)
        print(f"\nBookshelf data successfully migrated and saved to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error writing JSON file: {e}")

if __name__ == "__main__":
    generate_bookshelf_json()
