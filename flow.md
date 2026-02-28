# Glance Backend - Data Flow Documentation

Complete data flow documentation for the Glance visual semantic search system, explaining all functions, files, and the journey from catalog ingestion to search retrieval.

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Catalog Ingestion Pipeline](#2-catalog-ingestion-pipeline)
3. [Search Retrieval Pipeline](#3-search-retrieval-pipeline)
4. [Module-by-Module Function Reference](#4-module-by-module-function-reference)
5. [Data Transformations](#5-data-transformations)
6. [API Endpoint Flow](#6-api-endpoint-flow)

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              GLANCE BACKEND                                      │
│                                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Next.js     │    │   FastAPI    │    │   Amazon     │    │   Amazon     │  │
│  │  Frontend    │───▶│   Backend    │───▶│   Bedrock    │    │   RDS        │  │
│  │  (External)  │◀───│   (This App) │◀───│   (Nova AI)  │    │ (PostgreSQL) │  │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘  │
│                              │                        │    ┌──────────────┐   │
│                              │                        └───▶│   Amazon     │   │
│                              │                             │   OpenSearch │   │
│                              └─────────────────────────────▶│  (Vector DB) │   │
│                                                             └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Catalog Ingestion Pipeline

### 2.1 Overview
When a store sends their product catalog, the system processes each product through a pipeline that generates AI-powered embeddings for semantic search.

### 2.2 Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         CATALOG INGESTION PIPELINE                                   │
└─────────────────────────────────────────────────────────────────────────────────────┘

   Frontend Request                    FastAPI Layer                        Services
   ────────────────                    ─────────────                        ─────────
         │                                   │                                  │
         │  POST /ingest-catalog             │                                  │
         │  {                              │                                  │
         │    store_id,                    │                                  │
         │    products: [                  │                                  │
         │      {                          │                                  │
         │        product_id,              │                                  │
         │        name,                    │                                  │
         │        image_url (S3)           │                                  │
         │      }                          │                                  │
         │    ]                            │                                  │
         │  }                              │                                  │
         │──────────────────────────────▶│                                  │
         │                                   │                                  │
         │                                   │  1. Validate Request            │
         │                                   │     (CatalogRequest schema)     │
         │                                   │                                  │
         │                                   │  2. Batch Insert to RDS         │
         │                                   │     (Sync - Immediate)        │
         │                                   │────────▶ RDSClient            │
         │                                   │            .create_products_batch()
         │                                   │◀────────── Status: pending    │
         │                                   │                                  │
         │                                   │  3. Queue Background Task       │
         │                                   │                                  │
         │  202 Accepted                   │                                  │
         │  { job_id, status, total }      │                                  │
         │◀───────────────────────────────│                                  │
         │                                   │                                  │
         │                                   │  BACKGROUND PROCESSING         │
         │                                   │  (Per Product)                 │
         │                                   │                                  │
         │                                   │  process_product()             │
         │                                   │       │                        │
         │                                   │       ▼                        │
         │                                   │  ┌─────────────────────┐       │
         │                                   │  │ 1. Download Image   │       │
         │                                   │  │    image_utils.       │       │
         │                                   │  │    download_image()   │       │
         │                                   │  │         │             │       │
         │                                   │  │         ▼             │       │
         │                                   │  │  HTTP GET image_url   │       │
         │                                   │  └─────────────────────┘       │
         │                                   │       │                        │
         │                                   │       ▼                        │
         │                                   │  ┌─────────────────────┐       │
         │                                   │  │ 2. Vision Analysis    │◀──────┼──▶ BedrockService
         │                                   │  │    vision_service.  │       │      .invoke_nova_lite()
         │                                   │  │    analyze_image()    │       │      (Nova 2 Lite)
         │                                   │  │         │             │       │
         │                                   │  │    Generate:          │       │
         │                                   │  │    - visual_description│       │
         │                                   │  │    - material         │       │
         │                                   │  │    - fit_style        │       │
         │                                   │  │    - occasion         │       │
         │                                   │  │    - season           │       │
         │                                   │  │    - color_analysis   │       │
         │                                   │  │    - pattern          │       │
         │                                   │  │    - vibe_keywords    │       │
         │                                   │  └─────────────────────┘       │
         │                                   │       │                        │
         │                                   │       ▼                        │
         │                                   │  ┌─────────────────────┐       │
         │                                   │  │ 3. Update RDS       │◀──────┼──▶ RDSClient
         │                                   │  │    with Vision Attrs│       │      .update_vision_attributes()
         │                                   │  └─────────────────────┘       │
         │                                   │       │                        │
         │                                   │       ▼                        │
         │                                   │  ┌─────────────────────┐       │
         │                                   │  │ 4. Combine Text     │       │
         │                                   │  │    text_utils.        │       │
         │                                   │  │    combine_product_text()│    │
         │                                   │  │         │             │       │
         │                                   │  │    Product: name      │       │
         │                                   │  │    Description: desc │       │
         │                                   │  │    Category: cat      │       │
         │                                   │  │    Tags: [t1, t2]     │       │
         │                                   │  │    + Vision Attributes│       │
         │                                   │  │    = Combined Text    │       │
         │                                   │  └─────────────────────┘       │
         │                                   │       │                        │
         │                                   │       ▼                        │
         │                                   │  ┌─────────────────────┐       │
         │                                   │  │ 5. Generate         │◀──────┼──▶ BedrockService
         │                                   │  │    Embeddings       │       │      (Nova Multimodal)
         │                                   │  │    embedding_service. │     │
         │                                   │  │    embed_text()       │     │      .generate_text_embedding()
         │                                   │  │    embed_image()      │     │      .generate_image_embedding()
         │                                   │  │         │             │       │
         │                                   │  │    Text: 1024-dim     │       │
         │                                   │  │    Image: 1024-dim    │       │
         │                                   │  │    (Unified Space)    │       │
         │                                   │  └─────────────────────┘       │
         │                                   │       │                        │
         │                                   │       ▼                        │
         │                                   │  ┌─────────────────────┐       │
         │                                   │  │ 6. Index OpenSearch │◀──────┼──▶ OpenSearchClient
         │                                   │  │    opensearch.        │       │      .index_embedding()
         │                                   │  │    index_embedding()  │       │
         │                                   │  │         │             │       │
         │                                   │  │    Store:             │       │
         │                                   │  │    - product_id       │       │
         │                                   │  │    - text_embedding   │       │
         │                                   │  │    - image_embedding  │       │
         │                                   │  │    - combined_text    │       │
         │                                   │  │    - metadata         │       │
         │                                   │  └─────────────────────┘       │
         │                                   │       │                        │
         │                                   │       ▼                        │
         │                                   │  ┌─────────────────────┐       │
         │                                   │  │ 7. Update Status    │◀──────┼──▶ RDSClient
         │                                   │  │    Status: completed │       │      .update_embedding_status()
         │                                   │  └─────────────────────┘       │
         │                                   │                                  │
```

### 2.3 Key Functions - Catalog Ingestion

| File | Function | Purpose |
|------|----------|---------|
| `app/api/routes/catalog.py` | `ingest_catalog()` | Main endpoint handler, validates request, triggers background processing |
| `app/api/routes/catalog.py` | `verify_api_key()` | Authentication check via X-API-Key header |
| `app/api/routes/catalog.py` | `process_product()` | Background task orchestrating the full pipeline |
| `app/api/routes/catalog.py` | `process_catalog_batch()` | Batch processor handling multiple products |
| `app/utils/image_utils.py` | `download_image()` | Downloads image from S3/public URL via HTTP |
| `app/services/vision_service.py` | `analyze_image()` | Calls Nova Lite to extract visual attributes |
| `app/services/bedrock_service.py` | `invoke_nova_lite()` | Low-level Bedrock API call for image analysis |
| `app/utils/text_utils.py` | `combine_product_text()` | Merges metadata + vision attributes into single text |
| `app/services/embedding_service.py` | `embed_text()` | Generates text embedding (1024-dim) |
| `app/services/embedding_service.py` | `embed_image()` | Generates image embedding (1024-dim) |
| `app/db/rds_client.py` | `create_products_batch()` | Batch inserts products with pending status |
| `app/db/rds_client.py` | `update_vision_attributes()` | Stores AI-generated attributes |
| `app/db/rds_client.py` | `update_embedding_status()` | Updates processing status |
| `app/db/opensearch_client.py` | `index_embedding()` | Stores vectors in k-NN index |

---

## 3. Search Retrieval Pipeline

### 3.1 Overview
When a user searches, the query is converted to an embedding, and similar products are found using RRF (Reciprocal Rank Fusion) from both text and image embeddings.

### 3.2 Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          SEARCH RETRIEVAL PIPELINE                                   │
└─────────────────────────────────────────────────────────────────────────────────────┘

   Frontend Request                    FastAPI Layer                        Services
   ────────────────                    ─────────────                        ─────────
         │                                   │                                  │
         │  POST /search                     │                                  │
         │  {                              │                                  │
         │    query: "summer solid         │                                  │
         │             light blue         │                                  │
         │             linen shirt"        │                                  │
         │    store_id: "store-001"        │                                  │
         │    filters: {...}               │                                  │
         │    limit: 3                     │                                  │
         │  }                              │                                  │
         │──────────────────────────────▶│                                  │
         │                                   │                                  │
         │                                   │  1. Validate Request            │
         │                                   │     (SearchRequest schema)      │
         │                                   │     - query (required)          │
         │                                   │     - store_id (optional)       │
         │                                   │     - filters (optional)        │
         │                                   │     - limit (default: 3)        │
         │                                   │                                  │
         │                                   │  2. Generate Query Embedding    │
         │                                   │────────▶ embedding_service      │
         │                                   │            .embed_text()       │
         │                                   │◀────────── 1024-dim vector    │
         │                                   │                                  │
         │                                   │  3. Parallel Similarity Search  │
         │                                   │                                  │
         │                                   │  ┌─────────────────────────┐   │
         │                                   │  │  TEXT SEARCH            │   │
         │                                   │  │  opensearch.            │───┼──▶ .search_by_text_embedding()
         │                                   │  │  search_by_text_        │   │      (k-NN query)
         │                                   │  │  embedding(query_emb)   │   │      Returns top 10
         │                                   │  │                         │   │      [{product_id, score}]
         │                                   │  └─────────────────────────┘   │
         │                                   │              │                 │
         │                                   │              │ Parallel        │
         │                                   │              ▼                 │
         │                                   │  ┌─────────────────────────┐   │
         │                                   │  │  IMAGE SEARCH           │   │
         │                                   │  │  opensearch.            │───┼──▶ .search_by_image_embedding()
         │                                   │  │  search_by_image_       │   │      (k-NN query)
         │                                   │  │  embedding(query_emb)   │   │      Returns top 10
         │                                   │  │                         │   │      [{product_id, score}]
         │                                   │  └─────────────────────────┘   │
         │                                   │              │                 │
         │                                   │              ▼                 │
         │                                   │  ┌─────────────────────────┐   │
         │                                   │  │  4. RRF MERGE           │   │
         │                                   │  │  rrf_utils.             │   │
         │                                   │  │  rrf_merge()            │   │
         │                                   │  │                         │   │
         │                                   │  │  Formula:               │   │
         │                                   │  │  score = Σ(1/(k+rank)) │   │
         │                                   │  │  k=60 (constant)        │   │
         │                                   │  │                         │   │
         │                                   │  │  Example:               │   │
         │                                   │  │  Text rank: 2 → 1/62   │   │
         │                                   │  │  Image rank: 5 → 1/65   │   │
         │                                   │  │  Combined: 0.016 + 0.015│   │
         │                                   │  └─────────────────────────┘   │
         │                                   │              │                 │
         │                                   │              ▼                 │
         │                                   │  ┌─────────────────────────┐   │
         │                                   │  │  5. DEDUPLICATE & RANK  │   │
         │                                   │  │                         │   │
         │                                   │  │  Top N by RRF score     │   │
         │                                   │  │  N = limit (default 3)  │   │
         │                                   │  │                         │   │
         │                                   │  │  Result: [pid1, pid2,    │   │
         │                                   │  │          pid3]          │   │
         │                                   │  └─────────────────────────┘   │
         │                                   │              │                 │
         │                                   │              ▼                 │
         │                                   │  ┌─────────────────────────┐   │
         │                                   │  │  6. FETCH DETAILS       │───┼──▶ RDSClient
         │                                   │  │  rds.                   │   │      .get_products_by_ids()
         │                                   │  │  get_products_by_ids()  │   │      Returns full product
         │                                   │  │                         │   │      records from PostgreSQL
         │                                   │  └─────────────────────────┘   │
         │                                   │              │                 │
         │                                   │              ▼                 │
         │                                   │  ┌─────────────────────────┐   │
         │                                   │  │  7. BUILD RESPONSE      │   │
         │                                   │  │                         │   │
         │                                   │  │  For each product:      │   │
         │                                   │  │  - product_id           │   │
         │                                   │  │  - name                 │   │
         │                                   │  │  - description          │   │
         │                                   │  │  - price                │   │
         │                                   │  │  - image_url            │   │
         │                                   │  │  - confidence_score     │   │
         │                                   │  │    (RRF score)         │   │
         │                                   │  │  - match_type           │   │
         │                                   │  │    (text/image/hybrid) │   │
         │                                   │  └─────────────────────────┘   │
         │                                   │                                  │
         │  200 OK                         │                                  │
         │  {                              │                                  │
         │    results: [...],              │                                  │
         │    total_results: 3,            │                                  │
         │    query_embedding_time_ms: 150│                                  │
         │    search_time_ms: 250          │                                  │
         │  }                              │                                  │
         │◀───────────────────────────────│                                  │
         │                                   │                                  │
```

### 3.3 Key Functions - Search Retrieval

| File | Function | Purpose |
|------|----------|---------|
| `app/api/routes/search.py` | `search_products()` | Main endpoint handler |
| `app/api/routes/search.py` | `verify_api_key()` | Authentication check |
| `app/services/search_service.py` | `semantic_search()` | Orchestrates the entire search flow |
| `app/services/search_service.py` | `SearchService` | Main service class for search operations |
| `app/services/embedding_service.py` | `embed_text()` | Converts query text to 1024-dim embedding |
| `app/db/opensearch_client.py` | `search_by_text_embedding()` | k-NN search in text_embedding field |
| `app/db/opensearch_client.py` | `search_by_image_embedding()` | k-NN search in image_embedding field |
| `app/utils/rrf_utils.py` | `rrf_merge()` | Combines text + image results using RRF |
| `app/utils/rrf_utils.py` | `calculate_rrf_score()` | Computes 1/(k+rank) for a single result |
| `app/utils/rrf_utils.py` | `determine_match_type()` | Classifies match as text/image/hybrid |
| `app/db/rds_client.py` | `get_products_by_ids()` | Batch fetches product details from RDS |

---

## 4. Module-by-Module Function Reference

### 4.1 Configuration (`app/config.py`)

| Function/Class | Description |
|----------------|-------------|
| `Settings` | Pydantic Settings class, loads all env vars |
| `database_url` | Property, constructs PostgreSQL connection string |
| `opensearch_url` | Property, constructs OpenSearch URL |
| `get_settings()` | Returns cached Settings instance |

### 4.2 Database - RDS (`app/db/rds_client.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `init_db()` | None | None | Creates all SQL tables |
| `get_rds_client()` | None | RDSClient | Returns singleton client |
| `RDSClient.create_product()` | product_data dict | Product model | Insert single product |
| `RDSClient.create_products_batch()` | List[dict] | int count | Batch insert products |
| `RDSClient.get_product_by_id()` | product_id str | Product or None | Fetch single product |
| `RDSClient.get_products_by_ids()` | List[str] | List[Product] | Batch fetch by IDs |
| `RDSClient.update_vision_attributes()` | product_id, attrs | bool | Store vision results |
| `RDSClient.update_embedding_status()` | product_id, status | bool | Update processing status |
| `RDSClient.health_check()` | None | bool | Test connectivity |

### 4.3 Database - OpenSearch (`app/db/opensearch_client.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `get_opensearch_client()` | None | OpenSearchClient | Returns singleton client |
| `OpenSearchClient.create_index()` | None | bool | Creates k-NN enabled index |
| `OpenSearchClient.index_embedding()` | product_id, embeddings, metadata | bool | Stores vectors |
| `OpenSearchClient.search_by_text_embedding()` | embedding vector, k | List[results] | k-NN text search |
| `OpenSearchClient.search_by_image_embedding()` | embedding vector, k | List[results] | k-NN image search |
| `OpenSearchClient.delete_by_product_id()` | product_id | bool | Removes embedding |
| `OpenSearchClient.health_check()` | None | bool | Test connectivity |

### 4.4 Services - Bedrock (`app/services/bedrock_service.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `get_bedrock_service()` | None | BedrockService | Returns singleton |
| `BedrockService.__init__()` | None | None | Initializes boto3 client |
| `BedrockService.invoke_nova_lite()` | image_bytes, system_prompt | str (JSON) | Image analysis via Nova |
| `BedrockService.generate_text_embedding()` | text str | List[float] (1024-dim) | Text embedding |
| `BedrockService.generate_image_embedding()` | image_bytes | List[float] (1024-dim) | Image embedding |

### 4.5 Services - Vision (`app/services/vision_service.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `get_vision_service()` | None | VisionService | Returns singleton |
| `VisionService.analyze_image()` | image_bytes | Dict[attributes] | Extracts visual features |
| `VisionService.validate_attributes()` | raw_attrs | Normalized dict | Ensures required fields |

### 4.6 Services - Embedding (`app/services/embedding_service.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `get_embedding_service()` | None | EmbeddingService | Returns singleton |
| `EmbeddingService.embed_text()` | text str | List[float] | Text → 1024-dim vector |
| `EmbeddingService.embed_image()` | image_bytes | List[float] | Image → 1024-dim vector |

### 4.7 Services - Search (`app/services/search_service.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `get_search_service()` | None | SearchService | Returns singleton |
| `SearchService.semantic_search()` | query, store_id, filters, limit | Dict[results] | Full search pipeline |

### 4.8 Utilities - Image (`app/utils/image_utils.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `download_image()` | url str | bytes | HTTP download with timeout |
| `validate_image()` | image_bytes | Tuple[bool, str] | Check format/size |
| `resize_if_needed()` | image_bytes, max_size | bytes | Resize large images |
| `encode_image_base64()` | image_bytes | str | Base64 encoding |
| `get_image_format()` | image_bytes | str or None | Detect format |

### 4.9 Utilities - RRF (`app/utils/rrf_utils.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `calculate_rrf_score()` | rank int, k int | float | 1/(k+rank) |
| `rrf_merge()` | text_results, image_results | List[(id, score)] | Merged ranking |
| `deduplicate_by_id()` | List[(id, ...)] | List[(id, ...)] | Remove duplicates |
| `determine_match_type()` | product_id, text, image | str | text/image/hybrid |

### 4.10 Utilities - Text (`app/utils/text_utils.py`)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `combine_product_text()` | name, desc, attrs, vision | str | Merges all text |
| `sanitize_text()` | text str | str | Clean for embedding |
| `extract_keywords()` | text str | List[str] | Simple keyword extraction |

### 4.11 API Routes (`app/api/routes/`)

| File | Function | Method | Path | Description |
|------|----------|--------|------|-------------|
| `health.py` | `health_check()` | GET | `/health` | Service health check |
| `catalog.py` | `ingest_catalog()` | POST | `/ingest-catalog` | Product catalog ingestion |
| `catalog.py` | `process_product()` | Background | - | Single product pipeline |
| `search.py` | `search_products()` | POST | `/search` | Semantic search |
| `product.py` | `get_product()` | GET | `/product/{id}` | Product details |

---

## 5. Data Transformations

### 5.1 Product Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        PRODUCT DATA TRANSFORMATIONS                              │
└─────────────────────────────────────────────────────────────────────────────────┘

Input (API Request)                          Processing                        Output (Stored)
─────────────────                            ───────────                        ─────────────

CatalogRequest
{
  store_id: "store-001",
  products: [{
    product_id: "shirt-001",
    name: "Blue Linen Shirt",
    description: "Comfortable...",
    price: 59.99,
    category: "shirts",
    tags: ["linen", "blue"],
    attributes: {
      color: "blue",
      material: "linen"
    },
    image_url: "https://s3.../img.jpg"
  }]
}
                    │
                    │  1. RDS Insert
                    ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ RDS PostgreSQL (products table)                                                  │
│ ─────────────────────────────────                                                │
│ product_id: "shirt-001"                                                         │
│ store_id: "store-001"                                                           │
│ name: "Blue Linen Shirt"                                                         │
│ description: "Comfortable..."                                                    │
│ price: 59.99                                                                     │
│ category: "shirts"                                                               │
│ tags: ["linen", "blue"]                                                          │
│ attributes: {color: "blue", material: "linen"}                                   │
│ image_url: "https://s3.../img.jpg"                                               │
│ vision_attributes: null (pending)                                              │
│ embedding_status: "pending"                                                     │
└────────────────────────────────────────────────────────────────────────────────┘
                    │
                    │  2. Background Processing
                    │
                    │  2a. Vision Analysis
                    ▼
Bedrock Nova Lite Request
{
  image: <base64>,
  system: "You are a fashion analyst..."
}
                    │
                    ▼
Vision Response (JSON)
{
  visual_description: "Light blue button-up shirt...",
  material: "Linen blend",
  fit_style: "Regular fit",
  occasion: "Casual, smart-casual",
  season: "Summer, spring",
  color_analysis: {
    primary: "sky blue",
    synonyms: ["light blue", "powder blue"]
  },
  pattern: "Solid",
  vibe_keywords: ["breezy", "relaxed", "coastal"]
}
                    │
                    │  2b. Update RDS with Vision
                    ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ RDS Updated                                                                      │
│ ───────────                                                                      │
│ vision_attributes: {visual_description, material, ...}                          │
│ embedding_status: "processing"                                                  │
└────────────────────────────────────────────────────────────────────────────────┘
                    │
                    │  2c. Combine Text
                    ▼
Combined Text String:
"Product: Blue Linen Shirt | Description: Comfortable... | 
 Category: shirts | Tags: linen, blue | Attributes: color=blue, material=linen | 
 Visual: Light blue button-up shirt | Material: Linen blend | 
 Style: Regular fit | Occasion: Casual, smart-casual | 
 Season: Summer, spring | Color: sky blue (light blue, powder blue) | 
 Pattern: Solid | Vibe: breezy, relaxed, coastal"
                    │
                    │  2d. Generate Embeddings (Nova Multimodal)
                    ▼
Text Embedding: [0.023, -0.156, 0.089, ...]  (1024 dimensions)
Image Embedding: [-0.045, 0.234, -0.123, ...] (1024 dimensions)
                    │
                    │  2e. Index in OpenSearch
                    ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ OpenSearch Document                                                              │
│ ─────────────────                                                                │
│ _id: "shirt-001"                                                                 │
│ product_id: "shirt-001"                                                          │
│ store_id: "store-001"                                                            │
│ text_embedding: [0.023, -0.156, ...] (knn_vector)                             │
│ image_embedding: [-0.045, 0.234, ...] (knn_vector)                              │
│ combined_text: "Product: Blue Linen Shirt..."                                   │
│ metadata: {                                                                      │
│   category: "shirts",                                                            │
│   price: 59.99,                                                                  │
│   color: "blue"                                                                  │
│ }                                                                               │
│ created_at: "2026-02-28T09:15:30Z"                                               │
└────────────────────────────────────────────────────────────────────────────────┘
                    │
                    │  2f. Update Status
                    ▼
RDS: embedding_status = "completed"
```

### 5.2 Search Query Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SEARCH QUERY TRANSFORMATIONS                              │
└─────────────────────────────────────────────────────────────────────────────────┘

Input (Search Request)                       Processing                        Output (Results)
──────────────────────                       ───────────                        ───────────────

SearchRequest
{
  query: "summer solid light blue linen shirt",
  store_id: "store-001",
  filters: {price_max: 100},
  limit: 3
}
                    │
                    │  1. Validate & Parse
                    ▼
                    │
                    │  2. Generate Query Embedding (Nova Multimodal)
                    ▼
Query Embedding: [0.034, -0.128, 0.267, ...] (1024 dimensions)
                    │
                    │  3. k-NN Similarity Search (Parallel)
                    ├──▶ Text Embedding Search (top 10)
                    │    Query: {knn: {text_embedding: query_vec, k: 10}}
                    │    Results: [{pid: "shirt-001", score: 0.92}, ...]
                    │
                    └──▶ Image Embedding Search (top 10)
                         Query: {knn: {image_embedding: query_vec, k: 10}}
                         Results: [{pid: "shirt-001", score: 0.88}, ...]
                    │
                    │  4. RRF Merge
                    ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ RRF Calculation (k=60)                                                         │
│ ─────────────────────                                                           │
│                                                                                 │
│ Text Results:                     Image Results:                                │
│ Rank 1: shirt-001 (score 0.92)    Rank 3: shirt-001 (score 0.88)               │
│ Rank 2: shirt-002 (score 0.85)    Rank 1: shirt-003 (score 0.95)               │
│                                   Rank 5: shirt-002 (score 0.82)               │
│                                                                                 │
│ RRF Scores:                                                                     │
│ shirt-001: 1/(60+1) + 1/(60+3) = 0.0164 + 0.0159 = 0.0323                      │
│ shirt-002: 1/(60+2) + 1/(60+5) = 0.0161 + 0.0154 = 0.0315                      │
│ shirt-003: 1/(60+1)              = 0.0164                                        │
│                                                                                 │
│ Final Ranking: shirt-001 > shirt-002 > shirt-003                               │
└────────────────────────────────────────────────────────────────────────────────┘
                    │
                    │  5. Fetch Product Details from RDS
                    ▼
Batch Query: SELECT * FROM products WHERE product_id IN ('shirt-001', 'shirt-002', 'shirt-003')
                    │
                    │  6. Build Response
                    ▼
SearchResponse
{
  results: [
    {
      product_id: "shirt-001",
      name: "Blue Linen Shirt",
      description: "Comfortable...",
      price: 59.99,
      image_url: "https://s3.../img.jpg",
      confidence_score: 0.0323,
      match_type: "hybrid"
    },
    {
      product_id: "shirt-002",
      name: "Classic Linen Shirt",
      ...
      confidence_score: 0.0315,
      match_type: "hybrid"
    },
    {
      product_id: "shirt-003",
      name: "Summer Blue Shirt",
      ...
      confidence_score: 0.0164,
      match_type: "image"
    }
  ],
  total_results: 3,
  query_embedding_time_ms: 150,
  search_time_ms: 250
}
```

---

## 6. API Endpoint Flow

### 6.1 Endpoint Summary

| Endpoint | Method | Auth | Description | Key Components |
|----------|--------|------|-------------|----------------|
| `/health` | GET | No | Service health check | RDS, OpenSearch connectivity |
| `/ingest-catalog` | POST | API Key | Product catalog ingestion | Vision, Embeddings, Background tasks |
| `/search` | POST | API Key | Semantic product search | Query embedding, k-NN, RRF |
| `/product/{id}` | GET | API Key | Get product details | RDS lookup |

### 6.2 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AUTHENTICATION FLOW                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

All protected endpoints use API Key authentication via X-API-Key header.

Request:
POST /search
Headers:
  X-API-Key: your-secure-api-key-here
  Content-Type: application/json

                    │
                    ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ verify_api_key() (in each route file)                                          │
│ ─────────────────────────────────                                                │
│ 1. Extract header value                                                         │
│ 2. Compare with settings.API_KEY                                                │
│ 3. If mismatch → HTTP 401 Unauthorized                                          │
│ 4. If match → Proceed to endpoint handler                                       │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ERROR HANDLING FLOW                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

Exceptions flow through these layers:

1. Service Layer
   - BedrockException → 503 Service Unavailable
   - DatabaseException → 500 Internal Server Error
   - OpenSearchException → 503 Service Unavailable
   - EmbeddingException → 503 Service Unavailable
   - VisionAnalysisException → 503 Service Unavailable
   - ProductNotFoundException → 404 Not Found

2. FastAPI Layer
   - Automatically catches exceptions
   - Returns JSON error response:
     {
       "detail": "Error message",
       "status_code": 500
     }

3. Logging
   - All exceptions logged with context
   - Includes error type, message, stack trace
```

---

## Key Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `app/main.py` | ~60 | FastAPI app factory, router registration |
| `app/config.py` | ~70 | Environment configuration management |
| `app/api/routes/catalog.py` | ~180 | Catalog ingestion endpoint, background processing |
| `app/api/routes/search.py` | ~60 | Search endpoint |
| `app/api/routes/product.py` | ~45 | Product details endpoint |
| `app/api/routes/health.py` | ~65 | Health check endpoint |
| `app/api/schemas/*.py` | ~200 | Pydantic request/response models |
| `app/services/bedrock_service.py` | ~220 | AWS Bedrock integration |
| `app/services/vision_service.py` | ~85 | Image analysis orchestration |
| `app/services/embedding_service.py` | ~55 | Embedding generation |
| `app/services/search_service.py` | ~110 | RRF search orchestration |
| `app/db/rds_client.py` | ~170 | PostgreSQL operations |
| `app/db/opensearch_client.py` | ~220 | OpenSearch k-NN operations |
| `app/db/models.py` | ~50 | SQLAlchemy ORM models |
| `app/utils/image_utils.py` | ~100 | Image download/processing |
| `app/utils/rrf_utils.py` | ~85 | RRF algorithm implementation |
| `app/utils/text_utils.py` | ~90 | Text processing utilities |
| `app/core/exceptions.py` | ~50 | Custom exceptions |
| `app/core/constants.py` | ~40 | Application constants |
| `app/core/logging.py` | ~45 | Structured logging setup |

---

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Total Functions**: 50+  
**API Endpoints**: 4  
**Database Tables**: 1  
**OpenSearch Indices**: 1
