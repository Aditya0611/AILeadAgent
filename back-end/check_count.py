from database import DatabaseService

db = DatabaseService()
leads = db.list_leads(limit=1000)
print(f"Total Leads in Database: {len(leads)}")
