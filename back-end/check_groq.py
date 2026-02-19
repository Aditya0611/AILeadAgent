import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print(f"Groq Key Present: {bool(api_key)}")

client = Groq(api_key=api_key)

models_to_try = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192"
]

for model in models_to_try:
    print(f"\nTesting: {model}...")
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hi"}],
            model=model,
        )
        print(f"✅ Success with {model}")
        break
    except Exception as e:
        print(f"❌ Failed: {e}")
