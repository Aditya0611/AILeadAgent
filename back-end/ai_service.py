from groq import Groq
from config import GROQ_API_KEY
from models import Lead, SearchQuery
import json
import re
import time
from typing import List, Dict
from logger_util import log_event

class AIService:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY must be set in .env")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = 'llama-3.3-70b-versatile' # Validated working model

    def analyze_lead(self, content: str, query: SearchQuery) -> Lead:
        """
        Analyzes page content using Groq (Llama 3) to extract lead info.
        """
        # Truncate content slightly to fit context if needed, though Llama 3 is generous (8192)
        safe_content = content[:25000]

        prompt = f"""
        You are an expert Lead Generation Analyst. Analyze the text below and extract structured data.
        
        SEARCH CONTEXT:
        - Industry: {query.industry}
        - Location: {query.location}
        - Keywords: {', '.join(query.keywords)}

        TASK:
        Extract company info, contact details, funding, size, sentiment, and score the lead (0-10).
        
        SCORING:
        +3 Exact match, +2 Keywords present, +2 Contact info found, +1 Location match.

        RETURN JSON ONLY:
        {{
            "company_name": "Official Brand/Company Name",
            "industry": "Primary Industry (e.g. SaaS, Fintech, etc.)",
            "website": "URL",
            "email": "email or null",
            "phone": "phone or null",
            "linkedin_url": "url or null",
            "twitter_url": "url or null",
            "description": "Short description of what they do",
            "qualification_score": 0.0,
            "qualification_reasoning": "Detailed reason for the score",
            "employee_count": "e.g. 50-100",
            "funding_info": "e.g. Series A",
            "industry_tags": ["tag1", "tag2"],
            "sentiment_score": 0.8,
            "social_media_links": {{}}
        }}

        CONTENT:
        {safe_content}
        """
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=self.model,
                    response_format={"type": "json_object"}, # Groq supports JSON mode!
                )
                
                response_text = chat_completion.choices[0].message.content
                data = json.loads(response_text)
                
                return Lead(
                    name=data.get('company_name') or 'Unknown',
                    company=data.get('company_name'),
                    website=data.get('website'),
                    industry=data.get('industry') or query.industry,
                    email=data.get('email'),
                    phone=data.get('phone'),
                    linkedin_url=data.get('linkedin_url'),
                    twitter_url=data.get('twitter_url'),
                    description=data.get('description'),
                    qualification_score=float(data.get('qualification_score') or 0.0),
                    qualification_reasoning=data.get('qualification_reasoning'),
                    status="new",
                    source="AI Extraction",
                    employee_count=data.get('employee_count'),
                    funding_info=data.get('funding_info'),
                    industry_tags=data.get('industry_tags') or [],
                    sentiment_score=float(data.get('sentiment_score') or 0.0),
                    social_media_links=data.get('social_media_links') or {}
                )

            except Exception as e:
                # Rate limit handling (Groq uses 429 too)
                if "429" in str(e):
                    if attempt < max_retries - 1:
                        sleep_time = (attempt + 1) * 5 # Groq recovers faster usually
                        log_event(f"⚠️ Groq Rate Limit. Sleeping {sleep_time}s...", "WARNING")
                        time.sleep(sleep_time)
                        continue
                log_event(f"Error analyzing lead (Groq): {e}", "ERROR")
                if attempt == max_retries - 1:
                     return Lead(name="Error Processing", source="Error", qualification_score=0.0, qualification_reasoning=f"Error: {str(e)}")

        return Lead(name="Error Processing", source="Error", qualification_score=0.0, qualification_reasoning="Unknown Error")

    def brainstorm_leads(self, query: SearchQuery) -> List[Dict]:
        """
        Uses AI to brainstorm real companies that fit the search criteria
        if the Google Search API is unavailable.
        """
        prompt = f"""
        You are an expert Lead Generation Specialist. Brainstorm a list of 5-10 REAL companies that fit these criteria:
        
        CRITERIA:
        - Industry: {query.industry}
        - Location: {query.location}
        - Target Persona: {query.target_persona}
        - Keywords: {', '.join(query.keywords)}

        TASK:
        Provide a list of companies with their names, official websites, and a snippet about them.
        Only include real, active companies.
        
        RETURN JSON ONLY:
        {{
            "leads": [
                {{
                    "title": "Company Name",
                    "link": "https://www.company.com",
                    "snippet": "Short description of the company and why they fit the search."
                }}
            ]
        }}
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"},
            )
            response_text = chat_completion.choices[0].message.content
            return data.get('leads', [])
        except Exception as e:
            log_event(f"Error brainstorming leads: {e}", "ERROR")
            return []
