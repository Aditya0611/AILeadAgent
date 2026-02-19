
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

print(f"URL: {url}")
print(f"Key present: {bool(key)}")

if not url or not key:
    print("Missing credentials")
    exit(1)

try:
    supabase: Client = create_client(url, key)
    print("Client created")
    
    response = supabase.table("leads").select("count", count="exact").limit(1).execute()
    print(f"Connection successful! Row count: {response.count}")
    
    # Try to fetch some leads
    leads = supabase.table("leads").select("*").limit(5).execute()
    print(f"Fetched {len(leads.data)} leads")
    for l in leads.data:
        print(f"Name: {l.get('name')}, Company: {l.get('company')}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
