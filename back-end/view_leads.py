"""
View saved leads from the database
"""
from database import DatabaseService

def view_leads():
    db = DatabaseService()
    try:
        leads = db.list_leads()
    except Exception as e:
        print(f"Error: {e}")
        return

    print(f"\n{'='*60}")
    print(f"📊 SAVED LEADS: {len(leads)} total")
    print(f"{'='*60}\n")
    
    print(f"\nLast 10 Leads:")
    for lead in leads[-10:]:
        print(f"- Name: {lead.get('name')}")
        print(f"  Company: {lead.get('company')}")
        print(f"  Score: {lead.get('qualification_score')}")
        print(f"  Reason/Error: {lead.get('qualification_reasoning')}")
        print("-" * 30)

if __name__ == "__main__":
    view_leads()
