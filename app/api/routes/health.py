"""Health check endpoint."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.core.exceptions import DatabaseException, OpenSearchException
from app.core.logging import get_logger
from app.db.opensearch_client import get_opensearch_client
from app.db.rds_client import get_rds_client

logger = get_logger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for monitoring.
    
    Returns:
        Health status with service connectivity information.
    """
    settings = get_settings()
    
    # Check individual services
    services_status = {}
    overall_status = "healthy"
    
    # Check RDS
    try:
        rds = get_rds_client()
        rds_healthy = rds.health_check()
        services_status["database"] = "connected" if rds_healthy else "disconnected"
        if not rds_healthy:
            overall_status = "degraded"
    except Exception as e:
        logger.error("health_check_rds_error", error=str(e))
        services_status["database"] = "error"
        overall_status = "degraded"
    
    # Check OpenSearch
    try:
        opensearch = get_opensearch_client()
        os_healthy = opensearch.health_check()
        services_status["opensearch"] = "connected" if os_healthy else "disconnected"
        if not os_healthy:
            overall_status = "degraded"
    except Exception as e:
        logger.error("health_check_opensearch_error", error=str(e))
        services_status["opensearch"] = "error"
        overall_status = "degraded"
    
    # Bedrock check is implicit (we'll verify on first use)
    services_status["bedrock"] = "available"
    
    response = {
        "status": overall_status,
        "version": "1.0.0",
        "services": services_status,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.debug("health_check", status=overall_status)
    
    # Return 503 if critical services are down
    if services_status["database"] == "error" or services_status["opensearch"] == "error":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response
        )
    
    return response
