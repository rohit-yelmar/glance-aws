"""Schemas for catalog ingestion endpoints."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class ProductInput(BaseModel):
    """Input model for a single product in catalog ingestion."""
    
    product_id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Product price")
    currency: str = Field(default="USD", description="Currency code (ISO 4217)")
    category: Optional[str] = Field(None, description="Product category")
    tags: List[str] = Field(default_factory=list, description="Product tags/keywords")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional product attributes")
    image_url: HttpUrl = Field(..., description="Primary product image URL (S3 or public)")
    additional_images: List[HttpUrl] = Field(default_factory=list, description="Additional image URLs")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "shirt-001",
                "name": "Classic Blue Linen Shirt",
                "description": "A comfortable linen shirt perfect for summer",
                "price": 59.99,
                "currency": "USD",
                "category": "shirts",
                "tags": ["linen", "blue", "summer", "casual"],
                "attributes": {
                    "color": "blue",
                    "material": "linen",
                    "fit": "regular"
                },
                "image_url": "https://example-bucket.s3.amazonaws.com/shirt-001.jpg",
                "additional_images": []
            }
        }
    }


class CatalogRequest(BaseModel):
    """Request model for catalog ingestion."""
    
    store_id: str = Field(..., description="Store/tenant identifier")
    products: List[ProductInput] = Field(..., min_length=1, description="List of products to ingest")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "store_id": "fashion-store-001",
                "products": [
                    {
                        "product_id": "shirt-001",
                        "name": "Classic Blue Linen Shirt",
                        "description": "A comfortable linen shirt",
                        "price": 59.99,
                        "category": "shirts",
                        "tags": ["linen", "blue"],
                        "image_url": "https://example.com/image.jpg"
                    }
                ]
            }
        }
    }


class CatalogResponse(BaseModel):
    """Response model for catalog ingestion."""
    
    job_id: str = Field(..., description="Processing job identifier")
    status: str = Field(default="processing", description="Job status")
    total_products: int = Field(..., description="Total products submitted")
    message: str = Field(default="Catalog ingestion started")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "total_products": 10,
                "message": "Catalog ingestion started"
            }
        }
    }
