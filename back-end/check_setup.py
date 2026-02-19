"""
Quick Database Setup Script
Run this to verify your Supabase connection and check if the leads table exists.
"""
from database import DatabaseService
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

def check_database_setup():
    print("=" * 60)
    print("SUPABASE DATABASE SETUP CHECKER")
    print("=" * 60)
    
    try:
        # Test connection
        print("\n1. Testing Supabase connection...")
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("   ✅ Connected to Supabase successfully!")
        
        # Check if leads table exists
        print("\n2. Checking if 'leads' table exists...")
        try:
            response = supabase.table("leads").select("*").limit(1).execute()
            print("   ✅ 'leads' table exists!")
            print(f"   📊 Current lead count: {len(response.data)}")
        except Exception as e:
            error_msg = str(e)
            if "PGRST205" in error_msg or "not found" in error_msg.lower():
                print("   ❌ 'leads' table NOT found!")
                print("\n" + "=" * 60)
                print("ACTION REQUIRED: Create the database table")
                print("=" * 60)
                print("\nFollow these steps:")
                print("1. Go to: https://ydqwvjapqulylkflmcpr.supabase.co")
                print("2. Click 'SQL Editor' in the left sidebar")
                print("3. Click 'New Query'")
                print("4. Copy the contents of 'supabase_setup.sql'")
                print("5. Paste and click 'Run'")
                print("\nOr copy this file path:")
                print("c:\\Users\\rajni\\OneDrive\\Desktop\\Ai 1\\back-end\\supabase_setup.sql")
                print("=" * 60)
                return False
            else:
                raise e
        
        print("\n" + "=" * 60)
        print("✅ DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print("\nYou can now run: python main.py")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_database_setup()
