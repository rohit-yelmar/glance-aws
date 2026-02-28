"""Text processing utilities."""

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


def combine_product_text(
    name: str,
    description: Optional[str],
    category: Optional[str],
    tags: List[str],
    attributes: Dict[str, Any],
    vision_attrs: Optional[Dict[str, Any]]
) -> str:
    """Combine product metadata with vision attributes into a single text chunk.
    
    Args:
        name: Product name
        description: Product description
        category: Product category
        tags: Product tags
        attributes: Product attributes dict
        vision_attrs: Vision analysis attributes
        
    Returns:
        Combined text string for embedding
    """
    parts = []
    
    # Base product info
    parts.append(f"Product: {name}")
    
    if description:
        parts.append(f"Description: {description}")
    
    if category:
        parts.append(f"Category: {category}")
    
    if tags:
        parts.append(f"Tags: {', '.join(tags)}")
    
    if attributes:
        attr_str = ', '.join(f"{k}={v}" for k, v in attributes.items())
        parts.append(f"Attributes: {attr_str}")
    
    # Vision attributes
    if vision_attrs:
        if visual_desc := vision_attrs.get("visual_description"):
            parts.append(f"Visual: {visual_desc}")
        
        if material := vision_attrs.get("material"):
            parts.append(f"Material: {material}")
        
        if fit_style := vision_attrs.get("fit_style"):
            parts.append(f"Style: {fit_style}")
        
        if occasion := vision_attrs.get("occasion"):
            parts.append(f"Occasion: {occasion}")
        
        if season := vision_attrs.get("season"):
            parts.append(f"Season: {season}")
        
        # Color with synonyms
        if color_analysis := vision_attrs.get("color_analysis"):
            if isinstance(color_analysis, dict):
                primary = color_analysis.get("primary", "")
                synonyms = color_analysis.get("synonyms", [])
                if primary:
                    if synonyms:
                        parts.append(f"Color: {primary} ({', '.join(synonyms)})")
                    else:
                        parts.append(f"Color: {primary}")
        
        if pattern := vision_attrs.get("pattern"):
            parts.append(f"Pattern: {pattern}")
        
        if vibe_keywords := vision_attrs.get("vibe_keywords"):
            if isinstance(vibe_keywords, list):
                parts.append(f"Vibe: {', '.join(vibe_keywords)}")
    
    combined = " | ".join(parts)
    logger.debug("combined_product_text", product_name=name, length=len(combined))
    
    return combined


def sanitize_text(text: str) -> str:
    """Clean and sanitize text for embedding.
    
    Args:
        text: Input text
        
    Returns:
        Sanitized text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Trim to reasonable length (Nova has token limits)
    max_length = 8000  # Conservative limit
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning("text_truncated", original_length=len(text), max_length=max_length)
    
    return text.strip()


def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text (simple implementation).
    
    Args:
        text: Input text
        
    Returns:
        List of keywords
    """
    # Simple keyword extraction - could be enhanced with NLP
    import re
    
    # Convert to lowercase and extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'for', 'are', 'with', 'they', 'this', 'that',
        'have', 'from', 'word', 'what', 'were', 'been', 'their',
        'there', 'each', 'which', 'will', 'about', 'could', 'other'
    }
    
    keywords = [w for w in words if w not in stop_words]
    
    # Return unique keywords preserving order
    seen = set()
    unique_keywords = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique_keywords.append(k)
    
    return unique_keywords[:20]  # Limit to top 20
