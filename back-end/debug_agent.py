from main import LeadGenAgent
from models import SearchQuery
import traceback

print("🚀 Starting Debug Run...")

try:
    agent = LeadGenAgent()
    query = SearchQuery(
        industry="E-commerce",
        location="New York",
        target_persona="CTO",
        keywords=["AI"]
    )
    
    # Run the agent
    print("Running agent...")
    agent.run(query)
    print("✅ Agent run finished successfully")

except Exception as e:
    print("\n❌ CRITICAL ERROR CAUGHT:")
    traceback.print_exc()
