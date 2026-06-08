"""
Products routes — PUBLIC (no JWT required for browse/detail).
Authenticated users also log view interactions automatically.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from pymongo.database import Database
from typing import Optional
from app.utils.database import get_db, mongo_id, mongo_ids
from app.schemas.schemas import ProductResponse
from app.utils.logger import get_logger
import re

logger = get_logger(__name__)
router = APIRouter(prefix="/products", tags=["Products"])

VALID_CATEGORIES = [
    "Electronics", "Books", "Clothing", "Home & Kitchen",
    "Sports & Outdoors", "Beauty & Personal Care",
    "Mobiles", "Laptops", "Clothes", "Shoes", "Watches", "Bags", "Toys"
]


def _to_product_response(doc: dict) -> ProductResponse:
    d = mongo_id(dict(doc))
    if isinstance(d.get("features"), str):
        d["features"] = [f.strip() for f in d["features"].split(",") if f.strip()]
    return ProductResponse(**d)


@router.get("", response_model=list[ProductResponse])
def list_products(
    search: Optional[str] = Query(None, description="Text search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=1000),
    db: Database = Depends(get_db),
):
    """
    Browse products with optional search, category filter, and price range.
    Public endpoint — no authentication required.
    """
    query: dict = {}
    if search:
        regex = re.compile(search, re.IGNORECASE)
        query["$or"] = [
            {"name": {"$regex": regex}},
            {"description": {"$regex": regex}},
            {"features": {"$regex": regex}},
            {"brand": {"$regex": regex}},
        ]
    if category and category in VALID_CATEGORIES:
        query["category"] = category
    if min_price is not None:
        query.setdefault("price", {})["$gte"] = min_price
    if max_price is not None:
        query.setdefault("price", {})["$lte"] = max_price

    docs = list(db.products.find(query).skip(skip).limit(limit))
    return [_to_product_response(d) for d in docs]


@router.get("/popular", response_model=list[ProductResponse])
def popular_products(
    k: int = Query(12, ge=1, le=50),
    category: Optional[str] = Query(None),
    db: Database = Depends(get_db),
):
    """
    Returns globally popular products ranked by weighted interaction score.
    Popularity = sum(view*1 + add_to_cart*3 + purchase*5) per product.
    Public endpoint.
    """
    weights = {"view": 1, "add_to_cart": 3, "purchase": 5}
    pipeline = [
        {"$group": {
            "_id": "$product_id",
            "score": {"$sum": {
                "$switch": {
                    "branches": [
                        {"case": {"$eq": ["$interaction_type", "view"]}, "then": 1},
                        {"case": {"$eq": ["$interaction_type", "add_to_cart"]}, "then": 3},
                        {"case": {"$eq": ["$interaction_type", "purchase"]}, "then": 5},
                    ],
                    "default": 1,
                }
            }}
        }},
        {"$sort": {"score": -1}},
        {"$limit": k * 3},  # Fetch extra so we can filter by category
    ]
    popular_ids_scores = {r["_id"]: r["score"] for r in db.interactions.aggregate(pipeline)}

    product_filter: dict = {"_id": {"$in": [ObjectId(pid) for pid in popular_ids_scores if _is_valid_id(pid)]}}
    if category and category in VALID_CATEGORIES:
        product_filter["category"] = category

    docs = list(db.products.find(product_filter).limit(k))
    return [_to_product_response(d) for d in docs]


@router.get("/categories", response_model=list[str])
def get_categories():
    """Return all supported product categories. Public."""
    return VALID_CATEGORIES


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Database = Depends(get_db)):
    """
    Get a single product by ID. Public endpoint.
    The frontend logs a 'view' interaction separately via POST /interaction.
    """
    if not _is_valid_id(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    doc = db.products.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return _to_product_response(doc)


def _is_valid_id(oid: str) -> bool:
    try:
        ObjectId(oid)
        return True
    except Exception:
        return False
