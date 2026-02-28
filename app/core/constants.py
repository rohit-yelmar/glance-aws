"""Application constants."""

# Vision Analysis Prompt
VISION_ANALYSIS_PROMPT = """You are a fashion product analyst specializing in e-commerce catalog enrichment.
Analyze the provided product image and extract detailed attributes for semantic search.

Provide a structured analysis including:
1. Visual Description: Detailed description of what is visible
2. Material/Fabric: Inferred fabric type (cotton, linen, silk, polyester, etc.)
3. Fit/Style: Fit type (slim, regular, loose, oversized) and style descriptors
4. Occasion: Suitable occasions (casual, formal, business, party, etc.)
5. Season: Appropriate seasons (summer, winter, all-season, etc.)
6. Color Analysis: Primary color and secondary/accent colors with synonyms
7. Pattern: Pattern type (solid, striped, floral, checkered, etc.)
8. Vibe/Keywords: 10-15 descriptive keywords capturing the aesthetic

Respond ONLY with a valid JSON object containing these exact keys:
- visual_description (string)
- material (string)
- fit_style (string)
- occasion (string)
- season (string)
- color_analysis (object with "primary" and "synonyms" array)
- pattern (string)
- vibe_keywords (array of strings)

Do not include markdown formatting, explanations, or any text outside the JSON."""

# Embedding Status
EMBEDDING_STATUS_PENDING = "pending"
EMBEDDING_STATUS_PROCESSING = "processing"
EMBEDDING_STATUS_COMPLETED = "completed"
EMBEDDING_STATUS_FAILED = "failed"

# Search Match Types
MATCH_TYPE_TEXT = "text"
MATCH_TYPE_IMAGE = "image"
MATCH_TYPE_HYBRID = "hybrid"

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1

# Image Processing
MAX_IMAGE_DIMENSION = 2048
SUPPORTED_IMAGE_FORMATS = ["JPEG", "JPG", "PNG", "WEBP"]

# OpenSearch
OPENSEARCH_DEFAULT_KNN_K = 10
OPENSEARCH_EF_SEARCH = 100
OPENSEARCH_EF_CONSTRUCTION = 128
OPENSEARCH_M = 24
