# Glance - Visual Semantic Search Backend
## Requirements Document

---

## 1. Executive Summary

**Product:** Glance  
**Domain:** AI for Retail, Commerce & Market Intelligence  
**Version:** 1.0.0  
**Date:** February 2026

Glance is a visual semantic search backend system that enables fashion e-commerce platforms to understand natural, vibe-based product queries (e.g., "summer solid light blue linen shirt") and return semantically relevant products using a unified multimodal embedding space.

---

## 2. Problem Statement

### 2.1 Current Pain Points
- Traditional keyword-based search fails on semantic queries
- Customers cannot find products that exist in catalog
- Vibe-based queries ("elegant evening dress", "casual summer wear") return poor results
- Lost sales due to poor product discoverability

### 2.2 Target Users
- Fashion e-commerce platforms (Shopify stores, Indian fashion apps)
- Product catalog owners with 1,000+ items
- Marketplaces seeking enhanced search capabilities

---

## 3. Solution Architecture

### 3.1 Core Concept
A dual-path embedding system combining:
1. **Vision Understanding**: Deep image analysis via Amazon Nova 2 Lite
2. **Unified Latent Space**: Multimodal embeddings (text + image) via Amazon Nova Multimodal Embeddings
3. **Hybrid Retrieval**: Reciprocal Rank Fusion (RRF) merging for optimal results

### 3.2 Data Flow Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING PIPELINE                               │
└─────────────────────────────────────────────────────────────────────────────┘

  Catalog Ingestion          Image Analysis           Embedding Generation
  ─────────────────          ─────────────            ───────────────────
  POST /ingest-catalog       Nova 2 Lite Vision       Nova Multimodal
       │                           │                       │
       ▼                           ▼                       ▼
  ┌─────────┐                ┌──────────┐            ┌──────────────┐
  │ Product │──Image URL────▶│ Generate │──Text─────▶│   Generate   │
  │ Metadata│                │  Tags    │            │  Embeddings  │
  └─────────┘                └──────────┘            └──────────────┘
       │                                                    │
       │                                                    │
       ▼                                                    ▼
   ┌─────────────────┐                              ┌─────────────────┐
   │   Amazon RDS    │                              │    Pinecone     │
   │  (PostgreSQL)   │                              │  (Vector DB)    │
   │  Product Store  │                              │  Serverless     │
   └─────────────────┘                              └─────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                              RETRIEVAL FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  User Query                                            Results
  ──────────                                            ───────
  POST /search
  "summer solid light
   blue linen shirt"              Query Embedding
       │                               │
       ▼                               ▼
  ┌─────────┐                   ┌──────────────┐
  │  Query  │──────────────────▶│ Nova Multimodal
  │  Text   │                   │  Embeddings  │
  └─────────┘                   └──────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              ┌──────────┐      ┌──────────┐        ┌──────────┐
              │  Text    │      │  Image   │        │   RRF    │
              │ Similarity      │ Similarity        │  Merge   │
              │  Search  │      │  Search  │        │Algorithm │
              └──────────┘      └──────────┘        └──────────┘
                    │                   │                   │
                    └───────────────────┴───────────────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │  Top 3 Products │
                              │  (Deduplicated) │
                              └─────────────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │  productId[]    │
                              │  Response       │
                              └─────────────────┘
```

---

## 4. Technical Requirements

### 4.1 Tech Stack
| Component | Technology |
|-----------|------------|
| Framework | FastAPI (Python) |
| Database | Amazon RDS (PostgreSQL) |
| Vector DB | Pinecone (Serverless) |
| Vision Model | Amazon Nova 2 Lite |
| Embeddings | Amazon Nova Multimodal Embeddings |
| AWS SDK | boto3 |
| Database Driver | psycopg2-binary |
| Vector Client | pinecone-python-client |
| Deployment | Amazon EC2 |

### 4.2 AWS Services Required

#### 4.2.1 Amazon Bedrock
- **Models**:
  - `amazon.nova-lite-v1` - For image analysis and attribute generation
  - `amazon.nova-embeddings-v1` - For multimodal embeddings (text + image in same latent space)
- **Region**: Same as other AWS services for latency optimization
- **IAM**: Bedrock invocation permissions

#### 4.2.2 Amazon RDS (PostgreSQL)
- **Engine**: PostgreSQL 15.x
- **Instance Class**: db.t3.micro (dev) / db.t3.small (prod)
- **Storage**: 20GB GP2
- **Purpose**: Store product metadata and catalog information
- **Tables**:
  - `products` - Core product information
  - `product_attributes` - Extended product attributes

#### 4.2.3 Pinecone Vector Database
- **Deployment**: Serverless on AWS
- **Region**: us-east-1 (should match other AWS services)
- **Index Name**: `glance-index`
- **Dimensions**: 1024 (matches Nova embedding dimensions)
- **Metric**: Cosine similarity
- **Purpose**: Vector storage and similarity search
- **Namespaces**:
  - `text-embeddings` - Stores text embeddings
  - `image-embeddings` - Stores image embeddings
- **Authentication**: API key-based (via `PINECONE_API_KEY`)
- **Filter Syntax**: MongoDB-style operators (e.g., `{"store_id": {"$eq": "..."}}`)
- **Query Method**: Cosine similarity search with metadata filtering

#### 4.2.4 Amazon EC2
- **Instance Type**: t3.medium (2 vCPU, 4GB RAM)
- **OS**: Amazon Linux 2023 / Ubuntu 22.04 LTS
- **Security Group**: Ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (FastAPI)
- **IAM Role**: EC2 instance profile with access to Bedrock, RDS
- **Note**: Pinecone uses API key authentication (not AWS IAM)

---

## 5. API Specifications

### 5.1 Endpoint Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest-catalog` | Ingest product catalog for processing |
| POST | `/search` | Perform semantic product search |
| GET | `/health` | Health check endpoint |
| GET | `/product/{product_id}` | Get product details by ID |

### 5.2 Detailed Endpoint Specifications

#### 5.2.1 POST /ingest-catalog

**Purpose**: Ingest a batch of products from the catalog for processing through the pipeline.

**Request Body**:
```json
{
  "store_id": "string",
  "products": [
    {
      "product_id": "string",
      "name": "string",
      "description": "string",
      "price": 0.0,
      "currency": "string",
      "category": "string",
      "tags": ["string"],
      "attributes": {
        "color": "string",
        "size": "string",
        "material": "string"
      },
      "image_url": "string (S3 public URL)",
      "additional_images": ["string"]
    }
  ]
}
```

**Response (202 Accepted)**:
```json
{
  "job_id": "uuid",
  "status": "processing",
  "total_products": 0,
  "message": "Catalog ingestion started"
}
```

**Processing Flow**:
1. Store product metadata in RDS
2. Download image from S3 URL
3. Send image to Nova 2 Lite for analysis
4. Generate vision-based attributes
5. Combine original + generated text
6. Generate multimodal embeddings (text + image)
7. Store embeddings in Pinecone with product_id metadata (text-embeddings and image-embeddings namespaces)

---

#### 5.2.2 POST /search

**Purpose**: Perform semantic search using natural language query.

**Request Body**:
```json
{
  "query": "summer solid light blue linen shirt",
  "store_id": "string (optional)",
  "filters": {
    "category": "string",
    "price_min": 0.0,
    "price_max": 0.0,
    "color": "string"
  },
  "limit": 3
}
```

**Response (200 OK)**:
```json
{
  "results": [
    {
      "product_id": "string",
      "name": "string",
      "description": "string",
      "price": 0.0,
      "image_url": "string",
      "confidence_score": 0.95,
      "match_type": "hybrid"
    }
  ],
  "total_results": 3,
  "query_embedding_time_ms": 150,
  "search_time_ms": 250
}
```

**Retrieval Algorithm**:
1. Generate query embedding using Nova Multimodal
2. Perform text-based similarity search in `text-embeddings` namespace (top_k=10)
3. Perform image-based similarity search in `image-embeddings` namespace (top_k=10)
4. Apply RRF (Reciprocal Rank Fusion) to merge results:
   - Formula: `score = Σ(1 / (k + rank))` where k=60
5. Deduplicate by product_id
6. Return top N results

---

#### 5.2.3 GET /health

**Purpose**: Health check for monitoring and load balancers.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "pinecone": "connected",
    "bedrock": "available"
  },
  "timestamp": "2026-02-28T06:04:12Z"
}
```

---

#### 5.2.4 GET /product/{product_id}

**Purpose**: Retrieve full product details by ID.

**Response (200 OK)**:
```json
{
  "product_id": "string",
  "name": "string",
  "description": "string",
  "price": 0.0,
  "currency": "string",
  "category": "string",
  "tags": ["string"],
  "attributes": {},
  "image_url": "string",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

---

## 6. Data Models

### 6.1 Database Schema (RDS PostgreSQL)

#### Table: `products`
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) UNIQUE NOT NULL,
    store_id VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    category VARCHAR(255),
    tags TEXT[],
    attributes JSONB,
    image_url TEXT,
    additional_images TEXT[],
    vision_attributes JSONB,  -- Generated by Nova 2 Lite
    raw_vision_response TEXT,
    embedding_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_store_id ON products(store_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_embedding_status ON products(embedding_status);
```

### 6.2 Pinecone Index Schema

#### Index: `glance-index`

**Index Configuration**:
```json
{
  "index_name": "glance-index",
  "dimension": 1024,
  "metric": "cosine",
  "spec": {
    "serverless": {
      "cloud": "aws",
      "region": "us-east-1"
    }
  }
}
```

**Namespaces**:
- `text-embeddings` - Stores text embeddings
- `image-embeddings` - Stores image embeddings

**Vector Record Structure**:
```json
{
  "id": "shirt-001",
  "values": [0.023, -0.156, ...],
  "metadata": {
    "product_id": "shirt-001",
    "store_id": "store-001",
    "combined_text": "Product: Blue Linen Shirt...",
    "category": "shirts",
    "price": 59.99,
    "color": "blue"
  }
}
```

**Query Example**:
```python
results = index.query(
    vector=query_embedding,
    top_k=10,
    namespace="text-embeddings",
    filter={"store_id": {"$eq": "store-001"}},
    include_metadata=True
)
```

---

## 7. Processing Pipeline Details

### 7.1 Image Analysis Prompt (Nova 2 Lite)

**System Prompt**:
```
You are a fashion product analyst specializing in e-commerce catalog enrichment.
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

Format as JSON with these exact keys: visual_description, material, fit_style, 
occasion, season, color_analysis, pattern, vibe_keywords
```

**Example Output**:
```json
{
  "visual_description": "Light blue button-up shirt with spread collar and long sleeves",
  "material": "Linen blend, likely with cotton for structure",
  "fit_style": "Regular fit, slightly relaxed",
  "occasion": "Casual, smart-casual, beach wear",
  "season": "Summer, spring",
  "color_analysis": {
    "primary": "sky blue",
    "synonyms": ["light blue", "powder blue", "aqua blue", "pale blue"]
  },
  "pattern": "Solid, no visible pattern",
  "vibe_keywords": ["breezy", "relaxed", "coastal", "minimalist", "airy", 
                    "comfortable", "vacation", "casual elegance", "breathable"]
}
```

### 7.2 Text Combination Strategy

**Combined Text Format**:
```
Product: {name}
Description: {description}
Category: {category}
Tags: {comma-separated tags}
Attributes: {attributes as key-value}
Vision Analysis: {vision_attributes.visual_description}
Material: {vision_attributes.material}
Style: {vision_attributes.fit_style}
Occasion: {vision_attributes.occasion}
Season: {vision_attributes.season}
Color: {vision_attributes.color_analysis.primary} ({synonyms})
Pattern: {vision_attributes.pattern}
Vibe: {comma-separated vibe_keywords}
```

### 7.3 Embedding Generation

**Model**: Amazon Nova Multimodal Embeddings
- Text embeddings: 1024 dimensions
- Image embeddings: 1024 dimensions
- Same latent space for both modalities
- Distance metric: Cosine similarity

---

## 8. RRF (Reciprocal Rank Fusion) Algorithm

### 8.1 Formula
```python
def rrf_score(rank: int, k: int = 60) -> float:
    """
    Calculate RRF score for a given rank.
    k=60 is the constant that prevents top ranks from dominating.
    """
    return 1.0 / (k + rank)

def merge_results(text_results: List[Product], 
                  image_results: List[Product], 
                  k: int = 60) -> List[Product]:
    """
    Merge results from text and image searches using RRF.
    """
    scores = defaultdict(float)
    
    # Score from text search results
    for rank, product in enumerate(text_results, start=1):
        scores[product.id] += rrf_score(rank, k)
    
    # Score from image search results
    for rank, product in enumerate(image_results, start=1):
        scores[product.id] += rrf_score(rank, k)
    
    # Sort by combined score (descending)
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    
    # Return top N unique products
    return [get_product_by_id(pid) for pid in sorted_ids[:3]]
```

### 8.2 Deduplication Strategy
- Use `product_id` as unique identifier
- If same product appears in both text and image results, sum their RRF scores
- Return top 3 after deduplication and ranking

---

## 9. Non-Functional Requirements

### 9.1 Performance
- API Response Time (Search): < 500ms (p95)
- Catalog Ingestion Rate: > 10 products/minute (with image analysis)
- Concurrent Search Requests: Support 100 concurrent users

### 9.2 Scalability
- Support catalogs up to 100,000 products initially
- Horizontal scaling via EC2 Auto Scaling (future enhancement)

### 9.3 Security
- HTTPS only (via ALB or nginx)
- API Key authentication (optional for MVP)
- AWS IAM roles for service authentication (no hardcoded credentials)

### 9.4 Reliability
- Health check endpoint for monitoring
- Graceful degradation if Bedrock/Pinecone temporarily unavailable
- Retry logic for transient AWS service failures (max 3 retries with exponential backoff)

---

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| Search Relevance (Human Evaluation) | > 80% top-3 relevance |
| API Uptime | > 99% |
| Average Search Latency | < 300ms |
| Catalog Processing Success Rate | > 95% |

---

## 11. Out of Scope (Future Enhancements)

- Real-time catalog synchronization (webhooks)
- A/B testing framework for search results
- User behavior tracking and learning
- Multi-language support
- Advanced filtering (size availability, inventory)
- Recommendation engine ("You might also like")
- Kubernetes/Docker containerization
- Automated model fine-tuning

---

## 12. Glossary

| Term | Definition |
|------|------------|
| **Latent Space** | A mathematical space where similar items are positioned closer together |
| **Embedding** | A numerical vector representation of text or image |
| **k-NN** | k-Nearest Neighbors - algorithm for finding similar vectors |
| **Namespace** | Logical separation within a Pinecone index for different vector types |
| **RRF** | Reciprocal Rank Fusion - algorithm for merging ranked lists |
| **Cosine Similarity** | Measure of similarity between two vectors |

---

**Document Owner:** Glance Engineering Team  
**Last Updated:** February 2026  
**Status:** Draft v1.0
