import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing available models...")
try:
    with open('models.log', 'w') as f:
        for model in client.models.list():
            if "flash" in model.name:
                print(f"Model: {model.name}")
                f.write(f"Model: {model.name}\n")
    print("Done writing to models.log")
except Exception as e:
    print(f"Error listing models: {e}")
