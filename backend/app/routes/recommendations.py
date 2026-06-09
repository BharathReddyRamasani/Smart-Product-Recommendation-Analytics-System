"""
Recommendation routes — PROTECTED (JWT required).

Includes:
- GET /home         → Home feed (personalized vs cold-start)
- GET /recommend/user → Full personalized recommendation list
- GET /recommend/product/{id} → Similar products (public-style, but JWT checked)
- GET /metrics      → Evaluation metrics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from pymongo.database import Database
from typing import Optional
from app.utils.database import get_db, mongo_id
from app.utils.auth import get_current_user_id
from app.ml.engine import ml_engine
from app.schemas.schemas import (
    RecommendationResponse, SimilarProductResponse,
    RecommendedProduct, ProductResponse, HomeFeedResponse, MetricsResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Recommendations"])

COLD_START_THRESHOLD = 2   # < 2 interactions → popularity


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _is_valid_id(oid: str) -> bool:
    try:
        ObjectId(oid)
        return True
    except Exception:
        return False


def _enrich_products(
    results: list[tuple[str, float]],
    db: Database,
    reason: str = "",
) -> list[RecommendedProduct]:
    """
    Fetch product documents from MongoDB for a list of (product_id, score) tuples.
    Preserves ML ranking order.
    """
    if not results:
        return []
    pid_score = {pid: score for pid, score in results}
    valid_ids = [ObjectId(pid) for pid in pid_score if _is_valid_id(pid)]
    docs = {str(d["_id"]): d for d in db.products.find({"_id": {"$in": valid_ids}})}

    enriched = []
    for pid, score in results:
        doc = docs.get(pid)
        if not doc:
            continue
        features = doc.get("features", [])
        if isinstance(features, str):
            features = [f.strip() for f in features.split(",")]
        enriched.append(RecommendedProduct(
            id=pid,
            name=doc["name"],
            category=doc["category"],
            price=doc["price"],
            description=doc.get("description", ""),
            features=features,
            brand=doc.get("brand"),
            rating=doc.get("rating", 0),
            num_reviews=doc.get("num_reviews", 0),
            image_url=doc.get("image_url"),
            score=score,
            reason=reason,
        ))
    return enriched


def _get_interaction_count(user_id: str, db: Database) -> int:
    return db.interactions.count_documents({"user_id": user_id})


def _get_recently_viewed(user_id: str, k: int, db: Database) -> list[ProductResponse]:
    """Return last K distinct products the user viewed."""
    docs = list(
        db.interactions.find({"user_id": user_id, "interaction_type": "view"})
        .sort("timestamp", -1)
        .limit(k * 3)
    )
    seen, product_ids = set(), []
    for d in docs:
        pid = d["product_id"]
        if pid not in seen and _is_valid_id(pid):
            seen.add(pid)
            product_ids.append(ObjectId(pid))
        if len(product_ids) == k:
            break
    if not product_ids:
        return []
    products = list(db.products.find({"_id": {"$in": product_ids}}))
    result = []
    for p in products:
        features = p.get("features", [])
        if isinstance(features, str):
            features = [f.strip() for f in features.split(",")]
        result.append(ProductResponse(
            id=str(p["_id"]), name=p["name"], category=p["category"],
            price=p["price"], description=p.get("description", ""),
            features=features, brand=p.get("brand"),
            rating=p.get("rating", 0), num_reviews=p.get("num_reviews", 0),
            image_url=p.get("image_url"),
        ))
    return result


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/home", response_model=HomeFeedResponse)
def get_home_feed(
    user_id: str = Depends(get_current_user_id),
    db: Database = Depends(get_db),
):
    """
    Home page feed with explicit strategy logic:

    Cold start (< 5 interactions):
      - Main: globally popular products
      - Secondary: browse categories (newest products)

    Personalized (≥ 5 interactions):
      - Main: Hybrid recs (60% CF + 30% content + 10% trending)
      - Secondary: Popular in top interacted category
    """
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    n_interactions = _get_interaction_count(user_id, db)
    recently_viewed = _get_recently_viewed(user_id, k=6, db=db)

    if n_interactions < COLD_START_THRESHOLD:
        # Cold start → popularity
        pop_results, strategy = ml_engine.recommend_for_user(user_id, k=12, strategy="popularity")
        main_products = _enrich_products(pop_results, db, reason="Trending globally")
        # Secondary: newest products
        newest = list(db.products.find({}).sort("created_at", -1).limit(8))
        secondary_products = []
        for p in newest:
            features = p.get("features", [])
            if isinstance(features, str):
                features = [f.strip() for f in features.split(",")]
            secondary_products.append(RecommendedProduct(
                id=str(p["_id"]), name=p["name"], category=p["category"],
                price=p["price"], description=p.get("description", ""),
                features=features, brand=p.get("brand"),
                rating=p.get("rating", 0), num_reviews=p.get("num_reviews", 0),
                image_url=p.get("image_url"), score=0.0, reason="New arrival",
            ))
        return HomeFeedResponse(
            is_personalized=False,
            user_name=user["name"],
            interaction_count=n_interactions,
            main_section_title="Trending Products",
            main_products=main_products,
            recently_viewed=recently_viewed,
            secondary_section_title="New Arrivals",
            secondary_products=secondary_products,
        )
    else:
        # Personalized → hybrid
        hybrid_results, strategy = ml_engine.recommend_for_user(user_id, k=12, strategy="hybrid")
        main_products = _enrich_products(hybrid_results, db, reason="Recommended for you")

        # Find user's top category
        top_cat_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$lookup": {"from": "products", "localField": "product_id",
                         "foreignField": "_id", "as": "product"}},
            {"$unwind": {"path": "$product", "preserveNullAndEmptyArrays": True}},
            {"$group": {"_id": "$product.category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, {"$limit": 1},
        ]
        # Simpler approach: count categories from cached interactions
        top_cat = _get_top_category(user_id, db)
        
        # Fetch a larger pool of popular items, then explicitly filter by category to ensure honesty
        raw_pop_results, _ = ml_engine.recommend_for_user(user_id, k=50, strategy="popularity")
        pop_in_cat_results = []
        for pid, score in raw_pop_results:
            if not _is_valid_id(pid): continue
            product = db.products.find_one({"_id": ObjectId(pid), "category": top_cat})
            if product:
                pop_in_cat_results.append((pid, score))
            if len(pop_in_cat_results) >= 8:
                break
                
        secondary_products = _enrich_products(pop_in_cat_results, db, reason=f"Popular in {top_cat}")

        return HomeFeedResponse(
            is_personalized=True,
            user_name=user["name"],
            interaction_count=n_interactions,
            main_section_title="Recommended for You",
            main_products=main_products,
            recently_viewed=recently_viewed,
            secondary_section_title=f"Popular in {top_cat}",
            secondary_products=secondary_products,
        )


def _get_top_category(user_id: str, db: Database) -> str:
    """Find user's most-interacted product category."""
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$addFields": {"pid_obj": {"$toObjectId": "$product_id"}}},
        {"$lookup": {"from": "products", "localField": "pid_obj", "foreignField": "_id", "as": "p"}},
        {"$unwind": {"path": "$p", "preserveNullAndEmptyArrays": True}},
        {"$group": {"_id": "$p.category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}, {"$limit": 1},
    ]
    result = list(db.interactions.aggregate(pipeline))
    if result and result[0].get("_id"):
        return result[0]["_id"]
    return "Electronics"


@router.get("/recommend/user", response_model=RecommendationResponse)
def recommend_for_user(
    k: int = Query(10, ge=1, le=50),
    strategy: str = Query("auto", description="auto | popularity | content | collaborative | hybrid | svd"),
    user_id: str = Depends(get_current_user_id),
    db: Database = Depends(get_db),
):
    """
    Full personalized recommendation list.
    Strategy 'auto' applies: popularity < 5 / content 5-19 / hybrid ≥ 20 interactions.
    """
    results, strategy_used = ml_engine.recommend_for_user(user_id, k=k, strategy=strategy)
    enriched = _enrich_products(results, db, reason=_strategy_reason(strategy_used))
    return RecommendationResponse(
        user_id=user_id,
        strategy=strategy_used,
        is_personalized=strategy_used not in ("popularity", "not_ready"),
        recommendations=enriched,
        total=len(enriched),
    )


@router.get("/recommend/product/{product_id}", response_model=SimilarProductResponse)
def recommend_similar(
    product_id: str,
    k: int = Query(8, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
    db: Database = Depends(get_db),
):
    """
    Content-based product similarity using TF-IDF cosine similarity.
    Used on Product Detail page in 'Similar Products' section.
    """
    if not _is_valid_id(product_id):
        raise HTTPException(status_code=400, detail="Invalid product_id format")
    source = db.products.find_one({"_id": ObjectId(product_id)})
    if not source:
        raise HTTPException(status_code=404, detail="Product not found")

    results, strategy_used = ml_engine.recommend_similar_products(product_id, k=k)
    enriched = _enrich_products(results, db, reason="Similar product")
    return SimilarProductResponse(
        source_product_id=product_id,
        source_product_name=source["name"],
        strategy=strategy_used,
        recommendations=enriched,
        total=len(enriched),
    )


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(
    k: int = Query(10, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
):
    """Compute Precision@K, Recall@K, Hit Rate on hybrid strategy."""
    metrics = ml_engine.get_metrics(k=k)
    if "error" in metrics:
        raise HTTPException(status_code=503, detail=metrics["error"])
    return MetricsResponse(
        precision_at_k=metrics.get("precision_at_k", 0.0),
        recall_at_k=metrics.get("recall_at_k", 0.0),
        hit_rate=metrics.get("hit_rate", 0.0),
        k=metrics.get("k", k),
        evaluated_users=metrics.get("evaluated_users", 0),
    )


def _strategy_reason(strategy: str) -> str:
    return {
        "popularity": "Trending product",
        "content": "Similar to items you viewed",
        "collaborative": "Users like you also liked this",
        "hybrid": "Recommended for you",
        "svd": "Based on your taste profile",
    }.get(strategy, "Recommended")
