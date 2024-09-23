import requests
from bs4 import BeautifulSoup
import time
import random
import csv

#IBM modules
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 \
    import Features, EntitiesOptions
    
#os for dotenv
import os
from dotenv import load_dotenv

#clean data modules
import re
from datetime import datetime

def scrape_ltt_forum(url, pages=1):
    all_threads = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', # Just in case it is not always HTML. 
        'Accept-Language': 'en-US,en;q=0.5', #English US or any type of english
        'Referer': 'https://linustechtips.com/',
        'DNT': '1', # Do not track usage.
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
        
        time.sleep(random.uniform(2, 5))  # Random delay between requests. Please do not change it.
    
    return all_threads

def clean_data(threads):
    clean_threads = []
    for thread in threads:
        # Clean title, url, author. Whitespaces (unnecesary ones) removed with regex and strip.
        clean_title = re.sub(r'\s+', ' ', thread['title']).strip()
        clean_url = thread['url'].strip()
        clean_author = re.sub(r'\s+', ' ', thread['author']).strip()
        
        # Clean and standardize date
        try:
            date_obj = datetime.fromisoformat(thread['date'].replace('Z', '+00:00'))
            clean_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            clean_date = thread['date']  # Keep original if parsing fails
        
        clean_threads.append({
            'title': clean_title,
            'url': clean_url,
            'author': clean_author,
            'date': clean_date
        })
    
    return clean_threads

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
    
    cleaned_threads = clean_data(threads)
    
    # Save scraped data as CSV
    scraped_file = os.path.join(output_dir, 'scraped_threads.csv')
    with open(scraped_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'url', 'author', 'date'])
        writer.writeheader()
        writer.writerows(cleaned_threads)
    
    print(f"\nTotal threads scraped: {len(cleaned_threads)}")
    print(f"Scraped data saved to {scraped_file}")

    # Set up IBM Watson NLU
    load_dotenv()
    authenticator = IAMAuthenticator(os.getenv('API_KEY'))
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        version='2022-04-07',
        authenticator=authenticator
    )
    natural_language_understanding.set_service_url(os.getenv('SERVICE_URL'))

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
                        entity.get('confidence', 'N/A'), #Checking for no confidence.
                        entity['sentiment']['score']
                    ])
            except Exception as e:
                print(f"Error analyzing title: {thread['title']}")
                print(f"Error message: {str(e)}")

    print(f"Entity analysis completed and saved to {entity_file}")

if __name__ == "__main__":
    main()