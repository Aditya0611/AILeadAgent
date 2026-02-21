from models import SearchQuery, Lead
from database import DatabaseService
from ai_service import AIService
from search_service import SearchService
from logger_util import log_event
import time

class LeadGenAgent:
    def __init__(self):
        self.db = DatabaseService()
        self.ai = AIService()
        self.search = SearchService()

    def run(self, query: SearchQuery):
        log_event(f"Starting lead generation for: {query.industry} in {query.location}")
        
        # 1. Search for leads (3 pages = 30 results max)
        all_results = []
        base_search_term = f"{query.industry} companies in {query.location} {','.join(query.keywords)}"
        
        for page in range(3):
            start_index = (page * 10) + 1
            log_event(f"📄 Fetching page {page + 1}...")
            page_results = self.search.search_leads(
                base_search_term, 
                start_index=start_index, 
                ai_service=self.ai,
                original_query=query
            )
            if not page_results:
                break
            all_results.extend(page_results)
            time.sleep(1) # Polite delay betwen pages
            
        log_event(f"Found {len(all_results)} total raw results. Processing...")
        
        for result in all_results:
            url = result['link']
            log_event(f"Processing: {url}")
            
            # Check if already in DB
            existing = self.db.get_lead_by_website(url)
            if existing:
                log_event(f"Lead already exists: {url}")
                continue
            
            # 2. Extract content
            content = self.search.extract_page_content(url)
            
            # 3. Analyze and Qualify (Use result snippet as fallback content if extraction fails)
            if not content:
                log_event(f"   Using search snippet for {url} (Extraction failed)")
                content = f"Title: {result.get('title')}\nSnippet: {result.get('snippet')}"
                
            lead = self.ai.analyze_lead(content, query)
            if not lead:
                log_event(f"   Skipping {url} (AI analysis failed or rate limited)")
                continue

            lead.website = url  # Ensure website is set
            
            # 4. Save to DB
            if lead.qualification_score >= 0.0:  # Save EVERYTHING for testing
                saved_lead = self.db.save_lead(lead)
                log_event(f"✅ Saved lead: {lead.name} (Score: {lead.qualification_score})")
            else:
                log_event(f"⏭️  Lead skipped (Low score: {lead.qualification_score})")
            
            # Rate limiting / Sleep to avoid blocking
            time.sleep(2)

if __name__ == "__main__":
    # Example usage
    agent = LeadGenAgent()
    test_query = SearchQuery(
        industry="SaaS",
        location="New York",
        target_persona="Marketing Managers",
        keywords=["AI", "Automation"]
    )
    agent.run(test_query)
