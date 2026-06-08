import os
import sys
import time
import requests
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import connect_to_mongo, close_mongo

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: GEMINI_API_KEY is not set in the environment.")
    sys.exit(1)

import chromadb
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

def get_embeddings(texts: list) -> list:
    """Get embeddings using direct REST API batchEmbedContents to avoid rate limits."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    requests_payload = [
        {"model": "models/gemini-embedding-001", "content": {"parts": [{"text": text}]}}
        for text in texts
    ]
    
    data = {"requests": requests_payload}
    
    for _ in range(5): # Retry 5 times
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 429:
                print("429 Too Many Requests. Sleeping for 60 seconds...")
                time.sleep(60)
                continue
            response.raise_for_status()
            return [res["values"] for res in response.json()["embeddings"]]
        except Exception as e:
            print(f"Embedding error: {e}. Retrying...")
            time.sleep(5)
            
    raise Exception("Failed to get embeddings after 5 retries.")


def vectorize_catalog():
    print("Connecting to MongoDB...")
    db = connect_to_mongo()
    
    products = list(db.products.find({}))
    print(f"Found {len(products)} products in MongoDB.")
    
    if not products:
        print("No products found. Please seed the database first.")
        close_mongo()
        return

    print("Initializing ChromaDB...")
    from chromadb.config import Settings
    chroma_db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
    chroma_client = chromadb.PersistentClient(path=chroma_db_dir, settings=Settings(anonymized_telemetry=False))
    
    try:
        chroma_client.delete_collection(name="product_catalog")
        print("Deleted existing 'product_catalog' collection.")
    except Exception:
        pass
        
    collection = chroma_client.create_collection(name="product_catalog")
    print("Created 'product_catalog' collection.")

    docs = []
    metadatas = []
    ids = []

    print("Preparing product data for vectorization...")
    for prod in products:
        features_str = ", ".join(prod.get("features", []))
        text_content = (
            f"Product Name: {prod.get('name')}\n"
            f"Brand: {prod.get('brand')}\n"
            f"Category: {prod.get('category')}\n"
            f"Price: ${prod.get('price')}\n"
            f"Description: {prod.get('description')}\n"
            f"Features: {features_str}"
        )
        docs.append(text_content)
        
        metadatas.append({
            "mongo_id": str(prod.get("_id")),
            "name": str(prod.get("name")),
            "category": str(prod.get("category")),
            "brand": str(prod.get("brand")),
            "price": float(prod.get("price")),
            "rating": float(prod.get("rating", 0))
        })
        ids.append(str(prod.get("_id")))

    print(f"Embedding {len(docs)} products via Gemini REST API in batches...")
    
    all_embeddings = []
    batch_size = 50
    
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(docs) + batch_size - 1)//batch_size} (products {i+1} to {min(i+batch_size, len(docs))})...")
        embeddings = get_embeddings(batch_docs)
        all_embeddings.extend(embeddings)
        time.sleep(2) # Avoid hitting minute limits too quickly
        
    print("Storing embeddings in ChromaDB...")
    
    # ChromaDB add has a batch limit too, but usually it's ~100-5000. Let's do batches of 100
    for i in range(0, len(docs), 100):
        collection.add(
            documents=docs[i:i+100],
            embeddings=all_embeddings[i:i+100],
            metadatas=metadatas[i:i+100],
            ids=ids[i:i+100]
        )
    
    print("Successfully vectorized and stored the product catalog in ChromaDB!")
    close_mongo()

if __name__ == "__main__":
    vectorize_catalog()
