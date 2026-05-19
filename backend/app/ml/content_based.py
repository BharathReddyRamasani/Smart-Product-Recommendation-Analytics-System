"""
Content-based filtering using TF-IDF + Cosine Similarity.
Combines product name, category, description, and features into a rich text corpus.
Precomputes the full NxN similarity matrix for O(1) lookup at query time.
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _build_product_text(product: dict) -> str:
    """
    Combine product fields into a single text blob for TF-IDF.
    Category and name are repeated to increase their importance weight.
    """
    category = product.get("category", "")
    name = product.get("name", "")
    description = product.get("description", "")
    features = product.get("features", "").replace(",", " ")
    brand = product.get("brand", "")

    # Repeat category and name 3x to amplify importance
    return f"{category} {category} {category} {name} {name} {brand} {description} {features}"


class ContentBasedRecommender:
    """TF-IDF + Cosine Similarity recommender for product-to-product similarity."""

    def __init__(self) -> None:
        self._product_ids: list[int] = []
        self._id_to_index: dict[int, int] = {}
        self._similarity_matrix: np.ndarray | None = None
        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),          # Unigrams and bigrams
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,           # Apply log normalization
            stop_words="english",
        )
        self._is_fitted: bool = False

    def fit(self, products: list[dict]) -> "ContentBasedRecommender":
        """
        Build TF-IDF vectors and compute cosine similarity matrix.
        
        Args:
            products: List of dicts with keys: id, name, category, description, features, brand
        Returns:
            self
        """
        if not products:
            logger.warning("ContentBasedRecommender: No products to fit.")
            return self

        self._product_ids = [p["id"] for p in products]
        self._id_to_index = {pid: idx for idx, pid in enumerate(self._product_ids)}

        corpus = [_build_product_text(p) for p in products]
        tfidf_matrix = self._vectorizer.fit_transform(corpus)
        
        # Full similarity matrix: shape (N, N)
        self._similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        self._is_fitted = True
        logger.info(
            f"ContentBasedRecommender fitted: {len(products)} products, "
            f"matrix shape {self._similarity_matrix.shape}, "
            f"vocab size {len(self._vectorizer.vocabulary_)}"
        )
        return self

    def recommend_similar(
        self,
        product_id: int,
        k: int = 10,
        exclude_product_ids: list[int] | None = None,
    ) -> List[Tuple[int, float]]:
        """
        Return the top-K most similar products to the given product.
        
        Args:
            product_id: Source product ID
            k: Number of results
            exclude_product_ids: IDs to exclude from results
        Returns:
            List of (product_id, similarity_score) sorted descending
        """
        if not self._is_fitted or self._similarity_matrix is None:
            return []

        if product_id not in self._id_to_index:
            logger.warning(f"ContentBased: product_id {product_id} not in index")
            return []

        idx = self._id_to_index[product_id]
        similarity_row = self._similarity_matrix[idx]

        exclude = set(exclude_product_ids or [])
        exclude.add(product_id)  # Always exclude self

        results: list[tuple[int, float]] = []
        for other_idx, score in enumerate(similarity_row):
            pid = self._product_ids[other_idx]
            if pid not in exclude:
                results.append((pid, round(float(score), 4)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]

    def recommend_for_user(
        self,
        interacted_product_ids: list[int],
        k: int = 10,
        exclude_product_ids: list[int] | None = None,
    ) -> List[Tuple[int, float]]:
        """
        Recommend products for a user based on their interaction history.
        Aggregates similarity scores from all interacted products.
        
        Args:
            interacted_product_ids: Products the user has already interacted with
            k: Number of results
            exclude_product_ids: IDs to exclude (typically the interacted products)
        Returns:
            List of (product_id, aggregated_score)
        """
        if not self._is_fitted or not interacted_product_ids:
            return []

        if exclude_product_ids is not None:
            exclude = set(exclude_product_ids)
        else:
            exclude = set(interacted_product_ids)
        score_accumulator: dict[int, float] = {}

        for source_pid in interacted_product_ids:
            if source_pid not in self._id_to_index:
                continue
            sims = self.recommend_similar(source_pid, k=len(self._product_ids), exclude_product_ids=[])
            for pid, score in sims:
                if pid not in exclude:
                    score_accumulator[pid] = score_accumulator.get(pid, 0.0) + score

        if not score_accumulator:
            return []

        # Normalize by number of source products for fair comparison
        n_sources = len(interacted_product_ids)
        normalized = {pid: score / n_sources for pid, score in score_accumulator.items()}
        max_score = max(normalized.values()) or 1.0
        
        ranked = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
        return [(pid, round(score / max_score, 4)) for pid, score in ranked[:k]]
