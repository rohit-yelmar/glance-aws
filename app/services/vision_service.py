"""Vision service for product image analysis."""

import json
from typing import Dict, Any, Optional

from app.core.constants import VISION_ANALYSIS_PROMPT
from app.core.exceptions import VisionAnalysisException
from app.core.logging import get_logger
from app.services.bedrock_service import get_bedrock_service
from app.services.vllm_service import get_vllm_service

logger = get_logger(__name__)


class VisionService:
    """Service for analyzing product images using vision models."""
    
    def __init__(self):
        self.settings = get_settings()
        self.use_vllm = self.settings.USE_VLLM
        
        if self.use_vllm:
            self.vllm = get_vllm_service()
            logger.info("vision_service_using_vllm")
        else:
            self.bedrock = get_bedrock_service()
            logger.info("vision_service_using_bedrock")
    
    async def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Analyze product image and extract attributes.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary with extracted attributes
            
        Raises:
            VisionAnalysisException: If analysis fails
        """
        try:
            logger.info("starting_image_analysis", image_size=len(image_bytes))
            
            # Call vLLM Qwen or Bedrock Nova Lite
            if self.use_vllm:
                response_text = await self.vllm.invoke_vision_model(
                    image_bytes=image_bytes,
                    system_prompt=VISION_ANALYSIS_PROMPT,
                    user_prompt="Analyze this fashion product image and provide structured attributes."
                )
            else:
                response_text = await self.bedrock.invoke_nova_lite(
                    image_bytes=image_bytes,
                    system_prompt=VISION_ANALYSIS_PROMPT,
                    user_prompt="Analyze this fashion product image and provide structured attributes."
                )
            
            # Parse JSON response
            try:
                # Try to find JSON in the response (in case there's extra text)
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    attributes = json.loads(json_str)
                else:
                    # Try to parse the whole response
                    attributes = json.loads(response_text)
                
                logger.info("image_analysis_complete", 
                          has_visual="visual_description" in attributes,
                          has_material="material" in attributes,
                          vibe_count=len(attributes.get("vibe_keywords", [])))
                
                return attributes
                
            except json.JSONDecodeError as e:
                logger.error("json_parse_error", response=response_text[:500], error=str(e))
                # Return raw response for debugging
                return {
                    "raw_response": response_text,
                    "parse_error": str(e),
                    "visual_description": "Failed to parse vision analysis",
                    "vibe_keywords": []
                }
                
        except Exception as e:
            logger.error("image_analysis_error", error=str(e))
            raise VisionAnalysisException(f"Failed to analyze image: {str(e)}")
    
    def validate_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize vision attributes.
        
        Args:
            attributes: Raw attributes from vision model
            
        Returns:
            Normalized attributes with defaults
        """
        defaults = {
            "visual_description": "",
            "material": "",
            "fit_style": "",
            "occasion": "",
            "season": "",
            "color_analysis": {"primary": "", "synonyms": []},
            "pattern": "",
            "vibe_keywords": []
        }
        
        # Merge with defaults
        normalized = {**defaults, **attributes}
        
        # Ensure vibe_keywords is a list
        if not isinstance(normalized.get("vibe_keywords"), list):
            normalized["vibe_keywords"] = []
        
        # Ensure color_analysis has required fields
        if not isinstance(normalized.get("color_analysis"), dict):
            normalized["color_analysis"] = {"primary": "", "synonyms": []}
        
        return normalized


# Singleton instance
_vision_service = None


def get_vision_service() -> VisionService:
    """Get singleton Vision service instance."""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service
