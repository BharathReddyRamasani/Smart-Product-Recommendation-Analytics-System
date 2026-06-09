"""
ML Engine — Central orchestrator with explicit hybrid recommendation strategy.

Strategy Selection Logic:
  - User has < 5 interactions  → Popularity-based (cold start)
  - User has 5-19 interactions → Content-based (similar to viewed items)
  - User has ≥ 20 interactions → Hybrid:
        60% Collaborative Filtering (user-user similarity)
        30% Content-Based (TF-IDF on interacted items)
        10% Trending (popularity)

Products are weighted by interaction strength:
  view=1, add_to_cart=3, purchase=5
"""
import threading
from collections import defaultdict
from typing import List, Tuple
from app.ml.popularity import PopularityRecommender
from app.ml.content_based import ContentBasedRecommender
from app.ml.collaborative import CollaborativeFilteringRecommender
from app.ml.matrix_factorization import SVDRecommender
from app.ml.metrics import evaluate_recommendations
from app.utils.logger import get_logger

logger = get_logger(__name__)

COLD_START_THRESHOLD = 2      # < 2 → popularity
CONTENT_THRESHOLD = 10        # 2-9 → content-based
# ≥ 20 → hybrid (60% CF + 30% content + 10% trending)

HYBRID_CF_WEIGHT = 0.20
HYBRID_SVD_WEIGHT = 0.30
HYBRID_CONTENT_WEIGHT = 0.40
HYBRID_TRENDING_WEIGHT = 0.10

INTERACTION_WEIGHTS = {"view": 1, "add_to_cart": 3, "purchase": 5}


class MLEngine:
    """Thread-safe ML engine orchestrator with explicit hybrid strategy."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._popularity = PopularityRecommender()
        self._content_based = ContentBasedRecommender()
        self._collaborative = CollaborativeFilteringRecommender()
        self._svd = SVDRecommender(n_factors=20)
        self._is_ready: bool = False
        self._interactions_cache: list[dict] = []
        self._products_cache: list[dict] = []
        self._interactions_since_last_fit: int = 0
        self._BATCH_RETRAIN_THRESHOLD: int = 10
        self._retraining: bool = False

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def fit(self, db) -> None:
        """
        Load data from MongoDB and train all models.
        Products features are stored as lists in MongoDB.
        """
        with self._lock:
            logger.info("MLEngine: Starting model training from MongoDB...")

            products = list(db.products.find({}))
            interactions = list(db.interactions.find({}))

            if not products:
                logger.warning("MLEngine: No products found. Skipping fit.")
                return

            # Serialize for ML modules (convert ObjectId → str, features list → space-joined)
            product_dicts = []
            for p in products:
                features = p.get("features", [])
                features_str = " ".join(features) if isinstance(features, list) else str(features)
                product_dicts.append({
                    "id": str(p["_id"]),
                    "name": p.get("name", ""),
                    "category": p.get("category", ""),
                    "description": p.get("description", ""),
                    "features": features_str,
                    "brand": p.get("brand", ""),
                    "price": p.get("price", 0),
                    "rating": p.get("rating", 0),
                })

            interaction_dicts = []
            for i in interactions:
                interaction_dicts.append({
                    "user_id": str(i["user_id"]),
                    "product_id": str(i["product_id"]),
                    "interaction_type": i.get("interaction_type", "view"),
                    "rating": i.get("rating"),
                    "timestamp": i.get("timestamp"),
                })

            self._products_cache = product_dicts
            self._interactions_cache = interaction_dicts

            self._popularity.fit(interaction_dicts)
            self._content_based.fit(product_dicts)
            self._collaborative.fit(interaction_dicts)
            self._svd.fit(interaction_dicts)

            self._is_ready = True
            logger.info(
                f"MLEngine: Ready — {len(products)} products, "
                f"{len(interactions)} interactions"
            )

    def add_interaction(self, user_id: str, product_id: str, interaction_type: str, rating: float = None, timestamp: str = None) -> None:
        """Dynamically add an interaction to the cache and update models in real-time."""
        with self._lock:
            record = {
                "user_id": user_id,
                "product_id": product_id,
                "interaction_type": interaction_type,
                "rating": rating,
                "timestamp": timestamp,
            }
            self._interactions_cache.append(record)
            self._popularity.add_interaction(record)
            
            self._interactions_since_last_fit += 1
            if self._interactions_since_last_fit >= self._BATCH_RETRAIN_THRESHOLD:
                if not self._retraining:
                    self._interactions_since_last_fit = 0
                    self._retraining = True
                    logger.info(f"MLEngine: Threshold reached, kicking off batch retrain of collaborative models.")
                    threading.Thread(target=self._batch_recompute, daemon=True).start()
                
            logger.debug(f"MLEngine: Added real-time interaction {interaction_type} for {user_id} on {product_id}")

    def _batch_recompute(self) -> None:
        """Background thread to recompute heavy models on a batch schedule."""
        try:
            from app.utils.database import get_db
            db = get_db()
            if not db:
                logger.error("MLEngine: No DB connection available for batch recompute.")
                return

            products = list(db.products.find({}))
            interactions = list(db.interactions.find({}))

            product_dicts = []
            for p in products:
                features = p.get("features", [])
                features_str = " ".join(features) if isinstance(features, list) else str(features)
                product_dicts.append({
                    "id": str(p["_id"]),
                    "name": p.get("name", ""),
                    "category": p.get("category", ""),
                    "description": p.get("description", ""),
                    "features": features_str,
                    "brand": p.get("brand", ""),
                    "price": p.get("price", 0),
                    "rating": p.get("rating", 0),
                })

            interaction_dicts = []
            for i in interactions:
                interaction_dicts.append({
                    "user_id": str(i["user_id"]),
                    "product_id": str(i["product_id"]),
                    "interaction_type": i.get("interaction_type", "view"),
                    "rating": i.get("rating"),
                    "timestamp": i.get("timestamp"),
                })

            # Train new instances to avoid blocking during heavy computation
            new_content_based = ContentBasedRecommender().fit(product_dicts)
            new_collaborative = CollaborativeFilteringRecommender().fit(interaction_dicts)
            new_svd = SVDRecommender(n_factors=20).fit(interaction_dicts)
            new_popularity = PopularityRecommender().fit(interaction_dicts)

            with self._lock:
                self._products_cache = product_dicts
                self._interactions_cache = interaction_dicts
                self._content_based = new_content_based
                self._collaborative = new_collaborative
                self._svd = new_svd
                self._popularity = new_popularity
                
            logger.info("MLEngine: Dynamic batch recompute and model swap completed successfully.")
        except Exception as e:
            logger.error(f"MLEngine: Batch recompute failed: {e}")
        finally:
            with self._lock:
                self._retraining = False

    def _interaction_count(self, user_id: str) -> int:
        return sum(1 for r in self._interactions_cache if r["user_id"] == user_id)

    def _interacted_products(self, user_id: str) -> list[str]:
        """Return product IDs interacted by user, chronologically ordered (most recent first)."""
        records = [r for r in self._interactions_cache if r["user_id"] == user_id]
        # Sort purely by timestamp desc, ensuring [:5] gets the absolute most recent items
        def get_ts_str(x):
            ts = x.get("timestamp")
            if hasattr(ts, "isoformat"):
                return ts.isoformat()
            return str(ts) if ts else ""

        records.sort(
            key=lambda x: get_ts_str(x),
            reverse=True,
        )
        seen, result = set(), []
        for r in records:
            pid = r["product_id"]
            if pid not in seen:
                seen.add(pid)
                result.append(pid)
        return result

    def _merge_hybrid(
        self,
        cf_results: list[tuple[str, float]],
        content_results: list[tuple[str, float]],
        popular_results: list[tuple[str, float]],
        k: int,
        svd_results: list[tuple[str, float]] = None,
    ) -> list[tuple[str, float]]:
        """
        Merge ranked lists with explicit weights:
        20% Collaborative + 30% SVD + 40% Content-Based + 10% Trending
        """
        score_map: dict[str, float] = defaultdict(float)
        for pid, score in cf_results:
            score_map[pid] += HYBRID_CF_WEIGHT * score
        for pid, score in content_results:
            score_map[pid] += HYBRID_CONTENT_WEIGHT * score
        for pid, score in popular_results:
            score_map[pid] += HYBRID_TRENDING_WEIGHT * score
        if svd_results:
            for pid, score in svd_results:
                score_map[pid] += HYBRID_SVD_WEIGHT * score

        ranked = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
        max_score = ranked[0][1] if ranked else 1.0
        return [(pid, round(score / max_score, 4)) for pid, score in ranked[:k]]

    def recommend_for_user(
        self,
        user_id: str,
        k: int = 10,
        strategy: str = "auto",
        exclude_product_ids: list[str] = None,
    ) -> tuple[list[tuple[str, float]], str]:
        """
        Returns (product_id_score_list, strategy_name).

        Strategy auto-selection:
          < 2 interactions  → popularity
          2–9 interactions → content-based
          ≥ 10 interactions → hybrid (60% CF + 30% content + 10% trending)
        """
        if not self._is_ready:
            return [], "not_ready"

        n = self._interaction_count(user_id)
        interacted = self._interacted_products(user_id)
        exclude = set(exclude_product_ids) if exclude_product_ids is not None else set(interacted)

        if strategy == "auto":
            if n < COLD_START_THRESHOLD:
                strategy = "popularity"
            elif n < CONTENT_THRESHOLD:
                strategy = "content"
            else:
                strategy = "hybrid"

        if strategy == "popularity":
            results = self._popularity.recommend(k=k, exclude_product_ids=list(exclude))
            return results, "popularity"

        if strategy == "content":
            results = self._content_based.recommend_for_user(
                interacted_product_ids=interacted[:5], k=k, exclude_product_ids=list(exclude)
            )
            if not results:
                results = self._popularity.recommend(k=k, exclude_product_ids=list(exclude))
                return results, "popularity"
            return results, "content"

        if strategy == "hybrid":
            cf = self._collaborative.recommend_for_user(user_id=user_id, k=k * 2, exclude_product_ids=list(exclude))
            svd = self._svd.recommend_for_user(user_id=user_id, k=k * 2, exclude_product_ids=list(exclude))
            content = self._content_based.recommend_for_user(
                interacted_product_ids=interacted[:5], k=k * 2, exclude_product_ids=list(exclude)
            )
            popular = self._popularity.recommend(k=k * 2, exclude_product_ids=list(exclude))
            merged = self._merge_hybrid(cf, content, popular, k=k, svd_results=svd)
            if not merged:
                merged = popular[:k]
                return merged, "popularity"
            return merged, "hybrid"

        # Explicit strategy overrides
        if strategy == "collaborative":
            results = self._collaborative.recommend_for_user(user_id=user_id, k=k, exclude_product_ids=list(exclude))
            if not results:
                results = self._svd.recommend_for_user(user_id=user_id, k=k, exclude_product_ids=list(exclude))
            return results or self._popularity.recommend(k=k, exclude_product_ids=list(exclude)), "collaborative"

        if strategy == "svd":
            results = self._svd.recommend_for_user(user_id=user_id, k=k, exclude_product_ids=list(exclude))
            return results or self._popularity.recommend(k=k, exclude_product_ids=list(exclude)), "svd"

        return self._popularity.recommend(k=k, exclude_product_ids=list(exclude)), "popularity"

    def recommend_similar_products(
        self, product_id: str, k: int = 10
    ) -> tuple[list[tuple[str, float]], str]:
        if not self._is_ready:
            return [], "not_ready"
        results = self._content_based.recommend_similar(product_id=product_id, k=k)
        return results, "content"

    def get_metrics(self, k: int = 10) -> dict:
        if not self._is_ready:
            return {"error": "Engine not ready"}
        user_products: dict[str, list[str]] = {}

        def get_ts_str(x):
            ts = x.get("timestamp")
            if hasattr(ts, "isoformat"):
                return ts.isoformat()
            return str(ts) if ts else ""

        for r in sorted(self._interactions_cache, key=get_ts_str):
            uid, pid = r["user_id"], r["product_id"]
            if uid not in user_products:
                user_products[uid] = []
            if pid not in user_products[uid]:
                user_products[uid].append(pid)

        def recommender_fn(uid, top_k, train_items=None):
            return self.recommend_for_user(uid, k=top_k, strategy="hybrid", exclude_product_ids=train_items)[0]

        metrics = evaluate_recommendations(user_products, recommender_fn, k=k)
        metrics["k"] = k
        return metrics


# Global singleton
ml_engine = MLEngine()
