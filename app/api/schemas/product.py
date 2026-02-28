"""Schemas for product-related endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VisionAttributes(BaseModel):
    """Vision model extracted attributes from image analysis."""
    
    visual_description: Optional[str] = Field(None, description="Detailed visual description")
    material: Optional[str] = Field(None, description="Detected fabric/material")
    fit_style: Optional[str] = Field(None, description="Fit and style information")
    occasion: Optional[str] = Field(None, description="Suitable occasions")
    season: Optional[str] = Field(None, description="Appropriate seasons")
    color_analysis: Optional[Dict[str, Any]] = Field(None, description="Color analysis with synonyms")
    pattern: Optional[str] = Field(None, description="Pattern type")
    vibe_keywords: List[str] = Field(default_factory=list, description="Vibe/aesthetic keywords")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "visual_description": "Light blue button-up shirt with spread collar",
                "material": "Linen blend",
                "fit_style": "Regular fit, slightly relaxed",
                "occasion": "Casual, smart-casual",
                "season": "Summer, spring",
                "color_analysis": {
                    "primary": "sky blue",
                    "synonyms": ["light blue", "powder blue", "pale blue"]
                },
                "pattern": "Solid, no visible pattern",
                "vibe_keywords": ["breezy", "relaxed", "coastal", "minimalist", "airy"]
            }
        }
    }


class ProductResponse(BaseModel):
    """Full product details response."""
    
    product_id: str = Field(..., description="Product identifier")
    store_id: str = Field(..., description="Store identifier")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., description="Product price")
    currency: str = Field(default="USD")
    category: Optional[str] = Field(None, description="Product category")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Product attributes")
    image_url: Optional[str] = Field(None, description="Primary image URL")
    additional_images: List[str] = Field(default_factory=list, description="Additional images")
    vision_attributes: Optional[VisionAttributes] = Field(None, description="AI-generated attributes")
    embedding_status: str = Field(default="pending", description="Embedding generation status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "shirt-001",
                "store_id": "fashion-store-001",
                "name": "Classic Blue Linen Shirt",
                "description": "A comfortable linen shirt perfect for summer",
                "price": 59.99,
                "currency": "USD",
                "category": "shirts",
                "tags": ["linen", "blue", "summer"],
                "attributes": {"color": "blue", "material": "linen"},
                "image_url": "https://example.com/image.jpg",
                "embedding_status": "completed",
                "vision_attributes": {
                    "visual_description": "Light blue button-up shirt",
                    "material": "Linen blend",
                    "vibe_keywords": ["breezy", "relaxed", "coastal"]
                }
            }
        }
    }
