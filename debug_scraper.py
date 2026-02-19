import asyncio
import os
import sys

# Add back-end logic to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'back-end')
sys.path.append(backend_dir)

from linkedin_service import LinkedInService

async def debug_scraper():
    print("🐞 Starting Debug Scraper...")
    try:
        service = LinkedInService()
        service.use_headless = False # Force visible browser
        
        # We need to access internal method logic or instantiate Playwright manually 
        # to take screenshots, but for now we can just use the service and 
        # add print statements if we modified it. 
        # Or better, let's just run it and see if it fails or returns empty.
        
        # Test Company
        company = "Microsoft" 
        print(f"   Target Company: {company}")
        
        managers = await service.search_managers(company)
        
        # Note: The service itself closes the browser, so we can't get page content here unless we modify service 
        # OR we rely on the service to have printed debugging info.
        # Let's Modify the Service to dump HTML on failure temporarily? 
        # Actually, simpler: Let's just create a quick custom scraper script here that DOESN'T use the service class
        # but uses the same logic, so we can control it fully.
        pass

    except Exception as e:
        print(f"❌ Error: {e}")

async def debug_scraper_custom():
    from playwright.async_api import async_playwright
    import os
    
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not email:
        print("❌ Credentials missing")
        return

    company = "Microsoft"
    print(f"🕵️ Custom Debug: Logging in as {email}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto("https://www.linkedin.com/login")
            await page.fill("#username", email)
            await page.fill("#password", password)
            await page.click("button[type='submit']")
            
            # Wait for search box check
            try:
                await page.wait_for_selector(".global-nav__search", timeout=15000)
                print("   ✅ Login verify passed")
            except:
                print("   ⚠️ Login verify timed out (might still be ok)")
            
            search_query = f"Manager at {company}"
            url = f"https://www.linkedin.com/search/results/people/?keywords={search_query}&origin=GLOBAL_SEARCH_HEADER"
            print(f"   Navigating to: {url}")
            await page.goto(url)
            
            print("   Waiting for 10s...")
            await page.wait_for_timeout(10000)
            
            print("   📸 Saving debug_page.html...")
            content = await page.content()
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(content)
                
            print(f"   Saved {len(content)} bytes.")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_scraper_custom())
