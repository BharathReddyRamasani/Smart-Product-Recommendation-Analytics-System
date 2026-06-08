import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

def test_chat():
    load_dotenv("../../backend/.env")
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.7,
            google_api_key=os.getenv("GEMINI_API_KEY"),
            transport="rest"
        )
        res = llm.invoke("Hello!")
        print(f"Success with transport='rest': {res}")
    except Exception as e:
        print(f"Error with transport='rest': {e}")
        
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.7,
            google_api_key=os.getenv("GEMINI_API_KEY"),
            client_options={"transport": "rest"}
        )
        res = llm.invoke("Hello!")
        print(f"Success with client_options: {res}")
    except Exception as e:
        print(f"Error with client_options: {e}")

if __name__ == "__main__":
    test_chat()
