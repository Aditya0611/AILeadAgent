import asyncio
import os
import sys
from linkedin_service import LinkedInService
from dotenv import load_dotenv

async def test_scraper():
    print("\n" + "="*50)
    print("🔍 LINKEDIN SCRAPER DIRECT TEST")
    print("="*50 + "\n")
    
    load_dotenv()
    
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not email or not password:
        print("❌ ERROR: LinkedIn credentials missing in .env")
        return

    service = LinkedInService()
    # Force headful for local debugging if desired, or keep as is
    service.use_headless = False 
    
    test_company = "Amazon"
    print(f"🚀 Starting test for: {test_company}")
    
    try:
        managers = await service.search_managers(test_company)
        
        print("\n" + "="*50)
        print(f"📊 RESULTS: Found {len(managers)} managers")
        print("="*50)
        
        for i, m in enumerate(managers):
            print(f"{i+1}. {m['name']} - {m['title']}")
            if m.get('profile_url'):
                print(f"   Link: {m['profile_url']}")
            if m.get('email'):
                print(f"   Email: {m['email']}")
                
    except Exception as e:
        import traceback
        print(f"\n❌ FATAL ERROR: {e}")
        traceback.print_exc()

    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_scraper())
