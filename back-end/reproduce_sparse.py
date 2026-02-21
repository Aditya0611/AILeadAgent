from ai_service import AIService
from models import SearchQuery
import json

def test_sparse_analysis():
    ai = AIService()
    query = SearchQuery(
        industry="SaaS",
        location="New York",
        keywords=["AI", "Automation"]
    )
    
    # Mock data from a brainstormed lead
    snippet_content = "Title: Sailthru\nSnippet: Sailthru is a personalized marketing automation platform for retail and media companies."
    
    print("Testing extraction from sparse snippet...")
    lead = ai.analyze_lead(snippet_content, query)
    
    print(f"Resulting Lead Name: {lead.name}")
    print(f"Resulting Lead Company: {lead.company}")
    print(f"Resulting Lead Score: {lead.qualification_score}")
    print(f"Resulting Lead Industry: {lead.industry}")

if __name__ == "__main__":
    test_sparse_analysis()
