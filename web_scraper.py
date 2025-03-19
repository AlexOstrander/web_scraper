import requests
from bs4 import BeautifulSoup
import pandas as pd
import concurrent.futures
import logging
import time
from urllib.parse import urlparse
import os
from datetime import datetime
import json
from fake_useragent import UserAgent
import argparse

class WebScraper:
    def __init__(self, urls=None, output_dir="scraping_results"):
        """Initialize the scraper with configuration and setup."""
        self.urls = urls or []
        self.output_dir = output_dir
        self.results = []
        self.failed_urls = []
        self.setup_logging()
        self.setup_output_directory()
        
        # Configure headers with rotating User-Agents
        self.ua = UserAgent()
        self.session = requests.Session()
        
        # Default scraping settings
        self.settings = {
            'timeout': 30,
            'max_retries': 3,
            'delay_between_requests': 2,
            'concurrent_requests': 5
        }

    def setup_logging(self):
        """Configure logging system."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_output_directory(self):
        """Create output directory structure."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            os.makedirs(os.path.join(self.output_dir, 'html'))
            os.makedirs(os.path.join(self.output_dir, 'text'))
            os.makedirs(os.path.join(self.output_dir, 'data'))

    def get_random_headers(self):
        """Generate random headers for requests."""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def scrape_url(self, url):
        """Scrape a single URL with retry mechanism."""
        for attempt in range(self.settings['max_retries']):
            try:
                self.logger.info(f"Scraping URL: {url} (Attempt {attempt + 1})")
                
                response = self.session.get(
                    url,
                    headers=self.get_random_headers(),
                    timeout=self.settings['timeout']
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract basic information
                data = {
                    'url': url,
                    'title': soup.title.string if soup.title else 'No title',
                    'timestamp': datetime.now().isoformat(),
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'text_content': soup.get_text(strip=True),
                    'links': [a.get('href') for a in soup.find_all('a', href=True)],
                    'meta_tags': {
                        meta.get('name', meta.get('property', 'unknown')): meta.get('content')
                        for meta in soup.find_all('meta')
                    }
                }
                
                # Save raw HTML
                self.save_html(url, response.text)
                
                # Save extracted text
                self.save_text(url, data['text_content'])
                
                return data

            except requests.RequestException as e:
                self.logger.error(f"Error scraping {url}: {str(e)}")
                if attempt == self.settings['max_retries'] - 1:
                    self.failed_urls.append({'url': url, 'error': str(e)})
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff

    def save_html(self, url, html_content):
        """Save raw HTML content."""
        filename = self.get_safe_filename(url) + '.html'
        path = os.path.join(self.output_dir, 'html', filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def save_text(self, url, text_content):
        """Save extracted text content."""
        filename = self.get_safe_filename(url) + '.txt'
        path = os.path.join(self.output_dir, 'text', filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text_content)

    def get_safe_filename(self, url):
        """Convert URL to safe filename."""
        parsed = urlparse(url)
        return f"{parsed.netloc}_{hash(url)}"

    def scrape_all_urls(self):
        """Scrape multiple URLs concurrently."""
        start_time = time.time()
        self.logger.info(f"Starting scraping of {len(self.urls)} URLs")

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.settings['concurrent_requests']
        ) as executor:
            future_to_url = {
                executor.submit(self.scrape_url, url): url 
                for url in self.urls
            }

            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    if data:
                        self.results.append(data)
                        time.sleep(self.settings['delay_between_requests'])
                except Exception as e:
                    self.logger.error(f"Unexpected error for {url}: {str(e)}")
                    self.failed_urls.append({'url': url, 'error': str(e)})

        self.save_results()
        self.generate_report(start_time)

    def save_results(self):
        """Save scraping results in multiple formats."""
        # Save as JSON
        json_path = os.path.join(self.output_dir, 'data', 'results.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=4)

        # Save as CSV
        df = pd.DataFrame(self.results)
        csv_path = os.path.join(self.output_dir, 'data', 'results.csv')
        df.to_csv(csv_path, index=False)

        # Save failed URLs
        if self.failed_urls:
            failed_path = os.path.join(self.output_dir, 'data', 'failed_urls.json')
            with open(failed_path, 'w', encoding='utf-8') as f:
                json.dump(self.failed_urls, f, indent=4)

    def generate_report(self, start_time):
        """Generate a summary report of the scraping operation."""
        duration = time.time() - start_time
        report = {
            'total_urls': len(self.urls),
            'successful_scrapes': len(self.results),
            'failed_scrapes': len(self.failed_urls),
            'duration_seconds': round(duration, 2),
            'timestamp': datetime.now().isoformat()
        }

        report_path = os.path.join(self.output_dir, 'data', 'report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4)

        self.logger.info(f"Scraping completed. Summary:")
        self.logger.info(f"Total URLs: {report['total_urls']}")
        self.logger.info(f"Successful: {report['successful_scrapes']}")
        self.logger.info(f"Failed: {report['failed_scrapes']}")
        self.logger.info(f"Duration: {report['duration_seconds']} seconds")

def main():
    parser = argparse.ArgumentParser(description='Web Scraper')
    parser.add_argument('--urls', type=str, help='Path to file containing URLs')
    parser.add_argument('--output', type=str, default='scraping_results',
                      help='Output directory for results')
    args = parser.parse_args()

    # Read URLs from file
    if args.urls:
        with open(args.urls, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    else:
        # Example URLs for testing
        urls = [
            'https://example.com',
            'https://python.org',
            'https://github.com'
        ]

    # Initialize and run scraper
    scraper = WebScraper(urls=urls, output_dir=args.output)
    scraper.scrape_all_urls()

if __name__ == "__main__":
    main()
