import google.generativeai as genai
import os

api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyCw1q1cUo7enX0S3NMAdPKkKNMr1yVFf9A')
genai.configure(api_key=api_key)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
