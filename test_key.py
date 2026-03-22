import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv('c:\\Users\\Shannu\\Downloads\\ai-codebase-assistant (3)\\ai-codebase-assistant\\.env', override=True)
api_key = os.environ.get('GEMINI_API_KEY')
print(f"Testing key: {api_key[:10]}...")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')
try:
    response = model.generate_content("Hello")
    print("Success:", response.text)
except Exception as e:
    print("Error:", e)
