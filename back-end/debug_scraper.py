import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

async def run_debug():
    print("🤖 Starting Debug LinkedIn Scraper...")
    
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        print("❌ Missing LinkedIn Credentials")
        return

    company_name = "Amazon.com, Inc."
    search_query = f"Manager at {company_name}"

    async with async_playwright() as p:
        # Launch browser in HEADLESS mode false to hopefully see it, 
        # but we rely on screenshots for the agent.
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. Login
            print("   Logging in...")
            await page.goto("https://www.linkedin.com/login")
            await page.screenshot(path="debug_01_login_page.png")
            
            await page.fill("#username", LINKEDIN_EMAIL)
            await page.fill("#password", LINKEDIN_PASSWORD)
            await page.click("button[type='submit']")
            
            # Wait for login
            try:
                await page.wait_for_selector(".global-nav__search", timeout=15000)
                print("   ✅ Login Successful!")
            except:
                print("   ⚠️ Login challenge or failure detected.")
            
            await page.screenshot(path="debug_02_after_login.png")

            # 2. Search
            print(f"   Searching for: {search_query}")
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query}&origin=GLOBAL_SEARCH_HEADER"
            await page.goto(search_url)
            
            print("   Waiting for search results...")
            try:
                await page.wait_for_selector("div[role='listitem'], .reusable-search__result-container", timeout=15000)
                print("   ✅ Search results loaded (selector found).")
            except:
                print("   ⚠️ Search results selector timed out.")
            
            await page.screenshot(path="debug_03_search_results.png")
            
            # 3. Inspect Page Content
            content = await page.content()
            if "No results found" in content:
                print("   ⚠️ Page contains 'No results found' text.")
            
            # Robust Selector Strategy
            # 1. Try generic list items
            results = await page.query_selector_all("div[role='listitem'], .reusable-search__result-container, li.reusable-search__result-container, li")
            
            # Filter results that look too small (e.g. strict layout checks)
            valid_results = []
            for res in results:
                txt = await res.inner_text()
                if len(txt) > 20: # arbitrary filter to avoid empty list items
                    valid_results.append(res)
            
            print(f"   Found {len(valid_results)} potential result items.")
            
            for i, res in enumerate(valid_results[:5]):
                print(f"   --- Item {i+1} ---")
                try:
                    # Strategy A: Text Parsing
                    text = await res.inner_text()
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    
                    name = "Unknown"
                    title = "Unknown"
                    
                    if len(lines) > 0:
                        name = lines[0]
                    if len(lines) > 1:
                        # Sometimes 2nd line is "View name's profile", skip it
                        if "View" in lines[1] and "profile" in lines[1]:
                             if len(lines) > 2: title = lines[2]
                        else:
                             title = lines[1]
                             
                    print(f"      Extracted Name: {name}")
                    print(f"      Extracted Title: {title}")
                    
                    # Strategy B: Link Extraction (Best Effort)
                    link_el = await res.query_selector("a[href*='/in/']")
                    if link_el:
                        href = await link_el.get_attribute("href")
                        print(f"      Extracted Link: {href.split('?')[0]}")
                    else:
                        print("      No direct profile link found.")

                except Exception as e:
                    print(f"      Error parsing item: {e}")
                    
            # Try to fix the main scraper logic based on observation
            # ...

        except Exception as e:
            print(f"❌ Error: {e}")
            await page.screenshot(path="debug_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_debug())
