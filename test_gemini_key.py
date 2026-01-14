import google.generativeai as genai
import os

api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyCw1q1cUo7enX0S3NMAdPKkKNMr1yVFf9A')
print(f"Testing API Key: {api_key}")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello, can you hear me?")
    print("Success!")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
