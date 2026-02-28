"""RDS PostgreSQL client for product data operations."""

from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.core.exceptions import DatabaseException
from app.core.logging import get_logger
from app.db.models import Base, Product

logger = get_logger(__name__)

# Global engine and session factory
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,
        )
    return _engine


def get_session_local():
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    session = get_session_local()()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=get_engine())
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_init_error", error=str(e))
        raise DatabaseException(f"Failed to initialize database: {str(e)}")


class RDSClient:
    """Client for RDS PostgreSQL operations."""
    
    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """Create a new product record.
        
        Args:
            product_data: Product data dictionary
            
        Returns:
            Created Product model
        """
        try:
            with get_db_session() as session:
                product = Product(**product_data)
                session.add(product)
                session.flush()  # Get ID without committing
                logger.info("product_created", product_id=product.product_id)
                return product
        except Exception as e:
            logger.error("create_product_error", product_id=product_data.get("product_id"), error=str(e))
            raise DatabaseException(f"Failed to create product: {str(e)}")
    
    def create_products_batch(self, products_data: List[Dict[str, Any]]) -> int:
        """Create multiple products in batch.
        
        Args:
            products_data: List of product data dictionaries
            
        Returns:
            Number of products created
        """
        try:
            with get_db_session() as session:
                products = [Product(**data) for data in products_data]
                session.add_all(products)
                logger.info("products_batch_created", count=len(products))
                return len(products)
        except Exception as e:
            logger.error("batch_create_error", count=len(products_data), error=str(e))
            raise DatabaseException(f"Failed to create products batch: {str(e)}")
    
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Get product by product_id.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product model or None
        """
        try:
            with get_db_session() as session:
                result = session.execute(
                    select(Product).where(Product.product_id == product_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error("get_product_error", product_id=product_id, error=str(e))
            raise DatabaseException(f"Failed to get product: {str(e)}")
    
    def get_products_by_ids(self, product_ids: List[str]) -> List[Product]:
        """Get multiple products by IDs.
        
        Args:
            product_ids: List of product identifiers
            
        Returns:
            List of Product models
        """
        try:
            with get_db_session() as session:
                result = session.execute(
                    select(Product).where(Product.product_id.in_(product_ids))
                )
                return list(result.scalars().all())
        except Exception as e:
            logger.error("get_products_error", count=len(product_ids), error=str(e))
            raise DatabaseException(f"Failed to get products: {str(e)}")
    
    def update_vision_attributes(
        self, 
        product_id: str, 
        vision_attributes: Dict[str, Any],
        raw_response: Optional[str] = None
    ) -> bool:
        """Update vision analysis attributes for a product.
        
        Args:
            product_id: Product identifier
            vision_attributes: Vision analysis results
            raw_response: Raw API response (optional)
            
        Returns:
            True if updated successfully
        """
        try:
            with get_db_session() as session:
                result = session.execute(
                    select(Product).where(Product.product_id == product_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    logger.warning("product_not_found_for_vision_update", product_id=product_id)
                    return False
                
                product.vision_attributes = vision_attributes
                if raw_response:
                    product.raw_vision_response = raw_response
                
                logger.info("vision_attributes_updated", product_id=product_id)
                return True
        except Exception as e:
            logger.error("update_vision_error", product_id=product_id, error=str(e))
            raise DatabaseException(f"Failed to update vision attributes: {str(e)}")
    
    def update_embedding_status(self, product_id: str, status: str) -> bool:
        """Update embedding generation status.
        
        Args:
            product_id: Product identifier
            status: New status (pending/processing/completed/failed)
            
        Returns:
            True if updated successfully
        """
        try:
            with get_db_session() as session:
                result = session.execute(
                    select(Product).where(Product.product_id == product_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    logger.warning("product_not_found_for_status_update", product_id=product_id)
                    return False
                
                product.embedding_status = status
                logger.info("embedding_status_updated", product_id=product_id, status=status)
                return True
        except Exception as e:
            logger.error("update_status_error", product_id=product_id, error=str(e))
            raise DatabaseException(f"Failed to update embedding status: {str(e)}")
    
    def health_check(self) -> bool:
        """Check database connectivity.
        
        Returns:
            True if database is accessible
        """
        try:
            with get_db_session() as session:
                session.execute(select(1))
                return True
        except Exception as e:
            logger.error("health_check_failed", error=str(e))
            return False


# Singleton instance
_rds_client = None


def get_rds_client() -> RDSClient:
    """Get singleton RDS client instance."""
    global _rds_client
    if _rds_client is None:
        _rds_client = RDSClient()
    return _rds_client
