"""Product details endpoint."""

from fastapi import APIRouter, Depends, Header, HTTPException, Path, status

from app.api.schemas import ProductResponse
from app.core.exceptions import ProductNotFoundException
from app.core.logging import get_logger
from app.db.rds_client import get_rds_client

logger = get_logger(__name__)
router = APIRouter(tags=["Products"])


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


@router.get(
    "/product/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK
)
async def get_product(
    product_id: str = Path(..., description="Product identifier"),
    api_key: str = Depends(verify_api_key)
):
    """Get product details by ID.
    
    Args:
        product_id: Product identifier
        
    Returns:
        ProductResponse with full product details
        
    Raises:
        HTTPException: If product not found
    """
    logger.info("get_product_request", product_id=product_id)
    
    rds = get_rds_client()
    product = rds.get_product_by_id(product_id)
    
    if not product:
        logger.warning("product_not_found", product_id=product_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product not found: {product_id}"
        )
    
    # Convert to response model
    product_dict = product.to_dict()
    
    return ProductResponse(**product_dict)
