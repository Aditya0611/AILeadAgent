from bs4 import BeautifulSoup

def inspect():
    try:
        with open("debug_page.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        items = soup.select(".reusable-search__result-container") 
        if not items:
             items = soup.select("div[role='listitem']") # Attempt alternate selector
        
        if items:
            item = items[0]
            print(f"--- First Item Structure (Recursive) ---")
            
            # Print all links and spans to see where the name is
            for tag in item.find_all(['a', 'span', 'div']):
                 classes = tag.get('class', [])
                 text = tag.get_text(strip=True)
                 if text and len(text) < 50: # Only print interesting short text
                     print(f"{tag.name} | Class: {classes} | Text: {text}")
                 elif tag.name == 'a':
                     print(f"{tag.name} | Class: {classes} | Href: {tag.get('href', '')}")

        else:
            print("No items found.")

    except Exception as e:
        print(e)

if __name__ == "__main__":
    inspect()
