"""Embedding service for generating text and image embeddings."""

from typing import List

from app.config import get_settings
from app.core.logging import get_logger
from app.services.bedrock_service import get_bedrock_service
from app.utils.text_utils import sanitize_text

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating multimodal embeddings."""
    
    def __init__(self):
        self.bedrock = get_bedrock_service()
        self.settings = get_settings()
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate text embedding in unified latent space.
        
        Args:
            text: Input text to embed
            
        Returns:
            1024-dimension embedding vector
        """
        # Sanitize text
        clean_text = sanitize_text(text)
        
        logger.debug("embedding_text", length=len(clean_text))
        
        # Generate embedding via Bedrock
        embedding = await self.bedrock.generate_text_embedding(clean_text)
        
        # Validate dimensions
        if len(embedding) != self.settings.EMBEDDING_DIMENSIONS:
            logger.warning(
                "unexpected_embedding_dimensions",
                expected=self.settings.EMBEDDING_DIMENSIONS,
                actual=len(embedding)
            )
        
        logger.info("text_embedding_complete", dimensions=len(embedding))
        return embedding
    
    async def embed_image(self, image_bytes: bytes) -> List[float]:
        """Generate image embedding in unified latent space.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            1024-dimension embedding vector
        """
        logger.debug("embedding_image", size=len(image_bytes))
        
        # Generate embedding via Bedrock
        embedding = await self.bedrock.generate_image_embedding(image_bytes)
        
        # Validate dimensions
        if len(embedding) != self.settings.EMBEDDING_DIMENSIONS:
            logger.warning(
                "unexpected_embedding_dimensions",
                expected=self.settings.EMBEDDING_DIMENSIONS,
                actual=len(embedding)
            )
        
        logger.info("image_embedding_complete", dimensions=len(embedding))
        return embedding


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton Embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
