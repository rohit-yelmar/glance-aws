"""Search endpoint."""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from typing import Optional

from app.api.schemas import SearchRequest, SearchResponse
from app.core.logging import get_logger
from app.services.search_service import get_search_service

logger = get_logger(__name__)
router = APIRouter(tags=["Search"])


def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
    """Verify API key from header."""
    from app.config import get_settings
    settings = get_settings()
    
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK
)
async def search_products(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """Perform semantic product search.
    
    This endpoint uses RRF (Reciprocal Rank Fusion) to combine results
    from both text and image similarity searches in a unified embedding space.
    
    Args:
        request: Search request with query, optional filters, and limit
        
    Returns:
        SearchResponse with ranked product results
    """
    logger.info(
        "search_request",
        query=request.query,
        store_id=request.store_id,
        limit=request.limit
    )
    
    # Convert filters to dict if present
    filters = None
    if request.filters:
        filters = request.filters.model_dump(exclude_none=True)
    
    # Perform search
    search_service = get_search_service()
    result = await search_service.semantic_search(
        query=request.query,
        store_id=request.store_id,
        filters=filters,
        limit=request.limit
    )
    
    # Convert to response model
    return SearchResponse(
        results=result["results"],
        total_results=result["total_results"],
        query_embedding_time_ms=result.get("query_embedding_time_ms"),
        search_time_ms=result.get("search_time_ms")
    )
