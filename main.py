import requests
from bs4 import BeautifulSoup
import time
import random

def scrape_ltt_forum(url, pages=1):
    all_threads = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://linustechtips.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    session = requests.Session()
    
    for page in range(1, pages + 1):
        page_url = f"{url}?page={page}"
        try:
            response = session.get(page_url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to retrieve page {page}. Error: {e}")
            continue
        
        print(f"Retrieved page {page}. Status code: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if we're getting the expected content
        if "LINUS TECH TIPS" in soup.text:
            print("Received protective page. Attempting to bypass...")
            # Here you would implement logic to bypass the protection
            # This could involve solving a CAPTCHA, waiting, or using a different approach
            continue
        
        threads = soup.select('li.ipsDataItem')
        
        print(f"Found {len(threads)} thread elements on page {page}")
        
        for thread in threads:
            title_elem = thread.select_one('a')
            #print(title_elem)
            author_elem = thread.select_one('.ipsDataItem_meta a')
            date_elem = thread.select_one('time')
            
            if title_elem and author_elem and date_elem:
                thread_data = {
                    'title': title_elem.text.strip(),
                    'url': 'https://linustechtips.com' + title_elem['href'],
                    'author': author_elem.text.strip(),
                    'date': date_elem['datetime']
                }
                all_threads.append(thread_data)
            else:
                print("Missing elements in thread:")
                print(f"  Title element found: {title_elem is not None}")
                print(f"  Author element found: {author_elem is not None}")
                print(f"  Date element found: {date_elem is not None}")
        
        print(f"Scraped {len(all_threads)} threads from page {page}")
        time.sleep(random.uniform(2, 5))  # Random delay between requests
    
    return all_threads

def main():
    url = "https://linustechtips.com/forum/13-tech-news/"
    threads = scrape_ltt_forum(url, pages=3)  # Scrape 3 pages
    
    print(f"\nTotal threads scraped: {len(threads)}")
    for thread in threads:
        print(f"\nTitle: {thread['title']}")
        print(f"URL: {thread['url']}")
        print(f"Author: {thread['author']}")
        print(f"Date: {thread['date']}")
        print('----------------------------------')

if __name__ == "__main__":
    main()