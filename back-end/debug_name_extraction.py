
import sys
import os
from dotenv import load_dotenv

# Add current dir to path to import services
sys.path.append(os.getcwd())

from ai_service import AIService
from models import SearchQuery

load_dotenv()

def test_extraction():
    ai = AIService()
    
    sample_content = """
    About Us - TechCorp Solutions
    TechCorp Solutions is a leading provider of AI-driven automation for the manufacturing industry. 
    Founded in 2015, we have helped over 500 companies optimize their workflows.
    Our headquarters are in San Francisco, CA.
    Contact us at hello@techcorpsolutions.com or call +1-555-0199.
    CEO: Jane Doe.
    """
    
    query = SearchQuery(
        industry="Manufacturing",
        location="San Francisco",
        keywords=["AI", "Automation"]
    )
    
    print("Running extraction...")
    lead = ai.analyze_lead(sample_content, query)
    
    print("\n--- RESULTS ---")
    print(f"Name (field 'name'): {lead.name}")
    print(f"Company (field 'company'): {lead.company}")
    print(f"Score: {lead.qualification_score}")
    print(f"Reasoning: {lead.qualification_reasoning}")
    print(f"Description: {lead.description}")
    print("----------------\n")

if __name__ == "__main__":
    test_extraction()
