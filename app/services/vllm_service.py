"""vLLM service for Qwen model invocations via OpenAI-compatible API."""

import json
import base64
import os
from typing import Optional, List, Dict, Any

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import BedrockException, EmbeddingException
from app.core.logging import get_logger

logger = get_logger(__name__)


class VLLMService:
    """Service for Qwen model invocations via vLLM OpenAI-compatible API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.VLLM_BASE_URL
        self.vision_model = self.settings.VLLM_VISION_MODEL
        self.text_embedding_model = self.settings.VLLM_TEXT_EMBEDDING_MODEL
        self.image_embedding_model = self.settings.VLLM_IMAGE_EMBEDDING_MODEL
        self.api_key = self.settings.VLLM_API_KEY
        
        logger.info("vllm_service_initialized", 
                   base_url=self.base_url,
                   vision_model=self.vision_model,
                   text_embedding_model=self.text_embedding_model,
                   image_embedding_model=self.image_embedding_model)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=lambda e: isinstance(e, aiohttp.ClientError)
    )
    async def invoke_vision_model(
        self,
        image_bytes: bytes,
        system_prompt: str,
        user_prompt: str = "Analyze this product image."
    ) -> str:
        """Invoke Qwen2-VL for image analysis.
        
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
            
            # Qwen2-VL uses URL format for images in base64
            # Format: data:image/jpeg;base64,{base64_data}
            image_url = f"data:image/{image_format};base64,{image_base64}"
            
            # Build messages for Qwen2-VL
            # Qwen2-VL uses chat template similar to Qwen
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": user_prompt}
                    ]
                }
            ]
            
            # Prepare request body
            payload = {
                "model": self.vision_model,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.3,
                "stream": False
            }
            
            logger.debug("invoking_qwen_vision", model=self.vision_model)
            
            # Make API call
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error("vision_model_api_error", 
                                   status=response.status, 
                                   error=error_text)
                        raise BedrockException(f"vLLM API error: {error_text}")
                    
                    result = await response.json()
            
            # Extract text from response
            if "choices" in result and len(result["choices"]) > 0:
                text_response = result["choices"][0]["message"]["content"]
            else:
                raise BedrockException(f"Invalid response format: {result}")
            
            logger.info("vision_model_invocation_success", model=self.vision_model)
            return text_response.strip()
            
        except BedrockException:
            raise
        except Exception as e:
            logger.error("vision_model_invocation_error", error=str(e))
            raise BedrockException(f"Failed to invoke Qwen vision model: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=lambda e: isinstance(e, aiohttp.ClientError)
    )
    async def generate_text_embedding(self, text: str) -> List[float]:
        """Generate text embedding using e5-small-v2 or similar.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector
            
        Raises:
            EmbeddingException: If generation fails
        """
        try:
            # Trim text if too long
            max_length = 8000
            if len(text) > max_length:
                text = text[:max_length]
                logger.warning("text_truncated_for_embedding", original_length=len(text))
            
            # Prepare request body for embeddings API
            payload = {
                "model": self.text_embedding_model,
                "input": text,
                "encoding_format": "float"
            }
            
            logger.debug("generating_text_embedding", 
                        model=self.text_embedding_model, 
                        text_length=len(text))
            
            # Make API call
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/embeddings",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error("embedding_api_error", 
                                   status=response.status, 
                                   error=error_text)
                        raise EmbeddingException(f"vLLM API error: {error_text}")
                    
                    result = await response.json()
            
            # Extract embedding from response
            if "data" in result and len(result["data"]) > 0:
                embedding = result["data"][0]["embedding"]
            else:
                raise EmbeddingException(f"Invalid embedding response format: {result}")
            
            if not embedding:
                raise EmbeddingException("Empty embedding returned from model")
            
            logger.info("text_embedding_generated", dimensions=len(embedding))
            return embedding
            
        except EmbeddingException:
            raise
        except Exception as e:
            logger.error("text_embedding_error", error=str(e))
            raise EmbeddingException(f"Failed to generate text embedding: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=lambda e: isinstance(e, aiohttp.ClientError)
    )
    async def generate_image_embedding(self, image_bytes: bytes) -> List[float]:
        """Generate image embedding using CLIP model via vLLM.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Embedding vector
            
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
            
            # Prepare request body for image embeddings
            # Using CLIP model for image embeddings
            image_url = f"data:image/{image_format};base64,{image_base64}"
            
            payload = {
                "model": self.image_embedding_model,
                "input": image_url,
                "encoding_format": "float"
            }
            
            logger.debug("generating_image_embedding", 
                        model=self.image_embedding_model, 
                        format=image_format)
            
            # Make API call
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/embeddings",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error("image_embedding_api_error", 
                                   status=response.status, 
                                   error=error_text)
                        raise EmbeddingException(f"vLLM API error: {error_text}")
                    
                    result = await response.json()
            
            # Extract embedding from response
            if "data" in result and len(result["data"]) > 0:
                embedding = result["data"][0]["embedding"]
            else:
                raise EmbeddingException(f"Invalid embedding response format: {result}")
            
            if not embedding:
                raise EmbeddingException("Empty embedding returned from model")
            
            logger.info("image_embedding_generated", dimensions=len(embedding))
            return embedding
            
        except EmbeddingException:
            raise
        except Exception as e:
            logger.error("image_embedding_error", error=str(e))
            raise EmbeddingException(f"Failed to generate image embedding: {str(e)}")


# Singleton instance
_vllm_service = None


def get_vllm_service() -> VLLMService:
    """Get singleton vLLM service instance."""
    global _vllm_service
    if _vllm_service is None:
        _vllm_service = VLLMService()
    return _vllm_service
