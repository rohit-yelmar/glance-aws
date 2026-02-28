"""Schemas for search endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    """Optional filters for search queries."""
    
    category: Optional[str] = Field(None, description="Filter by category")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price")
    color: Optional[str] = Field(None, description="Filter by color")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "category": "shirts",
                "price_min": 20.0,
                "price_max": 100.0,
                "color": "blue"
            }
        }
    }


class SearchRequest(BaseModel):
    """Request model for semantic search."""
    
    query: str = Field(..., min_length=1, description="Natural language search query")
    store_id: Optional[str] = Field(None, description="Optional store filter")
    filters: Optional[SearchFilters] = Field(None, description="Optional filters")
    limit: int = Field(default=3, ge=1, le=20, description="Number of results to return")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "summer solid light blue linen shirt",
                "store_id": "fashion-store-001",
                "filters": {
                    "category": "shirts",
                    "price_max": 100.0
                },
                "limit": 3
            }
        }
    }


class SearchResult(BaseModel):
    """Single search result item."""
    
    product_id: str = Field(..., description="Product identifier")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., description="Product price")
    currency: str = Field(default="USD")
    image_url: Optional[str] = Field(None, description="Product image URL")
    confidence_score: float = Field(..., ge=0, le=1, description="RRF combined relevance score")
    match_type: str = Field(default="hybrid", description="Match source: text, image, or hybrid")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "shirt-001",
                "name": "Classic Blue Linen Shirt",
                "description": "A comfortable linen shirt perfect for summer",
                "price": 59.99,
                "currency": "USD",
                "image_url": "https://example.com/image.jpg",
                "confidence_score": 0.92,
                "match_type": "hybrid"
            }
        }
    }


class SearchResponse(BaseModel):
    """Response model for semantic search."""
    
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    query_embedding_time_ms: Optional[int] = Field(None, description="Time to generate query embedding")
    search_time_ms: Optional[int] = Field(None, description="Total search time")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "results": [
                    {
                        "product_id": "shirt-001",
                        "name": "Classic Blue Linen Shirt",
                        "price": 59.99,
                        "confidence_score": 0.92,
                        "match_type": "hybrid"
                    }
                ],
                "total_results": 3,
                "query_embedding_time_ms": 150,
                "search_time_ms": 250
            }
        }
    }
