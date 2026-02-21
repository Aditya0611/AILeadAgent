from database import DatabaseService
from ai_service import AIService
from models import SearchQuery
import time

def migrate_industry():
    db = DatabaseService()
    ai = AIService()
    
    print("🚀 Starting industry migration for existing leads...")
    leads = db.list_leads(limit=1000)
    print(f"Found {len(leads)} leads to check.")
    
    updated_count = 0
    for lead_data in leads:
        lead_id = lead_data.get('id')
        current_industry = lead_data.get('industry')
        
        if not current_industry or current_industry == 'N/A':
            print(f"Enriching industry for: {lead_data.get('company') or lead_data.get('name')}")
            
            # Simple query mock for context
            query = SearchQuery(
                industry="Unknown", 
                keywords=lead_data.get('industry_tags') or []
            )
            
            # Mock content from existing data if possible
            content = f"Company: {lead_data.get('company')}\nDescription: {lead_data.get('description')}\nTags: {', '.join(lead_data.get('industry_tags') or [])}"
            
            try:
                enriched_lead = ai.analyze_lead(content, query)
                industry = enriched_lead.industry
                
                if industry and industry != 'Unknown':
                    db.supabase.table("leads").update({"industry": industry}).eq("id", lead_id).execute()
                    print(f"✅ Updated to: {industry}")
                    updated_count += 1
                else:
                    print("⏭️ AI could not determine specific industry.")
            except Exception as e:
                print(f"❌ Error enriching {lead_id}: {e}")
            
            # Rate limiting / Sleep
            time.sleep(1)
            
    print(f"🎉 Migration complete! Updated {updated_count} leads.")

if __name__ == "__main__":
    migrate_industry()
