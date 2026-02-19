from database import DatabaseService
import requests

db = DatabaseService()
leads = db.list_leads(limit=100)
amazon_id = None
for l in leads:
    if l.get('company') and 'Amazon' in l['company']:
        amazon_id = l['id']
        break

if amazon_id:
    print(f"Found Amazon Lead ID: {amazon_id}")
    url = f"http://localhost:8000/leads/{amazon_id}/enrich-managers"
    print(f"Triggering enrichment via: {url}")
    try:
        # Using a long timeout because scraping takes time (5 minutes)
        response = requests.post(url, timeout=300)
        print(f"Response Status: {response.status_code}")
        print(f"Response Data: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Amazon lead not found in database.")
