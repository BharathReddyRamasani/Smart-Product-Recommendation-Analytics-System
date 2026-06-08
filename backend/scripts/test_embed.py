import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def test_embed():
    load_dotenv("backend/.env")
    api_key = os.getenv("GEMINI_API_KEY")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2",
            google_api_key=api_key,
            transport="rest"
        )
        res = embeddings.embed_query("Hello world")
        print(f"Success with rest transport! Length: {len(res)}")
    except Exception as e:
        print(f"Error with transport='rest': {e}")
        
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2",
            google_api_key=api_key,
            client_options={"transport": "rest"}
        )
        res = embeddings.embed_query("Hello world")
        print(f"Success with client_options! Length: {len(res)}")
    except Exception as e:
        print(f"Error with client_options: {e}")

if __name__ == "__main__":
    test_embed()
