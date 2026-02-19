import sys
import os

# Add back-end logic to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'back-end')
sys.path.append(backend_dir)

try:
    from linkedin_service import LinkedInService
except ImportError as e:
    print(f"Error importing LinkedInService: {e}")
    # try running from within back-end dir context?
    sys.exit(1)

import asyncio

async def test_service():
    print("Testing LinkedIn Service...")
    service = LinkedInService()
    
    # 1. Verify Token
    print("\n1. Verifying Token...")
    profile = service.verify_token()
    if profile:
        print(f"   > Token Valid (Result: {profile})")
    else:
        print("   > Token Invalid or API Error.")

    # 2. Search Managers
    print("\n2. Searching Managers (Test: 'Salesforce')...")
    managers = await service.search_managers("Salesforce")
    print(f"   > Found {len(managers)} managers.")
    for m in managers:
        print(f"     - {m['name']} ({m['title']})")
        print(f"       Email: {m.get('email', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_service())
