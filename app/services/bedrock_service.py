"""AWS Bedrock service for Nova model invocations."""

import json
import base64
from typing import Optional, List

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import BedrockException, EmbeddingException
from app.core.logging import get_logger

logger = get_logger(__name__)


class BedrockService:
    """Service for AWS Bedrock model invocations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.region = self.settings.AWS_REGION
        self.nova_lite_model_id = self.settings.BEDROCK_NOVA_LITE_MODEL_ID
        self.embedding_model_id = self.settings.BEDROCK_EMBEDDING_MODEL_ID
        
        # Initialize Bedrock client
        self._init_client()
    
    def _init_client(self):
        """Initialize Bedrock runtime client."""
        session_kwargs = {"region_name": self.region}
        
        # Use explicit credentials if provided, otherwise use IAM role
        if self.settings.AWS_ACCESS_KEY_ID and self.settings.AWS_SECRET_ACCESS_KEY:
            session_kwargs.update({
                "aws_access_key_id": self.settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": self.settings.AWS_SECRET_ACCESS_KEY,
            })
        
        session = boto3.Session(**session_kwargs)
        self.bedrock_client = session.client("bedrock-runtime")
        logger.info("bedrock_client_initialized", region=self.region)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=lambda e: isinstance(e, (ClientError, BotoCoreError))
    )
    async def invoke_nova_lite(
        self,
        image_bytes: bytes,
        system_prompt: str,
        user_prompt: str = "Analyze this product image."
    ) -> str:
        """Invoke Amazon Nova Lite for image analysis.
        
        Args:
            image_bytes: Raw image bytes
            system_prompt: System prompt for the model
            user_prompt: User message
            
        Returns:
            Model response text
            
        Raises:
            BedrockException: If invocation fails
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            
            # Detect image format
            import imghdr
            image_format = imghdr.what(None, image_bytes) or "jpeg"
            if image_format == "jpg":
                image_format = "jpeg"
            
            # Build message content
            messages = [{
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": image_format,
                            "source": {
                                "bytes": image_base64
                            }
                        }
                    },
                    {
                        "text": user_prompt
                    }
                ]
            }]
            
            # Prepare request body
            body = {
                "messages": messages,
                "system": [{"text": system_prompt}],
                "inferenceConfig": {
                    "temperature": 0.3,
                    "maxTokens": 1024
                }
            }
            
            logger.debug("invoking_nova_lite", model=self.nova_lite_model_id)
            
            # Invoke model
            response = self.bedrock_client.invoke_model(
                modelId=self.nova_lite_model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            
            # Extract text from response
            output_message = response_body.get("output", {}).get("message", {})
            content_items = output_message.get("content", [])
            
            text_response = ""
            for item in content_items:
                if "text" in item:
                    text_response += item["text"]
            
            logger.info("nova_lite_invocation_success", model=self.nova_lite_model_id)
            return text_response.strip()
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error("nova_lite_client_error", error_code=error_code, error_message=error_message)
            raise BedrockException(f"Bedrock client error: {error_message}")
        except Exception as e:
            logger.error("nova_lite_invocation_error", error=str(e))
            raise BedrockException(f"Failed to invoke Nova Lite: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=lambda e: isinstance(e, (ClientError, BotoCoreError))
    )
    async def generate_text_embedding(self, text: str) -> List[float]:
        """Generate text embedding using Amazon Nova Multimodal Embeddings.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector (1024 dimensions)
            
        Raises:
            EmbeddingException: If generation fails
        """
        try:
            # Trim text if too long
            max_length = 8000
            if len(text) > max_length:
                text = text[:max_length]
                logger.warning("text_truncated_for_embedding", original_length=len(text))
            
            # Prepare request body
            body = {
                "inputText": text,
                "embeddingConfig": {
                    "outputEmbeddingLength": 1024
                }
            }
            
            logger.debug("generating_text_embedding", model=self.embedding_model_id, text_length=len(text))
            
            # Invoke model
            response = self.bedrock_client.invoke_model(
                modelId=self.embedding_model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding", [])
            
            if not embedding:
                raise EmbeddingException("Empty embedding returned from model")
            
            logger.info("text_embedding_generated", dimensions=len(embedding))
            return embedding
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error("text_embedding_client_error", error_code=error_code, error_message=error_message)
            raise EmbeddingException(f"Bedrock client error: {error_message}")
        except Exception as e:
            logger.error("text_embedding_error", error=str(e))
            raise EmbeddingException(f"Failed to generate text embedding: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=lambda e: isinstance(e, (ClientError, BotoCoreError))
    )
    async def generate_image_embedding(self, image_bytes: bytes) -> List[float]:
        """Generate image embedding using Amazon Nova Multimodal Embeddings.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Embedding vector (1024 dimensions)
            
        Raises:
            EmbeddingException: If generation fails
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            
            # Detect image format
            import imghdr
            image_format = imghdr.what(None, image_bytes) or "jpeg"
            if image_format == "jpg":
                image_format = "jpeg"
            
            # Prepare request body
            body = {
                "inputImage": {
                    "format": image_format,
                    "source": {
                        "bytes": image_base64
                    }
                },
                "embeddingConfig": {
                    "outputEmbeddingLength": 1024
                }
            }
            
            logger.debug("generating_image_embedding", model=self.embedding_model_id, format=image_format)
            
            # Invoke model
            response = self.bedrock_client.invoke_model(
                modelId=self.embedding_model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding", [])
            
            if not embedding:
                raise EmbeddingException("Empty embedding returned from model")
            
            logger.info("image_embedding_generated", dimensions=len(embedding))
            return embedding
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error("image_embedding_client_error", error_code=error_code, error_message=error_message)
            raise EmbeddingException(f"Bedrock client error: {error_message}")
        except Exception as e:
            logger.error("image_embedding_error", error=str(e))
            raise EmbeddingException(f"Failed to generate image embedding: {str(e)}")


# Singleton instance
_bedrock_service = None


def get_bedrock_service() -> BedrockService:
    """Get singleton Bedrock service instance."""
    global _bedrock_service
    if _bedrock_service is None:
        _bedrock_service = BedrockService()
    return _bedrock_service
