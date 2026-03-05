"""Catalog ingestion endpoint."""

import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status

from app.api.schemas import CatalogRequest, CatalogResponse
from app.core.constants import EMBEDDING_STATUS_PENDING, EMBEDDING_STATUS_PROCESSING, EMBEDDING_STATUS_COMPLETED, EMBEDDING_STATUS_FAILED
from app.core.logging import get_logger
from app.db.pinecone_client import get_pinecone_client
from app.db.rds_client import get_rds_client
from app.services.embedding_service import get_embedding_service
from app.services.vision_service import get_vision_service
from app.utils.image_utils import download_image
from app.utils.text_utils import combine_product_text

logger = get_logger(__name__)
router = APIRouter(tags=["Catalog"])


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


async def process_product(
    store_id: str,
    product_data: dict
):
    """Process a single product through the pipeline.
    
    Steps:
    1. Download image
    2. Vision analysis
    3. Update RDS with vision attributes
    4. Combine text
    5. Generate embeddings
    6. Index in Pinecone
    7. Update status
    """
    product_id = product_data["product_id"]
    rds = get_rds_client()
    
    try:
        logger.info("processing_product", product_id=product_id, store_id=store_id)
        
        # Update status to processing
        rds.update_embedding_status(product_id, EMBEDDING_STATUS_PROCESSING)
        
        # 1. Download image
        image_bytes = await download_image(product_data["image_url"])
        
        # 2. Vision analysis
        vision = get_vision_service()
        vision_attrs = await vision.analyze_image(image_bytes)
        
        # 3. Update RDS with vision attributes
        rds.update_vision_attributes(
            product_id=product_id,
            vision_attributes=vision_attrs,
            raw_response=str(vision_attrs)
        )
        
        # 4. Combine text
        combined_text = combine_product_text(
            name=product_data["name"],
            description=product_data.get("description"),
            category=product_data.get("category"),
            tags=product_data.get("tags", []),
            attributes=product_data.get("attributes", {}),
            vision_attrs=vision_attrs
        )
        
        # 5. Generate embeddings
        embedding_service = get_embedding_service()
        text_embedding = await embedding_service.embed_text(combined_text)
        image_embedding = await embedding_service.embed_image(image_bytes)
        
        # 6. Index in Pinecone
        pinecone = get_pinecone_client()
        pinecone.upsert_product(
            product_id=product_id,
            store_id=store_id,
            text_embedding=text_embedding,
            image_embedding=image_embedding,
            combined_text=combined_text,
            metadata={
                "category": product_data.get("category"),
                "price": float(product_data["price"]),
                "color": product_data.get("attributes", {}).get("color")
            }
        )
        
        # 7. Update status to completed
        rds.update_embedding_status(product_id, EMBEDDING_STATUS_COMPLETED)
        
        logger.info("product_processing_complete", product_id=product_id)
        
    except Exception as e:
        logger.error("product_processing_error", product_id=product_id, error=str(e))
        rds.update_embedding_status(product_id, EMBEDDING_STATUS_FAILED)


async def process_catalog_batch(store_id: str, products: List[dict]):
    """Process a batch of products."""
    for product in products:
        try:
            await process_product(store_id, product)
        except Exception as e:
            logger.error("batch_processing_error", product_id=product.get("product_id"), error=str(e))
            # Continue with next product


@router.post(
    "/ingest-catalog",
    response_model=CatalogResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def ingest_catalog(
    request: CatalogRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Ingest product catalog for processing.
    
    Products are stored immediately in RDS and then processed in the background
    to generate embeddings. This endpoint returns immediately with a job ID.
    
    Args:
        request: Catalog ingestion request with store_id and products
        background_tasks: FastAPI background tasks
        
    Returns:
        CatalogResponse with job_id and status
    """
    job_id = str(uuid.uuid4())
    
    logger.info(
        "catalog_ingestion_started",
        job_id=job_id,
        store_id=request.store_id,
        product_count=len(request.products)
    )
    
    # Prepare product data for RDS
    products_data = []
    for product in request.products:
        product_dict = {
            "product_id": product.product_id,
            "store_id": request.store_id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "currency": product.currency,
            "category": product.category,
            "tags": product.tags,
            "attributes": product.attributes,
            "image_url": str(product.image_url),
            "additional_images": [str(url) for url in product.additional_images],
            "embedding_status": EMBEDDING_STATUS_PENDING
        }
        products_data.append(product_dict)
    
    # Store products in RDS (synchronous)
    rds = get_rds_client()
    rds.create_products_batch(products_data)
    
    # Queue background processing
    background_tasks.add_task(
        process_catalog_batch,
        request.store_id,
        products_data
    )
    
    return CatalogResponse(
        job_id=job_id,
        status="processing",
        total_products=len(request.products),
        message="Catalog ingestion started. Products are being processed in the background."
    )
