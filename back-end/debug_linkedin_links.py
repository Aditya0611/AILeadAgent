import os
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

async def debug_links():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Login
        await page.goto("https://www.linkedin.com/login")
        await page.fill("#username", LINKEDIN_EMAIL)
        await page.fill("#password", LINKEDIN_PASSWORD)
        await page.click("button[type='submit']")
        await page.wait_for_selector(".global-nav__search", timeout=45000)
        
        # Search
        search_query = "Manager at Amazon"
        await page.goto(f"https://www.linkedin.com/search/results/people/?keywords={search_query}")
        await page.wait_for_selector("div[role='listitem'], .reusable-search__result-container", timeout=45000)
        
        # Inspect Results
        results = await page.query_selector_all("div[role='listitem'], .reusable-search__result-container")
        print(f"Found {len(results)} results")
        
        for i, res in enumerate(results[:3]):
            html = await res.evaluate("el => el.outerHTML")
            print(f"\nResult {i+1} HTML:\n{html}\n")
            
            links = await res.query_selector_all("a")
            print(f"Found {len(links)} links in item")
            for link in links:
                href = await link.get_attribute("href")
                text = (await link.inner_text()).strip()
                print(f"  - Text: '{text}', Href: '{href}'")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_links())
