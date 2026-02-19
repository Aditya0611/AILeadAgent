import requests
from typing import List, Dict
from config import DEFAULT_SEARCH_LIMIT, GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID

class SearchService:
    def __init__(self, api_key: str = None, search_engine_id: str = None):
        self.api_key = api_key or GOOGLE_API_KEY
        self.search_engine_id = search_engine_id or GOOGLE_SEARCH_ENGINE_ID
        
        if not self.api_key or not self.search_engine_id:
            print("⚠️  Warning: Google Custom Search API credentials not configured.")
            print("   Using placeholder search results.")
            self.use_placeholder = True
        else:
            self.use_placeholder = False

    def search_leads(self, query: str, limit: int = DEFAULT_SEARCH_LIMIT, start_index: int = 1) -> List[Dict]:
        """
        Searches for potential leads using Google Custom Search API.
        Falls back to placeholder data if API is not configured.
        """
        print(f"Searching for: {query} (Page starting at {start_index})")
        
        if self.use_placeholder:
            return self._placeholder_search()
        
        try:
            # Google Custom Search API endpoint
            url = "https://www.googleapis.com/customsearch/v1"
            
            results = []
            # Google API returns max 10 results per request
            num_results = min(limit, 10)
            
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': num_results,
                'start': start_index  # Google Search start index (1-based)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we have results
            if 'items' not in data:
                print(f"⚠️  No search results found for: {query}")
                return []
            
            # Parse results
            for item in data['items']:
                results.append({
                    'title': item.get('title', 'No Title'),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                })
            
            print(f"✅ Found {len(results)} results from Google Custom Search")
            return results
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("❌ Google API quota exceeded (100 searches/day limit)")
            else:
                print(f"❌ Google API error: {e}")
            print("   Falling back to placeholder search")
            return self._placeholder_search()
            
        except Exception as e:
            print(f"❌ Error searching with Google API: {e}")
            print("   Falling back to placeholder search")
            return self._placeholder_search()

    def _placeholder_search(self) -> List[Dict]:
        """Fallback placeholder search results"""
        return [
            {
                "title": "Salesforce - CRM SaaS Platform", 
                "link": "https://www.salesforce.com/", 
                "snippet": "Leading CRM and SaaS platform for sales and marketing teams in New York and worldwide..."
            },
            {
                "title": "HubSpot - Marketing SaaS", 
                "link": "https://www.hubspot.com/", 
                "snippet": "All-in-one marketing, sales, and service platform for growing businesses..."
            }
        ]

    def extract_page_content(self, url: str) -> str:
        """
        Extracts clean text content from a URL.
        Now includes:
        1. BeautifulSoup for cleaning HTML
        2. searching for 'Contact' pages if main page is sparse
        3. Email extraction via Regex
        """
        try:
            import re
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements for cleaner text
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
                
            text = soup.get_text(separator=' ', strip=True)
            
            # 1. basic extraction
            content = f"URL: {url}\n\nMain Page Content:\n{text[:5000]}\n"
            
            # 2. Look for explicit contact links if we need more info
            contact_link = None
            for a in soup.find_all('a', href=True):
                if 'contact' in a.text.lower() or 'about' in a.text.lower():
                    contact_link = urljoin(url, a['href'])
                    break
            
            # If found a contact page, fetch it too
            if contact_link:
                try:
                    print(f"   Found contact page: {contact_link}")
                    contact_resp = requests.get(contact_link, timeout=10, headers=headers)
                    if contact_resp.status_code == 200:
                        contact_soup = BeautifulSoup(contact_resp.text, 'html.parser')
                        for s in contact_soup(["script", "style"]):
                            s.decompose()
                        contact_text = contact_soup.get_text(separator=' ', strip=True)
                        content += f"\n\nContact Page Content:\n{contact_text[:3000]}"
                except Exception as e:
                    print(f"   Could not fetch contact page: {e}")

            # 3. Regex extraction for Emails (add to content so AI sees it clearly)
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text))
            if emails:
                 # Filter out common junk emails
                valid_emails = [e for e in emails if not any(x in e.lower() for x in ['.png', '.jpg', '.jpeg', '.gif', 'sentry', 'example', 'domain'])]
                if valid_emails:
                    content += f"\n\nPossible Emails Found on Page:\n{', '.join(valid_emails[:5])}"

            return content

        except Exception as e:
            print(f"Error extracting {url}: {e}")
            return ""
