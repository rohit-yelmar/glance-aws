"""API routes package."""

from app.api.routes.health import router as health_router
from app.api.routes.catalog import router as catalog_router
from app.api.routes.search import router as search_router
from app.api.routes.product import router as product_router

__all__ = ["health_router", "catalog_router", "search_router", "product_router"]
