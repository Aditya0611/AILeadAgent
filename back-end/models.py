from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class Lead(BaseModel):
    name: str
    company: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    industry: Optional[str] = None
    source: str
    description: Optional[str] = None
    qualification_score: Optional[float] = Field(default=0.0, ge=0.0, le=10.0)
    qualification_reasoning: Optional[str] = None
    status: str = "new"  # new, qualified, contacted, interested, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # New Rich Data Fields
    employee_count: Optional[str] = None
    funding_info: Optional[str] = None
    industry_tags: List[str] = []
    sentiment_score: Optional[float] = 0.0  # -1.0 to 1.0 (Negative to Positive)
    social_media_links: Dict[str, str] = {}  # {"twitter": "url", "linkedin": "url"}
    managers_info: Optional[List[Dict]] = [] # [{"name": "...", "email": "..."}]

class SearchQuery(BaseModel):
    industry: str
    location: Optional[str] = None
    target_persona: Optional[str] = None
    keywords: List[str] = []
