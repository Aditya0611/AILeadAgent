
import sys
import asyncio
import os
from dotenv import load_dotenv

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

sys.path.append(os.getcwd())
from linkedin_service import LinkedInService

load_dotenv()

async def test_search():
    print(f"Loop type: {type(asyncio.get_running_loop())}")
    service = LinkedInService()
    # Test with a known company
    res = await service.search_managers("Amazon")
    print(f"\n--- Results ({len(res)}) ---")
    for m in res:
        print(f"- {m['name']} ({m['title']})")
    print("--- Done ---")

if __name__ == "__main__":
    try:
        asyncio.run(test_search())
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
