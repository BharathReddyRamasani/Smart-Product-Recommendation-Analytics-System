import os
import requests
from dotenv import load_dotenv

def test_rest_chat():
    load_dotenv("../../backend/.env")
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Hello, how are you?"}]}],
        "generationConfig": {"temperature": 0.7}
    }
    print(f"Testing URL: {url}")
    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=20)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_rest_chat()
