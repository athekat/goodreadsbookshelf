import requests
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime # Keep imports from previous script

# --- Configuration ---
GOODREADS_USER_ID = '39570859' # Replace with your actual Goodreads User ID

CURRENTLY_READING_SHELF_RSS_URL = f'https://www.goodreads.com/review/list_rss/{GOODREADS_USER_ID}?shelf=currently-reading'
# Define the years you want to fetch. Adjust as needed.
# This assumes you have shelves named '2022', '2023', etc.
YEARS_TO_FETCH = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025] # Add or remove years as per your data

OUTPUT_FILE = 'bookshelf.json' # Path where the JSON will be saved

# --- Helper Functions ---

# Add a global header variable
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    # You can try other common user agents too.
    # Example: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'
}

def fetch_and_parse_feed(url):
    """Fetches an RSS feed and parses its XML content."""
    print(f"Fetching: {url}")
    try:
        # Pass the headers with your request
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return ET.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch feed from URL: {url} - {e}")
        # print(f"Response content (if available): {response.text}") # Uncomment for debugging response content
        return None
    except ET.ParseError as e:
        print(f"Failed to parse XML from URL: {url} - {e}")
        return None

def extract_book_data(item_element):
    """Extracts relevant book data from an XML <item> element."""
    try:
        title = item_element.find('title').text if item_element.find('title') is not None else 'N/A'
        author = item_element.find('author_name').text if item_element.find('author_name') is not None else 'N/A'
        link = item_element.find('link').text if item_element.find('link') is not None else '#'
        image_url = item_element.find('book_small_image_url').text if item_element.find('book_small_image_url') is not None else ''
        # Goodreads RSS description often contains additional structured data as text
        description_full_html = item_element.find('description').text if item_element.find('description') is not None else ''

        # Extract shelves using regex
        shelves_match = re.search(r'shelves: ([\w,\s-]+)', description_full_html)
        shelves = [s.strip() for s in shelves_match.group(1).split(',')] if shelves_match else []

        # Extract 'read at' date using regex
        read_at_match = re.search(r'read at: (\d{4}/\d{2}/\d{2})', description_full_html)
        read_at = read_at_match.group(1) if read_at_match else None

        return {
            'title': title,
            'author': author,
            'link': link,
            'imageUrl': image_url,
            'shelves': shelves,
            'readAt': read_at,
            # Note: The full book description HTML might be large, consider if you need it:
            # 'descriptionHtml': description_full_html
        }
    except Exception as e:
        print(f"Warning: Could not fully extract data for an item. Error: {e}")
        # print(f"Problematic item XML: {ET.tostring(item_element, encoding='unicode')}") # Uncomment for deeper debugging
        return None

# --- Main Logic ---

def generate_bookshelf_json():
    all_books_data = {
        'currentlyReading': [],
        'readBooksByYear': {}
    }

    # 1. Fetch Currently Reading books
    currently_reading_root = fetch_and_parse_feed(CURRENTLY_READING_SHELF_RSS_URL)
    if currently_reading_root:
        # Navigate to <channel><item> elements
        for item in currently_reading_root.findall('.//item'):
            book = extract_book_data(item)
            if book:
                all_books_data['currentlyReading'].append(book)

    # 2. Fetch Read books from specific year shelves
    for year in YEARS_TO_FETCH:
        year_specific_url = f'https://www.goodreads.com/review/list_rss/{GOODREADS_USER_ID}?shelf={year}'
        year_root = fetch_and_parse_feed(year_specific_url)
        if year_root:
            # Navigate to <channel><item> elements
            for item in year_root.findall('.//item'):
                book = extract_book_data(item)
                if book:
                    if year not in all_books_data['readBooksByYear']:
                        all_books_data['readBooksByYear'][year] = []
                    all_books_data['readBooksByYear'][year].append(book)

    # Sort read books within each year by read date (if available) or title
    for year in all_books_data['readBooksByYear']:
        all_books_data['readBooksByYear'][year].sort(key=lambda x: (x['readAt'] is None, x['readAt'] if x['readAt'] else x['title']), reverse=True)

    # Write the combined data to a JSON file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_books_data, f, indent=2, ensure_ascii=False)
        print(f"\nBookshelf data successfully saved to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error writing JSON file: {e}")

if __name__ == "__main__":
    generate_bookshelf_json()