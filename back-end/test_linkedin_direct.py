import asyncio
from linkedin_service import LinkedInService
import json

async def test():
    service = LinkedInService()
    print("Testing LinkedIn scraper directly...\n")
    managers = await service.search_managers("Amazon.com, Inc.")
    print(f"\n{'='*50}")
    print(f"FINAL RESULT: Found {len(managers)} managers")
    print(f"{'='*50}\n")
    for i, m in enumerate(managers, 1):
        print(f"{i}. {m['name']}")
        print(f"   Title: {m['title']}")
        print(f"   URL: {m['profile_url']}")
        print()
    
    # Save to file for inspection
    with open("managers_result.json", "w", encoding="utf-8") as f:
        json.dump(managers, f, indent=2)
    print("Saved results to managers_result.json")
    
    return managers

if __name__ == "__main__":
    result = asyncio.run(test())
