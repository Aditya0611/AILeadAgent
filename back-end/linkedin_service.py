import os
import asyncio
import re
import time
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

from config import LINKEDIN_ACCESS_TOKEN, BROWSER_HEADLESS
# New credentials
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

class LinkedInService:
    def __init__(self):
        print("LinkedInService INITIALIZED")
        with open("scraper_debug.log", "a", encoding="utf-8") as log:
            log.write(f"\n--- LinkedInService INIT: {time.ctime()} ---\n")
            log.write(f"PLAYWRIGHT_BROWSERS_PATH: {os.getenv('PLAYWRIGHT_BROWSERS_PATH')}\n")
        self.email = LINKEDIN_EMAIL
        self.password = LINKEDIN_PASSWORD
        self.use_headless = BROWSER_HEADLESS # Use config (False for local viewing)

    async def enrich_manager_profiles(self, manager_list: list):
        """
        Takes a list of managers (with profile_url) and extracts contact info for the top 3.
        """
        if not self.email or not self.password:
            print("Missing LinkedIn Credentials in .env")
            return manager_list

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.use_headless)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Login
                print("   Logging in for enrichment...")
                await page.goto("https://www.linkedin.com/login")
                await page.fill("#username", self.email)
                await page.fill("#password", self.password)
                await page.click("button[type='submit']")
                await page.wait_for_selector(".global-nav__search", timeout=45000)
                
                # Enrich each manager (top 3)
                enriched_managers = []
                for i, mgr in enumerate(manager_list):
                    if i >= 3: # Limit for safety
                        enriched_managers.append(mgr)
                        continue
                        
                    if mgr.get("profile_url"):
                        print(f"   [Contact Info] Processing {mgr.get('name')}...")
                        contact_page = await context.new_page()
                        contact_details = await self.safe_extract_contact(contact_page, mgr["profile_url"])
                        mgr.update(contact_details)
                        await contact_page.close()
                        await asyncio.sleep(2)
                    
                    enriched_managers.append(mgr)
                
                return enriched_managers

            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                print(f"Enrichment Error: {e}\n{error_msg}")
                return manager_list
            finally:
                if 'browser' in locals():
                    await browser.close()

    async def safe_extract_contact(self, page, profile_url):
        """Visits profile contact info overlay and extracts email/phone."""
        contact_data = {"email": None, "phone": None}
        if not profile_url or "linkedin.com/in/" not in profile_url:
            return contact_data
            
        try:
            # Direct link to contact overlay
            contact_url = profile_url.rstrip('/') + "/overlay/contact-info/"
            print(f"      Checking contact info: {contact_url}")
            
            await page.goto(contact_url, timeout=30000)
            await asyncio.sleep(2) # Let it load
            
            # Strategy 1: Specific selectors from research
            # Email selector
            email_el = await page.query_selector(".pv-contact-info__contact-type.ci-email a, section.pv-contact-info__contact-type--email a")
            if email_el:
                contact_data["email"] = (await email_el.inner_text()).strip()
                
            # Phone selector
            phone_el = await page.query_selector(".pv-contact-info__contact-type.ci-phone a, section.pv-contact-info__contact-type--phone span:not(.visually-hidden)")
            if phone_el:
                contact_data["phone"] = (await phone_el.inner_text()).strip()
                
            # Strategy 2: Regex fallback if selectors fail but text is there
            if not contact_data["email"] or not contact_data["phone"]:
                body_text = await page.inner_text("body")
                if not contact_data["email"]:
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', body_text)
                    if email_match:
                        contact_data["email"] = email_match.group(0)
                
                if not contact_data["phone"]:
                    # Simple phone regex for common formats
                    phone_match = re.search(r'(\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}', body_text)
                    if phone_match:
                        contact_data["phone"] = phone_match.group(0)

            if contact_data["email"]: print(f"      Found Email: {contact_data['email']}")
            if contact_data["phone"]: print(f"      Found Phone: {contact_data['phone']}")
            
        except Exception as e:
            print(f"      Error in contact extraction: {e}")
            
        return contact_data

    async def search_managers(self, company_name: str):
        """
        Scrapes LinkedIn for managers at the specified company using Playwright.
        """
        loop = asyncio.get_running_loop()
        with open("scraper_debug.log", "a", encoding="utf-8") as log:
            log.write(f"\n--- SCRAPER START: {company_name} ---\n")
            log.write(f"Active Event Loop: {type(loop)}\n")
        print(f"Starting LinkedIn Scraper for: {company_name} (Loop: {type(loop)})")
        managers = []
        
        if not self.email or not self.password:
            print("Missing LinkedIn Credentials in .env")
            return []

        async with async_playwright() as p:
            # Launch browser with realistic User-Agent
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
            try:
                # Log executable check if path is set
                if os.getenv('PLAYWRIGHT_BROWSERS_PATH'):
                    print(f"DEBUG: Using custom browsers path: {os.getenv('PLAYWRIGHT_BROWSERS_PATH')}")

                browser = await p.chromium.launch(
                    headless=self.use_headless,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                
                # Use storage_state if available to bypass 2FA/Login
                session_file = "session.json"
                if os.path.exists(session_file):
                    print(f"   Using existing session from {session_file}")
                    context = await browser.new_context(
                        storage_state=session_file,
                        user_agent=user_agent,
                        viewport={'width': 1920, 'height': 1080}
                    )
                else:
                    print("   No session.json found. Proceeding with manual login.")
                    context = await browser.new_context(
                        user_agent=user_agent,
                        viewport={'width': 1920, 'height': 1080}
                    )
                
                # Add stealth scripts
                page = await context.new_page()
                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                print(f"FATAL: Browser/Context launch failed: {e}\n{error_msg}")
                return []
            
            try:
                # 1. Login (only if needed)
                print("   Checking login status...")
                await page.goto("https://www.linkedin.com/feed/", timeout=30000)
                
                # Check if we are already logged in
                if "login" in page.url or await page.query_selector("#username"):
                    print("   Session expired or missing. Logging in manually...")
                    await page.goto("https://www.linkedin.com/login")
                    await page.fill("#username", self.email)
                    await page.fill("#password", self.password)
                    await page.click("button[type='submit']")
                
                # Wait for login to complete (check for feed or search box)
                try:
                    await page.wait_for_selector(".global-nav__search", timeout=30000)
                    print("   ✅ Login Successful!")
                    # Refresh session state if we logged in manually
                    if not os.path.exists(session_file):
                        await context.storage_state(path=session_file)
                except:
                    # Capture screenshot for Render debug
                    screenshot_path = "debug_login_failure.png"
                    await page.screenshot(path=screenshot_path)
                    print(f"   ⚠️ Login challenge or timeout. Screenshot saved to {screenshot_path}")
                    print(f"   Current URL: {page.url}")
                    # Log more details from the page
                    try:
                        title = await page.title()
                        print(f"   Page Title: {title}")
                    except:
                        pass
                
                # 2. Search for Managers
                search_query = f"Manager at {company_name}"
                print(f"   Searching for: {search_query}")
                
                await page.goto(f"https://www.linkedin.com/search/results/people/?keywords={search_query}&origin=GLOBAL_SEARCH_HEADER")
                
                # Wait for results
                print("   Waiting for search results...")
                try:
                    # Reduced timeout for faster fallback
                    await page.wait_for_selector("div[role='listitem'], .reusable-search__result-container", timeout=20000)
                except:
                    print("   ⚠️ Primary list selector timed out. Checking for 'No results' or other structures.")
                
                # 3. Extract Data - Robust Strategy
                # Try multiple selectors to find result items
                results = await page.query_selector_all("div[role='listitem'], .reusable-search__result-container, li.reusable-search__result-container, li")
                
                print(f"   Potential results found: {len(results)}")
                with open("scraper_debug.log", "a", encoding="utf-8") as log:
                    log.write(f"   Potential results found: {len(results)}\n")
                
                # Filter out items with minimal text (likely not profile results)
                valid_results = []
                for res in results:
                    try:
                        text = (await res.inner_text()).strip()
                        if len(text) > 20:  # Arbitrary threshold to filter empty items
                            valid_results.append(res)
                    except:
                        continue
                
                if not valid_results:
                    print(f"   ⚠️ No results found. Current Page: {page.url}")
                    print(f"   ⚠️ Page Title: {await page.title()}")

                print(f"   Found {len(valid_results)} potential profiles on page 1.")
                
                for result in valid_results[:5]: # Top 5
                    try:
                        # NEW STRATEGY: Pattern-Based Extraction
                        text = await result.inner_text()
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        # print(f"   RAW LINES: {lines}")
                        
                        name = None
                        title = None
                        
                        # Filter out UI elements and look for meaningful content
                        meaningful_lines = []
                        for line in lines:
                            # Skip UI text
                            if line in ["Message", "Connect", "Follow", "Save"]:
                                continue
                            if "View" in line and "profile" in line:
                                continue
                            if len(line) < 3:
                                continue
                            meaningful_lines.append(line)
                        
                        # Now extract name and title from meaningful lines
                        for line in meaningful_lines:
                            # Title indicators: contains "at" or job keywords
                            is_title = (" at " in line or 
                                       "Manager" in line or 
                                       "Director" in line or 
                                       "Engineer" in line or 
                                       "Lead" in line or
                                       "Specialist" in line or
                                       "Analyst" in line)
                            
                            # Location indicators (skip these as names)
                            is_location = ("," in line and len(line.split(",")) >= 2)  # "City, State" pattern
                            
                            if is_title and not title:
                                title = line
                            elif not is_title and not is_location and not name and not line.startswith("LinkedIn Member"):
                                name = line
                        
                        # Fallback: use first two meaningful lines
                        if not name and len(meaningful_lines) > 0:
                            # If first line looks like a title, use second as name
                            if " at " in meaningful_lines[0]:
                                name = meaningful_lines[1] if len(meaningful_lines) > 1 else "Unknown User"
                                title = meaningful_lines[0]
                            else:
                                name = meaningful_lines[0]
                                title = meaningful_lines[1] if len(meaningful_lines) > 1 else "LinkedIn Member"
                        
                        if not name:
                            name = "Unknown User"
                        if not title:
                            title = "LinkedIn Member"
                        
                        # Extract Profile Link (best effort)
                        link = ""
                        try:
                            # Try the app-aware-link found by research first
                            link_el = await result.query_selector("a.app-aware-link, a[href*='/in/']")
                            if link_el:
                                link = await link_el.get_attribute("href")
                                if link and link.startswith("/"):
                                    link = "https://www.linkedin.com" + link
                        except:
                            pass
                        
                        # Debug logging
                        print(f"   EXTRACTED RESULT -> Name: '{name}' | Title: '{title}'")
                        
                        # Skip if no real data (be less aggressive on skipping if we have a title)
                        if (not name or name == "Unknown User" or name.startswith("LinkedIn Member")) and not title:
                            print(f"   Skipping: No profile access and no title")
                            continue

                        manager_info = {
                            "name": name.strip() if name else "LinkedIn Member",
                            "title": title.strip() if title else "LinkedIn Member",
                            "email": None,
                            "phone": None,
                            "profile_url": link.split('?')[0] if link else ""
                        }

                        # EXTRACT CONTACT INFO for the top managers
                        # Limit to top 3 to avoid excessive navigation/detection
                        if len(managers) < 3 and manager_info["profile_url"]:
                            print(f"   [Contact Info] Processing {manager_info['name']}...")
                            # Create a new page for contact extraction to keep search results active
                            contact_page = await context.new_page()
                            contact_details = await self.safe_extract_contact(contact_page, manager_info["profile_url"])
                            manager_info.update(contact_details)
                            await contact_page.close()
                            # Extra sleep to be more human-like
                            await asyncio.sleep(1.5)

                        managers.append(manager_info)
                    except Exception as e:
                        print(f"   Error parsing result: {e}")
                        continue
                        
            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                print(f"Scraper Error: {e}\n{error_msg}")
                with open("scraper_debug.log", "a", encoding="utf-8") as log:
                    log.write(f"Scraper Error: {e}\n{error_msg}\n")
            finally:
                if 'browser' in locals():
                    await browser.close()
        
        return managers

    def verify_token(self):
         # Legacy / Optional
         return True
