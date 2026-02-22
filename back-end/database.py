from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from models import Lead
from typing import List, Optional
from logger_util import log_event

class DatabaseService:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            log_event("❌ CRITICAL: SUPABASE_URL or SERVICE_KEY missing!", "ERROR")
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        try:
            # Mask the URL for safety in logs but show enough to verify
            masked_url = f"{SUPABASE_URL[:12]}...{SUPABASE_URL[-5:]}" if SUPABASE_URL else "None"
            log_event(f"Attempting Supabase connection to: {masked_url}")
            
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            log_event("✅ Supabase connection successful")
        except Exception as e:
            log_event(f"❌ Error: Could not initialize Supabase: {e}", "ERROR")
            self.supabase = None

    def save_lead(self, lead: Lead) -> dict:
        """Saves a lead to the 'leads' table in Supabase."""
        data = lead.dict()
        # Convert datetime to string for JSON serialization if necessary
        data['created_at'] = data['created_at'].isoformat()
        
        try:
            if not self.supabase:
                log_event("Cannot save lead: Supabase not initialized", "ERROR")
                return {}
            response = self.supabase.table("leads").insert(data).execute()
            return response.data[0]
        except Exception as e:
            log_event(f"❌ Error saving lead to Database: {e}", "ERROR")
            return {}

    def get_lead_by_website(self, website: str) -> Optional[dict]:
        """Checks if a lead with the same website already exists."""
        try:
            if not self.supabase:
                return None
            response = self.supabase.table("leads").select("*").eq("website", website).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error checking lead: {e}")
            return None

    def list_leads(self, limit: int = 200) -> List[dict]:
        """Lists latest leads from Supabase."""
        try:
            if not self.supabase:
                return []
            response = self.supabase.table("leads").select("*").order("created_at", desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"Error listing leads: {e}")
            return []
