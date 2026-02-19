from bs4 import BeautifulSoup
import os

file_path = r'c:\Users\rajni\OneDrive\Desktop\Ai 1\debug_page.html'
output_path = r'c:\Users\rajni\OneDrive\Desktop\Ai 1\analysis_result_utf8.txt'

if not os.path.exists(file_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"File not found: {file_path}")
    exit()

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

soup = BeautifulSoup(content, 'html.parser')

results = []
results.append(f"Title: {soup.title.string.strip() if soup.title else 'No Title'}")

# Check for existence of classes
classes_to_check = [
    'reusable-search__result-container',
    'reusable-search__entity-result-list',
    'entity-result',
    'search-results-container',
    'reusable-search__result-container',
    'artdeco-card',
    'reusable-search__result-item',
    'search-no-results__container',
    'search-results__list',
    'authentication-outlet' # check for auth wall
]

results.append("\nClass Check:")
for cls in classes_to_check:
    elements = soup.find_all(class_=cls)
    results.append(f"Class '{cls}': {len(elements)} found")

# Helper to explore structure if no standard classes found
results.append("\nStructure exploration:")
main = soup.find('main')
if main:
    results.append(f"Main tag found. Direct children: {[child.name for child in main.find_all(recursive=False)]}")
    # Print classes of main's children
    for child in main.find_all(recursive=False):
        if child.has_attr('class'):
            results.append(f"Child <{child.name}> classes: {child['class']}")
else:
    results.append("No <main> tag found.")

# Check for text "No results found"
text = soup.get_text().lower()
if "no results found" in text:
    results.append("Text 'No results found' IS present in the page.")
else:
    results.append("Text 'No results found' is NOT present.")

with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))
