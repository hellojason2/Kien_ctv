import google.generativeai as genai
import os

api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyCw1q1cUo7enX0S3NMAdPKkKNMr1yVFf9A')
genai.configure(api_key=api_key)

model_name = 'gemini-2.0-flash'
print(f"Testing model: {model_name}")

try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hello")
    print("Success!")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
