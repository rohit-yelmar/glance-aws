"""Pinecone client for vector storage and similarity search."""

from pinecone import Pinecone, ServerlessSpec

from app.config import get_settings
from app.core.exceptions import PineconeException
from app.core.logging import get_logger

logger = get_logger(__name__)

# Namespace constants
TEXT_EMBEDDINGS_NAMESPACE = "text-embeddings"
IMAGE_EMBEDDINGS_NAMESPACE = "image-embeddings"


class PineconeClient:
    """Client for Pinecone vector database operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.pc = self._create_client()
        self.index = self.pc.Index(self.settings.PINECONE_INDEX_NAME)
    
    def _create_client(self) -> Pinecone:
        """Create Pinecone client with API key."""
        return Pinecone(api_key=self.settings.PINECONE_API_KEY)
    
    def create_index(self) -> bool:
        """Create Pinecone index if it doesn't exist.
        
        Returns:
            True if index created or already exists
        """
        settings = self.settings
        index_name = settings.PINECONE_INDEX_NAME
        
        # Check if index exists
        existing_indexes = self.pc.list_indexes()
        if index_name in [idx.name for idx in existing_indexes]:
            logger.info("index_already_exists", index=index_name)
            return True
        
        # Create index with serverless spec
        try:
            self.pc.create_index(
                name=index_name,
                dimension=settings.EMBEDDING_DIMENSIONS,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=settings.PINECONE_CLOUD,
                    region=settings.PINECONE_REGION
                )
            )
            logger.info("index_created", index=index_name)
            return True
        except Exception as e:
            logger.error("index_creation_error", index=index_name, error=str(e))
            raise PineconeException(f"Failed to create index: {str(e)}")
    
    def upsert_product(
        self,
        product_id: str,
        store_id: str,
        text_embedding: list,
        image_embedding: list,
        combined_text: str,
        metadata: dict = None
    ) -> bool:
        """Upsert product embeddings to both namespaces.
        
        Args:
            product_id: Product identifier
            store_id: Store identifier
            text_embedding: Text embedding vector
            image_embedding: Image embedding vector
            combined_text: Combined text for reference
            metadata: Optional metadata dict with category, price, color
            
        Returns:
            True if upserted successfully
        """
        # Prepare metadata
        base_metadata = {
            "product_id": product_id,
            "store_id": store_id,
            "combined_text": combined_text,
        }
        
        if metadata:
            base_metadata.update({
                "category": metadata.get("category"),
                "price": metadata.get("price"),
                "color": metadata.get("color")
            })
        
        try:
            # Upsert text embedding to text-embeddings namespace
            self.index.upsert(
                vectors=[{
                    "id": product_id,
                    "values": text_embedding,
                    "metadata": base_metadata
                }],
                namespace=TEXT_EMBEDDINGS_NAMESPACE
            )
            
            # Upsert image embedding to image-embeddings namespace
            self.index.upsert(
                vectors=[{
                    "id": product_id,
                    "values": image_embedding,
                    "metadata": base_metadata
                }],
                namespace=IMAGE_EMBEDDINGS_NAMESPACE
            )
            
            logger.info("product_embeddings_upserted", product_id=product_id)
            return True
            
        except Exception as e:
            logger.error("upsert_product_error", product_id=product_id, error=str(e))
            raise PineconeException(f"Failed to upsert product: {str(e)}")
    
    def query_similar(
        self,
        embedding: list,
        namespace: str,
        top_k: int = 10,
        store_id: str = None,
        filter_dict: dict = None
    ) -> list:
        """Query for similar vectors in a namespace.
        
        Args:
            embedding: Query embedding vector
            namespace: Namespace to query (text-embeddings or image-embeddings)
            top_k: Number of results to return
            store_id: Optional store filter
            filter_dict: Optional additional filters
            
        Returns:
            List of search results with product_id and score
        """
        # Build filter
        query_filter = {}
        if store_id:
            query_filter["store_id"] = {"$eq": store_id}
        if filter_dict:
            query_filter.update(filter_dict)
        
        try:
            # Query Pinecone
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                namespace=namespace,
                filter=query_filter if query_filter else None,
                include_metadata=True
            )
            
            # Format results
            formatted_results = []
            for match in results.matches:
                formatted_results.append({
                    "product_id": match.id,
                    "score": match.score,
                    "source": match.metadata or {}
                })
            
            logger.debug(
                "query_complete",
                namespace=namespace,
                top_k=top_k,
                results=len(formatted_results)
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error("query_similar_error", namespace=namespace, error=str(e))
            raise PineconeException(f"Query failed: {str(e)}")
    
    def search_by_text_embedding(
        self,
        embedding: list,
        k: int = 10,
        store_id: str = None
    ) -> list:
        """Search by text embedding similarity.
        
        Args:
            embedding: Query embedding vector
            k: Number of results
            store_id: Optional store filter
            
        Returns:
            List of search results with product_id and score
        """
        return self.query_similar(
            embedding=embedding,
            namespace=TEXT_EMBEDDINGS_NAMESPACE,
            top_k=k,
            store_id=store_id
        )
    
    def search_by_image_embedding(
        self,
        embedding: list,
        k: int = 10,
        store_id: str = None
    ) -> list:
        """Search by image embedding similarity.
        
        Args:
            embedding: Query embedding vector
            k: Number of results
            store_id: Optional store filter
            
        Returns:
            List of search results with product_id and score
        """
        return self.query_similar(
            embedding=embedding,
            namespace=IMAGE_EMBEDDINGS_NAMESPACE,
            top_k=k,
            store_id=store_id
        )
    
    def delete_product(self, product_id: str) -> bool:
        """Delete product embeddings from both namespaces.
        
        Args:
            product_id: Product identifier
            
        Returns:
            True if deleted
        """
        try:
            # Delete from text-embeddings namespace
            self.index.delete(ids=[product_id], namespace=TEXT_EMBEDDINGS_NAMESPACE)
            
            # Delete from image-embeddings namespace
            self.index.delete(ids=[product_id], namespace=IMAGE_EMBEDDINGS_NAMESPACE)
            
            logger.info("product_embeddings_deleted", product_id=product_id)
            return True
            
        except Exception as e:
            logger.error("delete_product_error", product_id=product_id, error=str(e))
            return False
    
    def health_check(self) -> bool:
        """Check Pinecone connectivity.
        
        Returns:
            True if Pinecone is accessible
        """
        try:
            stats = self.index.describe_index_stats()
            logger.debug("pinecone_health", stats=stats.to_dict() if hasattr(stats, 'to_dict') else str(stats))
            return True
        except Exception as e:
            logger.error("health_check_failed", error=str(e))
            return False


# Singleton instance
_pinecone_client = None


def get_pinecone_client() -> PineconeClient:
    """Get singleton Pinecone client instance."""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = PineconeClient()
    return _pinecone_client
