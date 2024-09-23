import requests
from bs4 import BeautifulSoup
import time
import random
import csv
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 \
    import Features, EntitiesOptions

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
    
    for page in range(1, pages + 1): #For each page, get the page URL, access it and get threads.
        page_url = f"{url}?page={page}"
        try:
            response = session.get(page_url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to retrieve page {page}. Error: {e}")
            continue
        
        print(f"Retrieved page {page}. Status code: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        threads = soup.select('li.ipsDataItem')
        
        for thread in threads:
            title_elem = thread.select_one('a') #Title
            author_elem = thread.select_one('.ipsDataItem_meta a') #Author tag
            date_elem = thread.select_one('time')
            
            if title_elem and author_elem and date_elem:
                thread_data = {
                    'title': title_elem.text.strip(),
                    'url': 'https://linustechtips.com' + title_elem['href'],
                    'author': author_elem.text.strip(),
                    'date': date_elem['datetime']
                }
                all_threads.append(thread_data)
                
                
            #---------
            #Checks
            # else:
            #     print("Missing elements in thread:")
            #     print(f"  Title element found: {title_elem is not None}")
            #     print(f"  Author element found: {author_elem is not None}")
            #     print(f"  Date element found: {date_elem is not None}")
            #print(f"Scraped {len(all_threads)} threads from page {page}")
            #---------
        
        time.sleep(random.uniform(2, 5))  # Random delay between requests
    
    return all_threads

import csv
import json
import os
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EntitiesOptions

def main():
    url = "https://linustechtips.com/forum/13-tech-news/"
    
    # User input for number of pages to scrape
    while True:
        try:
            pages = int(input("Enter the number of pages to scrape: "))
            if pages > 0:
                break
            else:
                print("Please enter a positive integer.")
        except ValueError:
            print("Invalid input. Please enter a positive integer.")
    
    # User input for output directory
    output_dir = input("Enter the output directory path (leave blank for current directory): ").strip()
    if not output_dir:
        output_dir = '.'
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    threads = scrape_ltt_forum(url, pages=pages)
    
    # Save scraped data as CSV
    scraped_file = os.path.join(output_dir, 'scraped_threads.csv')
    with open(scraped_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'url', 'author', 'date'])
        writer.writeheader()
        writer.writerows(threads)
    
    print(f"\nTotal threads scraped: {len(threads)}")
    print(f"Scraped data saved to {scraped_file}")

    # Set up IBM Watson NLU
    authenticator = IAMAuthenticator('UVPe694_HOJgsU4Gq0mWhTgXppC9i1LsMXUfaJu_tWLY')
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        version='2022-04-07',
        authenticator=authenticator
    )
    natural_language_understanding.set_service_url('https://api.us-east.natural-language-understanding.watson.cloud.ibm.com/instances/c33e95c2-226e-4c7d-90ad-422e73786ba0')

    # Analyze titles for entities and save results as CSV
    entity_file = os.path.join(output_dir, 'entity_analysis.csv')
    with open(entity_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'URL', 'Entity', 'Type', 'Confidence', 'Sentiment Score'])

        for thread in threads:
            try:
                response = natural_language_understanding.analyze(
                    text=thread['title'],
                    features=Features(entities=EntitiesOptions(sentiment=True, limit=5))
                ).get_result()
                
                for entity in response['entities']:
                    writer.writerow([
                        thread['title'],
                        thread['url'],
                        entity['text'],
                        entity['type'],
                        entity.get('confidence', 'N/A'),
                        entity['sentiment']['score']
                    ])
            except Exception as e:
                print(f"Error analyzing title: {thread['title']}")
                print(f"Error message: {str(e)}")

    print(f"Entity analysis completed and saved to {entity_file}")

if __name__ == "__main__":
    main()