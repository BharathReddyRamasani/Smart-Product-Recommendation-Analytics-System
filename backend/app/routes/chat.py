from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import time

from app.services.rag_service import rag_service
from app.utils.auth import get_current_user_id
from app.utils.database import get_db
from app.ml.engine import ml_engine
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat Assistant"])

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    recommended_products: List[dict]
    session_id: Optional[str] = None

@router.post("/", response_model=ChatResponse)
def handle_chat(request: ChatRequest, current_user_id: str = Depends(get_current_user_id)):
    """
    Handle user chat queries for the AI Shopping Assistant.
    Integrates RAG (ChromaDB + Gemini) with the Hybrid Recommendation Engine.
    """
    try:
        user_id = current_user_id
        db = get_db()
        
        # 1. Retrieve products semantically using RAG Service
        # We retrieve slightly more to allow the recommendation engine to re-rank
        retrieved_products = rag_service.retrieve_products(request.query, top_k=10)
        
        if not retrieved_products:
            return ChatResponse(
                answer="I couldn't find any products matching your query. Please try searching for something else.",
                recommended_products=[]
            )
            
        # 2. Re-rank or fuse context with ML recommendations
        user_recommendations, _ = ml_engine.recommend_for_user(user_id=user_id, k=50)
        
        # Map user's personalized recommendation scores
        rec_scores = {str(pid): score for pid, score in user_recommendations}
        
        # Sort retrieved products by combining semantic relevance (implicit in retrieval order) 
        # and the user's personal recommendation score.
        # This is a simple fusion strategy:
        for i, prod in enumerate(retrieved_products):
            pid = prod["mongo_id"]
            # Base semantic score (higher index = lower score)
            semantic_score = 10 - i 
            personal_score = rec_scores.get(pid, 0)
            
            # Combined score: weight personal score slightly higher if it exists
            prod["fusion_score"] = semantic_score + (personal_score * 5)
            
        # Sort by the new fusion score and take top 5
        final_products = sorted(retrieved_products, key=lambda x: x["fusion_score"], reverse=True)[:5]
        
        # 3. Generate response with Gemini
        answer = rag_service.generate_response(request.query, final_products)
        
        # 4. Save to chat history (optional, if we want to store it in MongoDB)
        chat_entry = {
            "user_id": user_id,
            "session_id": request.session_id,
            "query": request.query,
            "answer": answer,
            "recommended_product_ids": [p["mongo_id"] for p in final_products],
            "timestamp": time.time()
        }
        db.chat_sessions.insert_one(chat_entry)
        
        # 5. Return the response
        return ChatResponse(
            answer=answer,
            recommended_products=final_products,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error in chat handler: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")
