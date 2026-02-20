import asyncio
import os
import json
from playwright.async_api import async_playwright

async def export_session():
    print("\n--- LinkedIn Session Exporter ---")
    print("This tool will help you log in to LinkedIn locally and save your session.")
    print("This allows the Render server to skip the Login/2FA screen.\n")
    
    async with async_playwright() as p:
        # Launch browser in NON-HEADLESS mode so you can see it
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()
        print("Opening LinkedIn Login...")
        await page.goto("https://www.linkedin.com/login")
        
        print("\nACTION REQUIRED:")
        print("1. Log in to your LinkedIn account in the browser window that just opened.")
        print("2. Complete any 2FA or verification codes if asked.")
        print("3. Once you see your LinkedIn Feed, come back here and press ENTER.")
        
        input("\nPress ENTER once you are logged in and see your feed...")
        
        # Save storage state (cookies, local storage, etc.)
        session_file = "session.json"
        storage = await context.storage_state(path=session_file)
        
        print(f"\n✅ SUCCESS! Session saved to {session_file}")
        print("IMPORTANT: Do not share session.json! It contains your login session.")
        print("\nNext steps:")
        print("1. Commit session.json to your GitHub repository.")
        print("2. The Render server will now automatically use this session.\n")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(export_session())
