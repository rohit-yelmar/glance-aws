"""Search service with RRF (Reciprocal Rank Fusion) for hybrid semantic search."""

import time
from typing import List, Optional, Tuple

from app.config import get_settings
from app.core.exceptions import SearchServiceException
from app.core.logging import get_logger
from app.db.pinecone_client import get_pinecone_client
from app.db.rds_client import get_rds_client
from app.services.embedding_service import get_embedding_service
from app.utils.rrf_utils import rrf_merge, determine_match_type

logger = get_logger(__name__)


class SearchService:
    """Service for semantic product search using RRF."""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.pinecone = get_pinecone_client()
        self.rds = get_rds_client()
        self.settings = get_settings()
    
    async def semantic_search(
        self,
        query: str,
        store_id: Optional[str] = None,
        filters: Optional[dict] = None,
        limit: int = 3
    ) -> dict:
        """Perform semantic search with RRF merging.
        
        Args:
            query: Natural language search query
            store_id: Optional store filter
            filters: Optional filters (category, price, color)
            limit: Number of results to return
            
        Returns:
            Dictionary with results and metadata
        """
        start_time = time.time()
        
        try:
            logger.info("starting_semantic_search", query=query, store_id=store_id, limit=limit)
            
            # Step 1: Generate query embedding
            embedding_start = time.time()
            query_embedding = await self.embedding_service.embed_text(query)
            embedding_time = int((time.time() - embedding_start) * 1000)
            
            logger.debug("query_embedding_generated", time_ms=embedding_time)
            
            # Step 2: Parallel search - text and image similarity
            top_k = self.settings.SEARCH_TOP_K
            
            # Search by text embedding
            text_results_raw = self.pinecone.search_by_text_embedding(
                embedding=query_embedding,
                k=top_k,
                store_id=store_id
            )
            
            # Search by image embedding (using same query embedding in unified space)
            image_results_raw = self.pinecone.search_by_image_embedding(
                embedding=query_embedding,
                k=top_k,
                store_id=store_id
            )
            
            # Convert to standard format (product_id, score)
            text_results = [(r["product_id"], r["score"]) for r in text_results_raw]
            image_results = [(r["product_id"], r["score"]) for r in image_results_raw]
            
            logger.debug(
                "similarity_search_complete",
                text_results=len(text_results),
                image_results=len(image_results)
            )
            
            # Step 3: RRF Merge
            rrf_results = rrf_merge(text_results, image_results)
            
            # Step 4: Get top N unique products
            top_product_ids = [pid for pid, _ in rrf_results[:limit]]
            
            if not top_product_ids:
                logger.info("no_search_results")
                return {
                    "results": [],
                    "total_results": 0,
                    "query_embedding_time_ms": embedding_time,
                    "search_time_ms": int((time.time() - start_time) * 1000)
                }
            
            # Step 5: Fetch full product details from RDS
            products = self.rds.get_products_by_ids(top_product_ids)
            
            # Create product lookup
            product_lookup = {p.product_id: p for p in products}
            
            # Step 6: Build response preserving RRF order
            results = []
            for product_id, rrf_score in rrf_results[:limit]:
                product = product_lookup.get(product_id)
                if not product:
                    continue
                
                # Determine match type
                match_type = determine_match_type(product_id, text_results, image_results)
                
                results.append({
                    "product_id": product.product_id,
                    "name": product.name,
                    "description": product.description,
                    "price": float(product.price),
                    "currency": product.currency,
                    "image_url": product.image_url,
                    "confidence_score": round(rrf_score, 4),
                    "match_type": match_type
                })
            
            search_time = int((time.time() - start_time) * 1000)
            
            logger.info(
                "search_complete",
                total_results=len(results),
                search_time_ms=search_time
            )
            
            return {
                "results": results,
                "total_results": len(results),
                "query_embedding_time_ms": embedding_time,
                "search_time_ms": search_time
            }
            
        except Exception as e:
            logger.error("semantic_search_error", error=str(e))
            raise SearchServiceException(f"Search failed: {str(e)}")


# Singleton instance
_search_service = None


def get_search_service() -> SearchService:
    """Get singleton Search service instance."""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
