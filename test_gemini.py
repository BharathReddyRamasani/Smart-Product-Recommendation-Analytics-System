import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "backend", ".env"))
API_KEY = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:batchEmbedContents?key={API_KEY}"
requests_payload = [
    {"model": "models/text-embedding-004", "content": {"parts": [{"text": f"Test {i}"}]}}
    for i in range(50)
]

response = requests.post(
    url,
    headers={"Content-Type": "application/json"},
    json={"requests": requests_payload}
)

print("Status Code:", response.status_code)
if response.status_code == 200:
    print("Success! text-embedding-004 batchEmbedContents works.")
else:
    print("Response:", response.text)
