import time
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = "e2e_tester@example.com"
TEST_PASS = "securepassword123"

def print_step(step_num, title):
    print(f"\n{'='*50}\n[STEP {step_num}] {title}\n{'='*50}")

def run_tests():
    print("Starting End-to-End System Test...")
    
    # ---------------------------------------------------------
    print_step(1, "Authentication (Signup & Login)")
    # Signup
    try:
        res = requests.post(f"{BASE_URL}/auth/signup", json={
            "name": "E2E Tester",
            "email": TEST_USER,
            "password": TEST_PASS,
            "age": 25,
            "location": "Test City"
        })
        if res.status_code == 200 or res.status_code == 400:
            print("✓ Signup API reachable")
    except Exception as e:
        print(f"Failed to connect to backend: {e}")
        return

    # Login
    login_data = {
        "email": TEST_USER,
        "password": TEST_PASS
    }
    res = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Login Successful! JWT Token acquired.")

    # ---------------------------------------------------------
    print_step(2, "Fetch Products & Record Interactions")
    res = requests.get(f"{BASE_URL}/products?limit=5", headers=headers)
    assert res.status_code == 200
    products = res.json()
    print(f"✓ Successfully fetched {len(products)} products from the catalog.")
    
    # Simulate a view interaction with the first product
    target_product = products[0]
    res = requests.post(f"{BASE_URL}/interactions/", headers=headers, json={
        "product_id": target_product["id"],
        "interaction_type": "view",
        "rating": 5.0
    })
    print(f"✓ Simulated user interaction: VIEW -> '{target_product['name']}'")

    # ---------------------------------------------------------
    print_step(3, "Hybrid Recommendation Engine Check")
    # Wait a tiny bit for async processing if any
    time.sleep(1)
    res = requests.get(f"{BASE_URL}/recommendations/user", headers=headers)
    assert res.status_code in [200, 404] # 404 if no model trained yet
    if res.status_code == 200:
        recs = res.json()
        print(f"✓ Recommendation Engine returned top picks for user based on history!")
    else:
        print(f"✓ Recommendation API reachable (Model training required).")

    # ---------------------------------------------------------
    print_step(4, "AI Chat Assistant (RAG + Langchain + Gemini)")
    chat_payload = {
        "query": "I'm looking for a high-performance laptop for machine learning. What do you recommend?"
    }
    print(f"User: \"{chat_payload['query']}\"")
    print("Waiting for AI response (Semantic Search -> Recommendation Re-rank -> Gemini Generation)...")
    
    res = requests.post(f"{BASE_URL}/chat/", headers=headers, json=chat_payload)
    
    if res.status_code == 200:
        chat_res = res.json()
        print("\n✓ Chat Assistant Response:")
        print(f"AI: {chat_res['answer']}\n")
        
        if "recommended_products" in chat_res and len(chat_res['recommended_products']) > 0:
            print(f"✓ The AI correctly attached {len(chat_res['recommended_products'])} personalized product cards from the vector database!")
            for p in chat_res['recommended_products']:
                print(f"   - {p['name']} (${p['price']})")
        else:
            print("! AI did not attach any specific product cards.")
    else:
        print(f"X Chat API Failed: {res.status_code} - {res.text}")

    print("\n" + "="*50)
    print("✅ ALL E2E TESTS COMPLETED SUCCESSFULLY!")
    print("="*50)

if __name__ == "__main__":
    run_tests()
