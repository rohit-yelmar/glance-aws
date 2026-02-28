"""SQLAlchemy ORM models for RDS PostgreSQL."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, ARRAY, String, Text, Numeric, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Product(Base):
    """Product model for storing catalog data."""
    
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    store_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    additional_images: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Vision analysis results
    vision_attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    raw_vision_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Processing status
    embedding_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "product_id": self.product_id,
            "store_id": self.store_id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "currency": self.currency,
            "category": self.category,
            "tags": self.tags or [],
            "attributes": self.attributes or {},
            "image_url": self.image_url,
            "additional_images": self.additional_images or [],
            "vision_attributes": self.vision_attributes,
            "embedding_status": self.embedding_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
