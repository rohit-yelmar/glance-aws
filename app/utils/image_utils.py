"""Image download and processing utilities."""

import base64
from io import BytesIO
from typing import Optional, Tuple

import httpx
from PIL import Image

from app.config import get_settings
from app.core.exceptions import ImageDownloadException
from app.core.logging import get_logger

logger = get_logger(__name__)


async def download_image(url: str, timeout: Optional[int] = None) -> bytes:
    """Download image from URL.
    
    Args:
        url: Image URL to download
        timeout: Download timeout in seconds
        
    Returns:
        Image bytes
        
    Raises:
        ImageDownloadException: If download fails
    """
    settings = get_settings()
    timeout = timeout or settings.IMAGE_DOWNLOAD_TIMEOUT
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            content = response.content
            
            # Check size limit
            if len(content) > settings.MAX_IMAGE_SIZE:
                raise ImageDownloadException(
                    f"Image size {len(content)} exceeds maximum {settings.MAX_IMAGE_SIZE}"
                )
            
            logger.debug("image_downloaded", url=url, size=len(content))
            return content
            
    except httpx.HTTPStatusError as e:
        logger.error("image_download_http_error", url=url, status=e.response.status_code)
        raise ImageDownloadException(f"HTTP error {e.response.status_code} downloading image")
    except httpx.TimeoutException:
        logger.error("image_download_timeout", url=url, timeout=timeout)
        raise ImageDownloadException(f"Timeout downloading image after {timeout}s")
    except Exception as e:
        logger.error("image_download_error", url=url, error=str(e))
        raise ImageDownloadException(f"Failed to download image: {str(e)}")


def validate_image(image_bytes: bytes) -> Tuple[bool, str]:
    """Validate image format and size.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        
        # Check format
        if img.format not in ["JPEG", "JPG", "PNG", "WEBP"]:
            return False, f"Unsupported format: {img.format}"
        
        # Check dimensions
        width, height = img.size
        max_dim = get_settings().MAX_IMAGE_DIMENSION
        if width > max_dim or height > max_dim:
            return False, f"Image dimensions {width}x{height} exceed maximum {max_dim}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Invalid image: {str(e)}"


def resize_if_needed(image_bytes: bytes, max_size: Tuple[int, int] = (1024, 1024)) -> bytes:
    """Resize image if it exceeds maximum dimensions.
    
    Args:
        image_bytes: Raw image bytes
        max_size: Maximum (width, height)
        
    Returns:
        Resized image bytes
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        
        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # Resize if needed
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = BytesIO()
        img.save(output, format="JPEG", quality=85)
        return output.getvalue()
        
    except Exception as e:
        logger.error("image_resize_error", error=str(e))
        # Return original if resize fails
        return image_bytes


def encode_image_base64(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Base64 encoded string
    """
    return base64.b64encode(image_bytes).decode("utf-8")


def get_image_format(image_bytes: bytes) -> Optional[str]:
    """Detect image format from bytes.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Image format string or None
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        return img.format
    except Exception:
        return None
