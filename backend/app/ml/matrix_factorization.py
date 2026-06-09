"""
Matrix Factorization using Truncated SVD.
Decomposes the user-item interaction matrix to discover latent factors.
Falls back gracefully if the matrix is too sparse for SVD.
"""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
from typing import List, Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)

INTERACTION_WEIGHTS = {"view": 1, "add_to_cart": 3, "purchase": 5}


class SVDRecommender:
    """Matrix factorization recommender using truncated SVD."""

    def __init__(self, n_factors: int = 20) -> None:
        self._n_factors = n_factors
        self._user_ids: list[str] = []
        self._product_ids: list[str] = []
        self._user_index: dict[str, int] = {}
        self._product_index: dict[str, int] = {}
        self._predicted_matrix: np.ndarray | None = None
        self._user_item_matrix: np.ndarray | None = None
        self._is_fitted: bool = False

    def fit(self, interactions: list[dict]) -> "SVDRecommender":
        """
        Decompose user-item matrix using truncated SVD.
        
        Args:
            interactions: List of dicts with user_id, product_id, interaction_type, rating
        Returns:
            self
        """
        if not interactions:
            logger.warning("SVDRecommender: No interactions to fit.")
            return self

        user_ids = sorted(set(r["user_id"] for r in interactions))
        product_ids = sorted(set(r["product_id"] for r in interactions))

        self._user_ids = user_ids
        self._product_ids = product_ids
        self._user_index = {uid: i for i, uid in enumerate(user_ids)}
        self._product_index = {pid: j for j, pid in enumerate(product_ids)}

        n_users, n_products = len(user_ids), len(product_ids)
        matrix = np.zeros((n_users, n_products), dtype=np.float32)

        for record in interactions:
            uid = record.get("user_id")
            pid = record.get("product_id")
            itype = record.get("interaction_type", "view")
            rating = record.get("rating")

            if uid not in self._user_index or pid not in self._product_index:
                continue

            i = self._user_index[uid]
            j = self._product_index[pid]
            weight = INTERACTION_WEIGHTS.get(itype, 1)

            if rating:
                matrix[i, j] = max(matrix[i, j], weight * (rating / 5.0) * 5)
            else:
                matrix[i, j] = max(matrix[i, j], float(weight))

        self._user_item_matrix = matrix

        # Determine feasible number of factors
        k = min(self._n_factors, n_users - 1, n_products - 1)
        if k < 1:
            logger.warning("SVDRecommender: Matrix too small for SVD, skipping.")
            return self

        sparse_matrix = csr_matrix(matrix)
        try:
            U, sigma, Vt = svds(sparse_matrix, k=k)
            # Reconstruct the full predicted ratings matrix
            sigma_diag = np.diag(sigma)
            self._predicted_matrix = np.dot(np.dot(U, sigma_diag), Vt)
            self._is_fitted = True
            logger.info(
                f"SVDRecommender fitted: {n_users}×{n_products} matrix, "
                f"{k} latent factors"
            )
        except Exception as e:
            logger.error(f"SVD decomposition failed: {e}")

        return self

    def recommend_for_user(
        self,
        user_id: str,
        k: int = 10,
        exclude_product_ids: list[str] | None = None,
    ) -> List[Tuple[str, float]]:
        """
        Recommend products using reconstructed preference scores.
        
        Args:
            user_id: Target user
            k: Number of recommendations
            exclude_product_ids: Products to exclude
        Returns:
            List of (product_id, score) sorted descending
        """
        if not self._is_fitted or self._predicted_matrix is None:
            return []

        if user_id not in self._user_index:
            logger.warning(f"SVDRecommender: user_id {user_id} not in index")
            return []

        u_idx = self._user_index[user_id]
        predicted_scores = self._predicted_matrix[u_idx]

        if exclude_product_ids is not None:
            exclude = set(exclude_product_ids)
        elif self._user_item_matrix is not None:
            seen = set(
                self._product_ids[j]
                for j in np.nonzero(self._user_item_matrix[u_idx])[0]
            )
            exclude = seen
        else:
            exclude = set()

        results: list[tuple[str, float]] = []
        for j, score in enumerate(predicted_scores):
            pid = self._product_ids[j]
            if pid not in exclude:
                results.append((pid, float(score)))

        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:k]

        if not results:
            return []

        min_score = min(s for _, s in results)
        max_score = max(s for _, s in results)
        score_range = max_score - min_score or 1.0

        return [(pid, round((score - min_score) / score_range, 4)) for pid, score in results]
