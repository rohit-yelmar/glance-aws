"""Reciprocal Rank Fusion (RRF) algorithm implementation."""

from collections import defaultdict
from typing import Dict, List, Tuple

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def calculate_rrf_score(rank: int, k: int = 60) -> float:
    """Calculate RRF score for a given rank.
    
    The RRF formula: score = 1 / (k + rank)
    Where k=60 is the standard constant that prevents top ranks from dominating.
    
    Args:
        rank: Position in ranked list (1-indexed)
        k: RRF constant (default: 60)
        
    Returns:
        RRF score
    """
    return 1.0 / (k + rank)


def rrf_merge(
    text_results: List[Tuple[str, float]],
    image_results: List[Tuple[str, float]],
    k: int = None
) -> List[Tuple[str, float]]:
    """Merge two ranked lists using Reciprocal Rank Fusion.
    
    Args:
        text_results: List of (product_id, score) from text search, ordered by relevance
        image_results: List of (product_id, score) from image search, ordered by relevance
        k: RRF constant (uses settings default if None)
        
    Returns:
        List of (product_id, rrf_score) sorted by combined score descending
    """
    if k is None:
        k = get_settings().RRF_K
    
    # Accumulate RRF scores
    scores: Dict[str, float] = defaultdict(float)
    
    # Add scores from text results
    for rank, (product_id, _) in enumerate(text_results, start=1):
        scores[product_id] += calculate_rrf_score(rank, k)
        logger.debug("rrf_text_score", product_id=product_id, rank=rank, score=calculate_rrf_score(rank, k))
    
    # Add scores from image results
    for rank, (product_id, _) in enumerate(image_results, start=1):
        scores[product_id] += calculate_rrf_score(rank, k)
        logger.debug("rrf_image_score", product_id=product_id, rank=rank, score=calculate_rrf_score(rank, k))
    
    # Sort by combined score descending
    sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    logger.info("rrf_merge_complete", 
                text_count=len(text_results), 
                image_count=len(image_results),
                merged_count=len(sorted_results))
    
    return sorted_results


def deduplicate_by_id(results: List[Tuple[str, any]]) -> List[Tuple[str, any]]:
    """Remove duplicate products keeping first occurrence.
    
    Args:
        results: List of (product_id, ...) tuples
        
    Returns:
        Deduplicated list
    """
    seen = set()
    deduplicated = []
    
    for item in results:
        product_id = item[0]
        if product_id not in seen:
            seen.add(product_id)
            deduplicated.append(item)
    
    logger.debug("deduplicate_complete", 
                original_count=len(results), 
                deduplicated_count=len(deduplicated))
    
    return deduplicated


def determine_match_type(
    product_id: str,
    text_results: List[Tuple[str, float]],
    image_results: List[Tuple[str, float]]
) -> str:
    """Determine if match came from text, image, or both.
    
    Args:
        product_id: Product ID to check
        text_results: Text search results
        image_results: Image search results
        
    Returns:
        Match type: "text", "image", or "hybrid"
    """
    text_ids = {r[0] for r in text_results}
    image_ids = {r[0] for r in image_results}
    
    in_text = product_id in text_ids
    in_image = product_id in image_ids
    
    if in_text and in_image:
        return "hybrid"
    elif in_text:
        return "text"
    else:
        return "image"
