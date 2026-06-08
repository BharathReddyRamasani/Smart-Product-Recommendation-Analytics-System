import os
import requests
from dotenv import load_dotenv

def list_models():
    load_dotenv("../../backend/.env")
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=20)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        for m in data.get("models", []):
            print(m["name"])
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    list_models()
