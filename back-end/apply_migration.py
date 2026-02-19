from database import DatabaseService
import os

def apply_migration():
    print("🔄 Applying database migration...")
    db = DatabaseService()
    
    # SQL commands to run
    commands = [
        "ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS employee_count TEXT;",
        "ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS funding_info TEXT;",
        "ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS industry_tags TEXT[];",
        "ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS sentiment_score DECIMAL(3,2);",
        "ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS social_media_links JSONB DEFAULT '{}'::jsonb;",
        "CREATE INDEX IF NOT EXISTS idx_leads_industry_tags ON public.leads USING GIN (industry_tags);"
    ]
    
    try:
        # We can't run raw SQL easily with the simple client, so we might have to use a workaround 
        # or ask the user to run it in Supabase dashboard. 
        # However, we can try to use a postgres client if available, or just use the REST API 
        # to insert a dummy record with new fields to force schema update? No, that won't work in SQL.
        
        # Let's try to see if we can use the `rpc` call if there's a generic exec function, 
        # commonly "exec_sql" or similar. If not, we'll inform the user.
        
        # CHANGED STRATEGY: 
        # Since we don't have direct SQL access via this client easily without setup, 
        # I will ask the user to run the SQL in their Supabase SQL Editor for 100% safety,
        # OR I can try to use `psycopg2` if installed?
        
        # Let's try to just print the instructions for now, as I don't want to break the connection.
        pass
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    # Just creating a file to document the migration for the user
    print("⚠️  Automated migration via REST API is limited.")
    print("👉 Please run the following SQL in your Supabase SQL Editor:")
    print("-" * 50)
    with open("migration_enrichData.sql", "r") as f:
        print(f.read())
    print("-" * 50)
