import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()

async def debug_extraction():
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Login
            await page.goto("https://www.linkedin.com/login")
            await page.fill("#username", email)
            await page.fill("#password", password)
            await page.click("button[type='submit']")
            await page.wait_for_selector(".global-nav__search", timeout=15000)
            
            # Search
            search_url = "https://www.linkedin.com/search/results/people/?keywords=Manager at Amazon.com, Inc.&origin=GLOBAL_SEARCH_HEADER"
            await page.goto(search_url)
            await page.wait_for_selector("div[role='listitem'], .reusable-search__result-container", timeout=15000)
            
            # Get results
            results = await page.query_selector_all("div[role='listitem'], .reusable-search__result-container, li.reusable-search__result-container, li")
            
            valid_results = []
            for res in results:
                text = await res.inner_text()
                if len(text) > 20:
                    valid_results.append(res)
            
            print(f"Found {len(valid_results)} valid results\n")
            
            # Analyze first 3
            for i, res in enumerate(valid_results[:3]):
                print(f"=== RESULT {i+1} ===")
                text = await res.inner_text()
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                print(f"Total lines: {len(lines)}")
                for j, line in enumerate(lines[:10]):  # First 10 lines
                    print(f"  Line {j}: '{line}'")
                print()
                
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_extraction())
