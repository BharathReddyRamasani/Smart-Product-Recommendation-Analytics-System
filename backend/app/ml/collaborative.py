"""
Collaborative Filtering using User-Item matrix and cosine similarity.
Supports both user-user similarity-based prediction.
Interaction types are weighted: view=1, add_to_cart=3, purchase=5.
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from typing import List, Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)

INTERACTION_WEIGHTS = {"view": 1, "add_to_cart": 3, "purchase": 5}


class CollaborativeFilteringRecommender:
    """Memory-based user-user collaborative filtering recommender."""

    def __init__(self) -> None:
        self._user_item_matrix: np.ndarray | None = None
        self._user_ids: list[str] = []
        self._product_ids: list[str] = []
        self._user_index: dict[str, int] = {}
        self._product_index: dict[str, int] = {}
        self._user_similarity: np.ndarray | None = None
        self._is_fitted: bool = False

    def fit(self, interactions: list[dict]) -> "CollaborativeFilteringRecommender":
        """
        Build user-item matrix and compute user-user cosine similarity.
        
        Args:
            interactions: List of dicts with user_id, product_id, interaction_type, rating
        Returns:
            self
        """
        if not interactions:
            logger.warning("CollaborativeFilteringRecommender: No interactions to fit.")
            return self

        # Collect all unique users and products
        user_ids = sorted(set(r["user_id"] for r in interactions))
        product_ids = sorted(set(r["product_id"] for r in interactions))

        self._user_ids = user_ids
        self._product_ids = product_ids
        self._user_index = {uid: i for i, uid in enumerate(user_ids)}
        self._product_index = {pid: j for j, pid in enumerate(product_ids)}

        # Build weighted interaction matrix
        matrix = np.zeros((len(user_ids), len(product_ids)), dtype=np.float32)

        for record in interactions:
            uid = record["user_id"]
            pid = record["product_id"]
            itype = record["interaction_type"]
            rating = record.get("rating")

            if uid not in self._user_index or pid not in self._product_index:
                continue

            i = self._user_index[uid]
            j = self._product_index[pid]
            weight = INTERACTION_WEIGHTS.get(itype, 1)

            # Incorporate explicit rating if available
            if rating:
                rating_factor = rating / 5.0  # Normalize to [0,1]
                matrix[i, j] = max(matrix[i, j], weight * rating_factor * 5)
            else:
                matrix[i, j] = max(matrix[i, j], weight)

        self._user_item_matrix = matrix

        # Compute user-user cosine similarity
        self._user_similarity = cosine_similarity(matrix)
        self._is_fitted = True

        logger.info(
            f"CollaborativeFiltering fitted: {len(user_ids)} users × {len(product_ids)} products, "
            f"sparsity={1 - np.count_nonzero(matrix) / matrix.size:.2%}"
        )
        return self

    def recommend_for_user(
        self,
        user_id: str,
        k: int = 10,
        n_similar_users: int = 20,
        exclude_product_ids: list[str] | None = None,
    ) -> List[Tuple[str, float]]:
        """
        Generate recommendations using weighted nearest-neighbor scoring.
        
        Args:
            user_id: Target user
            k: Number of recommendations
            n_similar_users: Number of similar users to aggregate from
            exclude_product_ids: Products to exclude (typically already seen)
        Returns:
            List of (product_id, score) sorted descending
        """
        if not self._is_fitted or self._user_similarity is None:
            return []

        if user_id not in self._user_index:
            logger.warning(f"CollaborativeFiltering: user_id {user_id} not in training set")
            return []

        u_idx = self._user_index[user_id]
        sim_row = self._user_similarity[u_idx]

        # Find top similar users (excluding self)
        similar_indices = np.argsort(sim_row)[::-1]
        similar_indices = similar_indices[similar_indices != u_idx][:n_similar_users]

        if exclude_product_ids is not None:
            exclude = set(exclude_product_ids)
        else:
            seen_products = set(
                self._product_ids[j]
                for j in np.nonzero(self._user_item_matrix[u_idx])[0]
            )
            exclude = seen_products

        # Weighted aggregation of scores from similar users
        score_accumulator: dict[str, float] = defaultdict(float)

        for sim_idx in similar_indices:
            sim_score = sim_row[sim_idx]
            if sim_score <= 0:
                continue
            user_vector = self._user_item_matrix[sim_idx]
            for j, val in enumerate(user_vector):
                if val > 0:
                    pid = self._product_ids[j]
                    if pid not in exclude:
                        score_accumulator[pid] += sim_score * val

        if not score_accumulator:
            return []

        max_score = max(score_accumulator.values()) or 1.0
        ranked = sorted(score_accumulator.items(), key=lambda x: x[1], reverse=True)
        return [(pid, round(score / max_score, 4)) for pid, score in ranked[:k]]
