import sys
import asyncio

if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import csv
import io

from database import DatabaseService
from ai_service import AIService
from search_service import SearchService
from linkedin_service import LinkedInService
from models import Lead, SearchQuery
from main import LeadGenAgent

app = FastAPI(title="Lead Generation API")

@app.on_event("startup")
async def startup_event():
    import os
    loop = asyncio.get_running_loop()
    with open("api_trace.log", "a", encoding="utf-8") as f:
        f.write(f"\n--- API STARTUP: {datetime.now()} ---\n")
        f.write(f"Startup event loop: {type(loop)}\n")
        f.write(f"Working Directory: {os.getcwd()}\n")
        f.write(f"PLAYWRIGHT_BROWSERS_PATH: {os.getenv('PLAYWRIGHT_BROWSERS_PATH')}\n")
    print(f"Startup event loop: {type(loop)}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"PLAYWRIGHT_BROWSERS_PATH: {os.getenv('PLAYWRIGHT_BROWSERS_PATH')}")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseService()
search_service = SearchService()
linkedin_service = LinkedInService()

# Pydantic models for API
class LeadCreate(BaseModel):
    name: str
    company: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    description: Optional[str] = None
    qualification_score: Optional[float] = 0.0
    qualification_reasoning: Optional[str] = None
    status: str = "new"

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    description: Optional[str] = None
    qualification_score: Optional[float] = None
    qualification_reasoning: Optional[str] = None
    status: Optional[str] = None
    managers_info: Optional[List[dict]] = None

class AgentRunRequest(BaseModel):
    industry: str
    location: Optional[str] = None
    target_persona: Optional[str] = None
    keywords: List[str] = []

@app.get("/")
async def read_root():
    return {"message": "Lead Generation API", "version": "1.0"}

@app.get("/leads")
def get_leads(
    limit: int = 50,
    min_score: Optional[float] = None,
    status: Optional[str] = None
):
    """Get all leads with optional filtering"""
    try:
        leads = db.list_leads(limit=limit)
        
        # Apply filters
        if min_score is not None:
            leads = [l for l in leads if l.get('qualification_score', 0) >= min_score]
        
        if status:
            leads = [l for l in leads if l.get('status') == status]
        
        return {"leads": leads, "count": len(leads)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leads/{lead_id}")
def get_lead(lead_id: str):
    """Get a specific lead by ID"""
    try:
        lead = db.supabase.table("leads").select("*").eq("id", lead_id).execute()
        if not lead.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        return lead.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/leads")
def create_lead(lead: LeadCreate):
    """Manually create a new lead"""
    try:
        new_lead = Lead(
            name=lead.name,
            company=lead.company,
            website=lead.website,
            email=lead.email,
            phone=lead.phone,
            linkedin_url=lead.linkedin_url,
            twitter_url=lead.twitter_url,
            source="Manual Entry",
            description=lead.description,
            qualification_score=lead.qualification_score,
            qualification_reasoning=lead.qualification_reasoning,
            status=lead.status
        )
        saved = db.save_lead(new_lead)
        return {"message": "Lead created successfully", "lead": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/leads/{lead_id}")
def update_lead(lead_id: str, lead: LeadUpdate):
    """Update an existing lead"""
    try:
        # Get existing lead
        existing = db.supabase.table("leads").select("*").eq("id", lead_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Update only provided fields
        update_data = {k: v for k, v in lead.dict().items() if v is not None}
        
        if update_data:
            response = db.supabase.table("leads").update(update_data).eq("id", lead_id).execute()
            return {"message": "Lead updated successfully", "lead": response.data[0]}
        
        return {"message": "No changes made", "lead": existing.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/leads/{lead_id}")
def delete_lead(lead_id: str):
    """Delete a lead"""
    try:
        response = db.supabase.table("leads").delete().eq("id", lead_id).execute()
        return {"message": "Lead deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import BackgroundTasks

@app.post("/run-agent")
async def run_agent(request: AgentRunRequest, background_tasks: BackgroundTasks):
    """Trigger the lead generation agent in background"""
    try:
        query = SearchQuery(
            industry=request.industry,
            location=request.location,
            target_persona=request.target_persona,
            keywords=request.keywords
        )
        
        agent = LeadGenAgent()
        # Add to background tasks so API returns immediately
        background_tasks.add_task(agent.run, query)
        
        return {"message": "Agent started in background! Check back in a few minutes for new leads.", "query": request.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export-csv")
def export_csv():
    """Export all leads to CSV"""
    try:
        leads = db.list_leads(limit=1000)
        
        # Create CSV in memory
        output = io.StringIO()
        if leads:
            fieldnames = ['name', 'company', 'website', 'email', 'phone', 
                         'linkedin_url', 'twitter_url', 'qualification_score', 
                         'status', 'created_at']
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(leads)
        
        # Convert to bytes for streaming
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=leads.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_stats():
    """Get dashboard statistics"""
    try:
        all_leads = db.list_leads(limit=1000)
        
        total = len(all_leads)
        qualified = len([l for l in all_leads if l.get('qualification_score', 0) >= 5.0])
        avg_score = sum(l.get('qualification_score', 0) for l in all_leads) / total if total > 0 else 0
        
        status_counts = {}
        for lead in all_leads:
            status = lead.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_leads": total,
            "qualified_leads": qualified,
            "average_score": round(avg_score, 2),
            "status_breakdown": status_counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/leads/{lead_id}/enrich-managers")
async def enrich_lead_managers(lead_id: str):
    """Fetch manager details from LinkedIn for a specific lead"""
    with open("api_trace.log", "a", encoding="utf-8") as f:
        f.write(f"\n--- API REQUEST: enrichment for lead {lead_id} ---\n")
        
    try:
        # Get existing lead
        existing = db.supabase.table("leads").select("*").eq("id", lead_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead_data = existing.data[0]
        company = lead_data.get('company')
        
        if not company:
            # Fallback to name if company not set
            company = lead_data.get('name')
            
        with open("api_trace.log", "a", encoding="utf-8") as f:
            f.write(f"Enriching managers for lead {lead_id}, company: {company}\n")
            
        # Fetch managers (Async call now)
        managers = await linkedin_service.search_managers(company)
        
        # Check if results are restricted (mostly "LinkedIn Member")
        is_restricted = False
        if not managers:
            is_restricted = True
        else:
            member_count = sum(1 for m in managers if m.get('name', '') == 'LinkedIn Member' or 'Greater' in m.get('name', ''))
            if member_count >= len(managers) * 0.5: # mostly restricted
                is_restricted = True
        
        if is_restricted:
            with open("api_trace.log", "a", encoding="utf-8") as f:
                f.write(f"LinkedIn results restricted. Trying Google discovery...\n")
            
            # Use Google to find real names and LinkedIn URLs
            google_query = f'site:linkedin.com/in "Manager" at "{company}"'
            discovery_results = search_service.search_leads(google_query)
            
            if discovery_results:
                potential_managers = []
                for res in discovery_results[:3]: # Top 3
                    title_raw = res.get('title', '')
                    # Extract name from title like "Mohit Raj - Manager at Amazon | LinkedIn"
                    name_part = title_raw.split('-')[0].split('|')[0].strip()
                    potential_managers.append({
                        "name": name_part,
                        "title": title_raw,
                        "email": None,
                        "phone": None,
                        "profile_url": res.get('link', '')
                    })
                
                if potential_managers:
                    # Enrich these specific profiles via LinkedIn
                    enriched = await linkedin_service.enrich_manager_profiles(potential_managers)
                    if enriched:
                        managers = enriched

        with open("api_trace.log", "a", encoding="utf-8") as f:
            f.write(f"Scraper/Discovery returned {len(managers)} managers\n")
        
        # Update lead
        if db.supabase:
            response = db.supabase.table("leads").update({"managers_info": managers}).eq("id", lead_id).execute()
        else:
            with open("api_trace.log", "a", encoding="utf-8") as f:
                f.write("⚠️ Warning: Lead updated locally but could not save to Supabase (client offline)\n")
        
        return {"message": "Lead enriched with manager details", "managers": managers}
        
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open("api_trace.log", "a", encoding="utf-8") as f:
            f.write(f"ERROR in enrichment: {str(e)}\n{error_msg}\n")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    import uvicorn
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    config = uvicorn.Config("api:app", host="0.0.0.0", port=8001, reload=False, loop="asyncio")
    server = uvicorn.Server(config)
    
    # Use a specific way to run the server on Windows to ensure Proactor
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(server.serve())

if __name__ == "__main__":
    main()
