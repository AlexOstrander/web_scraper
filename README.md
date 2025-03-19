- Web Scraper

- **Features:**

1. **Robust Error Handling**
- Retry mechanism with exponential backoff
- Comprehensive error logging
- Tracking of failed URLs

2. **Concurrent Scraping**
- Multiple URLs processed simultaneously
- Configurable number of concurrent requests
- Rate limiting to prevent overloading servers

3. **Data Extraction**
- HTML content
- Page title
- Meta tags
- Links
- Text content

4. **Output Formats**
- Raw HTML files
- Extracted text files
- JSON results
- CSV export
- Summary report
- Detailed logging

5. **Security Features**
- Rotating User-Agents
- Configurable delays between requests
- Request timeout handling

**Usage:**

1. **Install Dependencies:**
```bash
pip install requests beautifulsoup4 pandas fake-useragent
```

2. **Create URL List File:**
```text
https://example.com
https://python.org
https://github.com
```

3. **Run the Scraper:**
```bash
python scraper.py --urls urls.txt --output scraping_results
```

**Output Structure:**
```
scraping_results/
├── html/
│   └── (raw HTML files)
├── text/
│   └── (extracted text files)
├── data/
│   ├── results.json
│   ├── results.csv
│   ├── failed_urls.json
│   └── report.json
└── scraper.log
```

**Customization:**
- Adjust scraping settings in the `settings` dictionary
- Modify the data extraction in the `scrape_url` method
- Add custom parsing rules for specific websites
- Extend the output formats as needed

This scraper is suitable for both small and large-scale scraping tasks while maintaining good practices for responsible web scraping. 
