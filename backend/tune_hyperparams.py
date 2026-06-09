import sys
import os

from app.utils.database import connect_to_mongo, close_mongo
from app.ml.engine import MLEngine
from app.ml.collaborative import CollaborativeFilteringRecommender
from app.ml.matrix_factorization import SVDRecommender
from app.ml.content_based import ContentBasedRecommender
from app.ml.popularity import PopularityRecommender

class TunedMLEngine(MLEngine):
    def __init__(self, cf_w, content_w, trend_w, svd_w=0.0):
        super().__init__()
        self.cf_w = cf_w
        self.content_w = content_w
        self.trend_w = trend_w
        self.svd_w = svd_w

    def _merge_hybrid(
        self,
        cf_results: list[tuple[str, float]],
        content_results: list[tuple[str, float]],
        popular_results: list[tuple[str, float]],
        k: int,
        svd_results: list[tuple[str, float]] = None
    ) -> list[tuple[str, float]]:
        from collections import defaultdict
        score_map = defaultdict(float)
        for pid, score in cf_results:
            score_map[pid] += self.cf_w * score
        for pid, score in content_results:
            score_map[pid] += self.content_w * score
        for pid, score in popular_results:
            score_map[pid] += self.trend_w * score
        if svd_results and self.svd_w > 0:
            for pid, score in svd_results:
                score_map[pid] += self.svd_w * score

        ranked = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
        max_score = ranked[0][1] if ranked else 1.0
        return [(pid, round(score / max_score, 4)) for pid, score in ranked[:k]]

    def recommend_for_user(self, user_id: str, k: int = 10, strategy: str = "auto", exclude_product_ids: list[str] = None):
        n = self._interaction_count(user_id)
        interacted = self._interacted_products(user_id)
        exclude = set(exclude_product_ids) if exclude_product_ids is not None else set(interacted)

        # Force hybrid for testing
        cf = self._collaborative.recommend_for_user(user_id=user_id, k=k * 2, exclude_product_ids=list(exclude))
        content = self._content_based.recommend_for_user(
            interacted_product_ids=interacted, k=k * 2, exclude_product_ids=list(exclude)
        )
        popular = self._popularity.recommend(k=k * 2, exclude_product_ids=list(exclude))
        
        svd = []
        if self.svd_w > 0:
            svd = self._svd.recommend_for_user(user_id=user_id, k=k * 2, exclude_product_ids=list(exclude))
            
        merged = self._merge_hybrid(cf, content, popular, k=k, svd_results=svd)
        if not merged:
            merged = popular[:k]
        return merged, "hybrid"


def run_experiment():
    db = connect_to_mongo()
    try:
        print("Loading products and interactions...")
        products = list(db.products.find({}))
        interactions = list(db.interactions.find({}))
        
        product_dicts = []
        for p in products:
            features = p.get("features", [])
            features_str = " ".join(features) if isinstance(features, list) else str(features)
            product_dicts.append({
                "id": str(p["_id"]), "name": p.get("name", ""),
                "category": p.get("category", ""), "description": p.get("description", ""),
                "features": features_str, "brand": p.get("brand", "")
            })
            
        interaction_dicts = []
        for i in interactions:
            interaction_dicts.append({
                "user_id": str(i["user_id"]), "product_id": str(i["product_id"]),
                "interaction_type": i.get("interaction_type", "view"),
                "rating": i.get("rating"), "timestamp": i.get("timestamp")
            })

        print("Fitting models once...")
        content = ContentBasedRecommender().fit(product_dicts)
        collab = CollaborativeFilteringRecommender().fit(interaction_dicts)
        svd = SVDRecommender(n_factors=20).fit(interaction_dicts)
        pop = PopularityRecommender().fit(interaction_dicts)

        configs = [
            (0.7, 0.2, 0.1, 0.0), # Current
            (0.5, 0.3, 0.1, 0.1), # Add SVD
            (0.4, 0.2, 0.1, 0.3), # Heavy SVD
            (0.8, 0.2, 0.0, 0.0), # Pure CF+Content
            (0.4, 0.4, 0.1, 0.1), # Even CF+Content
            (0.0, 0.0, 0.0, 1.0), # Pure SVD
        ]

        for cf_w, con_w, pop_w, svd_w in configs:
            engine = TunedMLEngine(cf_w, con_w, pop_w, svd_w)
            engine._is_ready = True
            engine._interactions_cache = interaction_dicts
            engine._products_cache = product_dicts
            engine._content_based = content
            engine._collaborative = collab
            engine._svd = svd
            engine._popularity = pop
            
            metrics = engine.get_metrics(k=10)
            print(f"Weights (CF:{cf_w}, Con:{con_w}, Pop:{pop_w}, SVD:{svd_w}) -> Prec: {metrics['precision_at_k']:.4f}, Rec: {metrics['recall_at_k']:.4f}, Hit: {metrics['hit_rate']:.4f}")

    finally:
        close_mongo()

if __name__ == "__main__":
    run_experiment()
