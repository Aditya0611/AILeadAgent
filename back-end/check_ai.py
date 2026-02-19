import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key present: {bool(api_key)}")

client = genai.Client(api_key=api_key)

models_to_try = [
    "gemini-1.5-flash", 
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro",
    "models/gemini-1.5-flash"
]

for model_name in models_to_try:
    print(f"\nTesting model: {model_name}...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Say hello"
        )
        print(f"✅ SUCCESS! Response: {response.text.strip()}")
        break # Stop on first success
    except Exception as e:
        print(f"❌ FAILED: {e}")
