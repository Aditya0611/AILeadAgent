from database import DatabaseService
db = DatabaseService()
leads = db.list_leads(limit=100)
for l in leads:
    if l.get('company') and 'Amazon' in l['company']:
        print(f"{l['id']} | {l['company']}")
