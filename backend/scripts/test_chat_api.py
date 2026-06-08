import requests

def test_chat():
    url = "http://localhost:8000/api/v1/chat/"
    payload = {
        "query": "laptop",
        "user_id": "test_user_id"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_chat()
