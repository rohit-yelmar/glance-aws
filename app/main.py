"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health_router, catalog_router, search_router, product_router
from app.config import get_settings
from app.core.logging import configure_logging, get_logger

# Configure logging on import
configure_logging()
logger = get_logger(__name__)


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Glance - Visual Semantic Search",
        description="""
        AI-powered visual semantic search backend for fashion e-commerce.
        
        ## Features
        
        * **Catalog Ingestion**: Process product catalogs with AI-generated attributes
        * **Semantic Search**: Natural language product search using multimodal embeddings
        * **RRF Merging**: Reciprocal Rank Fusion for optimal text + image results
        
        ## AWS Services
        
        * Amazon Bedrock (Nova Lite, Nova Multimodal Embeddings)
        * Amazon RDS (PostgreSQL)
        * Amazon OpenSearch
        """,
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health_router)
    app.include_router(catalog_router)
    app.include_router(search_router)
    app.include_router(product_router)
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup event."""
        logger.info(
            "application_startup",
            environment=settings.ENVIRONMENT,
            version="1.0.0"
        )
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event."""
        logger.info("application_shutdown")
    
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
