import os
import sys

print(f"Python version: {sys.version}")

try:
    import google.generativeai as genai
    print("google.generativeai is installed.")
except ImportError:
    print("google.generativeai is NOT installed.")

api_key = os.environ.get('GEMINI_API_KEY')
if api_key:
    print(f"GEMINI_API_KEY is set: {api_key[:5]}...")
else:
    print("GEMINI_API_KEY is NOT set.")
