"""Custom exceptions for the Glance application."""


class GlanceException(Exception):
    """Base exception for Glance application."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class BedrockException(GlanceException):
    """Exception for AWS Bedrock service errors."""
    
    def __init__(self, message: str = "Bedrock service error"):
        super().__init__(message, status_code=503)


class ImageDownloadException(GlanceException):
    """Exception for image download failures."""
    
    def __init__(self, message: str = "Failed to download image"):
        super().__init__(message, status_code=400)


class DatabaseException(GlanceException):
    """Exception for database operations."""
    
    def __init__(self, message: str = "Database error"):
        super().__init__(message, status_code=500)


class VectorDBException(GlanceException):
    """Exception for vector database operations (Pinecone)."""
    
    def __init__(self, message: str = "Vector database error"):
        super().__init__(message, status_code=503)


# Backwards compatibility aliases
OpenSearchException = VectorDBException
PineconeException = VectorDBException


class EmbeddingException(GlanceException):
    """Exception for embedding generation failures."""
    
    def __init__(self, message: str = "Failed to generate embeddings"):
        super().__init__(message, status_code=503)


class VisionAnalysisException(GlanceException):
    """Exception for vision analysis failures."""
    
    def __init__(self, message: str = "Vision analysis failed"):
        super().__init__(message, status_code=503)


class ProductNotFoundException(GlanceException):
    """Exception when product is not found."""
    
    def __init__(self, product_id: str):
        super().__init__(f"Product not found: {product_id}", status_code=404)


class AuthenticationException(GlanceException):
    """Exception for authentication failures."""
    
    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, status_code=401)

class SearchServiceException(GlanceException):
    """Exception for search service errors."""
    
    def __init__(self, message: str = "Search service error"):
        super().__init__(message, status_code=503)
