"""
Evaluation metrics for recommendation systems.
Implements Precision@K, Recall@K, and Hit Rate.
"""
from typing import List, Set
from app.utils.logger import get_logger

logger = get_logger(__name__)


def precision_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
    """
    Precision@K: fraction of top-K recommendations that are relevant.
    
    Args:
        recommended: Ordered list of recommended product IDs
        relevant: Set of actually relevant product IDs for the user
        k: Cutoff rank
    Returns:
        Precision score in [0, 1]
    """
    if not recommended or not relevant:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for pid in top_k if pid in relevant)
    return hits / k


def recall_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
    """
    Recall@K: fraction of relevant items retrieved in top-K recommendations.
    
    Args:
        recommended: Ordered list of recommended product IDs
        relevant: Set of actually relevant product IDs for the user
        k: Cutoff rank
    Returns:
        Recall score in [0, 1]
    """
    if not recommended or not relevant:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for pid in top_k if pid in relevant)
    return hits / len(relevant)


def hit_rate(recommended: List[int], relevant: Set[int], k: int) -> float:
    """
    Hit Rate@K: 1 if at least one recommended item is relevant, 0 otherwise.
    
    Args:
        recommended: Ordered list of recommended product IDs
        relevant: Set of actually relevant product IDs for the user
        k: Cutoff rank
    Returns:
        1.0 or 0.0
    """
    if not recommended or not relevant:
        return 0.0
    top_k = set(recommended[:k])
    return 1.0 if top_k & relevant else 0.0


def evaluate_recommendations(
    user_interactions: dict[int, list[int]],
    recommender_fn,
    k: int = 10,
    test_ratio: float = 0.2,
) -> dict[str, float]:
    """
    Evaluate a recommender function using leave-last-N-out split.
    
    Args:
        user_interactions: Dict of user_id → list of interacted product IDs (ordered by time)
        recommender_fn: Callable(user_id, k) → list of (product_id, score)
        k: Evaluation cutoff
        test_ratio: Fraction of each user's interactions to use as ground truth
    Returns:
        Dict with precision@k, recall@k, hit_rate averaged over all users
    """
    precisions: list[float] = []
    recalls: list[float] = []
    hits: list[float] = []
    evaluated = 0

    for user_id, product_ids in user_interactions.items():
        if len(product_ids) < 2:
            continue  # Need at least train + test

        n_test = max(1, int(len(product_ids) * test_ratio))
        ground_truth = set(product_ids[-n_test:])  # Last N as ground truth
        train_items = product_ids[:-n_test]

        try:
            try:
                recs = recommender_fn(user_id, k, train_items)
            except TypeError:
                recs = recommender_fn(user_id, k)

            if not recs:
                continue
            rec_ids = [pid for pid, _ in recs]
            precisions.append(precision_at_k(rec_ids, ground_truth, k))
            recalls.append(recall_at_k(rec_ids, ground_truth, k))
            hits.append(hit_rate(rec_ids, ground_truth, k))
            evaluated += 1
        except Exception as e:
            logger.warning(f"Error evaluating user {user_id}: {e}")
            continue

    if not evaluated:
        return {"precision_at_k": 0.0, "recall_at_k": 0.0, "hit_rate": 0.0, "evaluated_users": 0}

    return {
        "precision_at_k": round(sum(precisions) / evaluated, 4),
        "recall_at_k": round(sum(recalls) / evaluated, 4),
        "hit_rate": round(sum(hits) / evaluated, 4),
        "evaluated_users": evaluated,
    }
