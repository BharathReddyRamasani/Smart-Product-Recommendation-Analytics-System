import os
from typing import List, Dict, Any, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain.chains.combine_documents import create_stuff_documents_chain
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
import chromadb

import requests
from langchain_core.embeddings import Embeddings

class RESTGeminiEmbeddings(Embeddings):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={self.api_key}"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # For our RAG Service, we only need query embedding at runtime
        return [self.embed_query(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        response = requests.post(
            self.url,
            headers={"Content-Type": "application/json"},
            json={"model": "models/gemini-embedding-001", "content": {"parts": [{"text": text}]}},
            timeout=10
        )
        if response.status_code != 200:
            raise Exception(f"Gemini API Error: {response.text}")
        return response.json()["embedding"]["values"]

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

class RESTGeminiChat(BaseChatModel):
    api_key: str
    model: str = "gemini-2.5-flash"
    temperature: float = 0.7

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        # Convert Langchain messages to Gemini API format
        gemini_messages = []
        for m in messages:
            role = "user" if m.type in ["human", "system", "user"] else "model"
            gemini_messages.append({"role": role, "parts": [{"text": m.content}]})

        payload = {
            "contents": gemini_messages,
            "generationConfig": {"temperature": self.temperature}
        }

        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=20)
        if response.status_code != 200:
            raise Exception(f"Gemini API Error: {response.text}")
            
        data = response.json()
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            content = "I'm sorry, but I couldn't process the response."
            
        message = AIMessage(content=content)
        return ChatResult(generations=[ChatGeneration(message=message)])

    @property
    def _llm_type(self) -> str:
        return "rest-gemini-chat"

class RAGService:
    def __init__(self):
        # We assume the ChromaDB client persists in the backend directory where we run the server
        # So the path must be relative to where main.py runs or an absolute path
        # Assuming the backend directory is the working directory:
        from chromadb.config import Settings
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db", settings=Settings(anonymized_telemetry=False))
        
        try:
            self.collection = self.chroma_client.get_collection("product_catalog")
        except Exception as e:
            # Collection might not exist yet if vectorization hasn't run
            self.collection = None
            print(f"Warning: RAGService couldn't load 'product_catalog' collection. {e}")

        api_key = os.getenv("GEMINI_API_KEY", "")
        self.embeddings = RESTGeminiEmbeddings(api_key=api_key)
        self.llm = RESTGeminiChat(
            api_key=api_key,
            model="gemini-2.5-flash", 
            temperature=0.7
        )
        
        # Setup the conversation prompt
        self.prompt = PromptTemplate.from_template(
            template="""You are a helpful, expert AI shopping assistant for our e-commerce store.
Your goal is to recommend the best products based on the user's request and provide a personalized explanation.

Context (Relevant Products from our Catalog):
{context}

User Query: {query}

Instructions:
1. Recommend the most suitable products from the context.
2. Explain WHY these products are a good fit for the user based on their query.
3. If the context does not contain relevant products, kindly apologize and say we don't have exactly what they are looking for, but suggest alternatives if possible.
4. Keep the tone conversational, friendly, and helpful.
5. CRITICAL: If the user's query contains explicit, inappropriate, NSFW topics, or is wildly irrelevant to our store's products (e.g. asking for adult content), you MUST strictly refuse to fulfill the request. Reply ONLY with: "I'm sorry, but I can only assist you with finding items from our store catalog, such as electronics, clothing, and books." Do not suggest any products in this case.

Response:"""
        )

    def retrieve_products(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve the most relevant products from ChromaDB based on the query."""
        if not self.collection:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        retrieved_products = []
        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            for i in range(len(results['metadatas'][0])):
                product = results['metadatas'][0][i]
                # we also have the text document in results['documents'][0][i]
                product['document'] = results['documents'][0][i]
                retrieved_products.append(product)
                
        return retrieved_products

    def generate_response(self, query: str, context_products: List[Dict[str, Any]]) -> str:
        """Generate a conversational response using Gemini."""
        if not context_products:
            return "I couldn't find any products in our catalog that match your request. Is there anything else you are looking for?"
            
        # Convert context products back to LangChain Documents for the chain
        docs = [Document(page_content=p.get('document', str(p)), metadata=p) for p in context_products]
        
        # Create stuff documents chain
        chain = create_stuff_documents_chain(self.llm, self.prompt)
        
        # Run the chain
        response = chain.invoke({"context": docs, "query": query})
        
        # Ensure we return a plain string to avoid Pydantic serializing objects to JSON
        if isinstance(response, dict):
            return response.get("output_text", str(response))
        if hasattr(response, "content"):
            return str(response.content)
        return str(response)

# Instantiate a singleton to use across routes
rag_service = RAGService()
