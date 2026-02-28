# Glance Backend - Implementation Plan

## Project Structure

```
glance-aws/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── catalog.py      # POST /ingest-catalog endpoint
│   │   │   ├── search.py       # POST /search endpoint
│   │   │   ├── health.py       # GET /health endpoint
│   │   │   └── product.py      # GET /product/{id} endpoint
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── catalog.py      # Pydantic models for catalog
│   │       ├── search.py       # Pydantic models for search
│   │       └── product.py      # Pydantic models for product
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── logging.py          # Logging configuration
│   │   └── constants.py        # Application constants
│   ├── services/
│   │   ├── __init__.py
│   │   ├── bedrock_service.py  # AWS Bedrock (Nova) integration
│   │   ├── embedding_service.py # Embedding generation
│   │   ├── vision_service.py   # Image analysis service
│   │   └── search_service.py   # RRF search logic
│   ├── db/
│   │   ├── __init__.py
│   │   ├── rds_client.py       # PostgreSQL connection & operations
│   │   ├── opensearch_client.py # OpenSearch connection & operations
│   │   └── models.py           # SQLAlchemy models
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── image_utils.py      # Image download & processing
│   │   ├── rrf_utils.py        # RRF algorithm implementation
│   │   └── text_utils.py       # Text processing utilities
│   └── workers/
│       ├── __init__.py
│       └── catalog_processor.py # Async catalog processing
├── scripts/
│   ├── init_db.py              # Database initialization script
│   ├── init_opensearch.py      # OpenSearch index creation
│   └── setup_aws.sh            # AWS resource setup helper
├── tests/                      # (Optional) Test files
├── docs/
│   └── architecture.md         # Architecture diagrams
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .gitignore
└── README.md
```

---

## File-by-File Implementation Details

### 1. Configuration Files

#### `app/config.py`

**Purpose**: Centralized configuration management using Pydantic Settings
**Key Features**:

- Environment variable loading
- AWS region configuration
- Database connection strings
- OpenSearch endpoint configuration
- Bedrock model IDs

#### `.env.example`

**Purpose**: Template for all required environment variables

---

### 2. API Layer

#### `app/api/routes/catalog.py`

**Endpoint**: `POST /ingest-catalog`
**Implementation**:

- Accept catalog payload validation
- Store products in RDS (sync)
- Trigger async processing pipeline
- Return job_id for tracking

**Async Processing Flow**:

```python
async def process_catalog_batch(products: List[Product]):
    for product in products:
        # 1. Download image
        image_bytes = await download_image(product.image_url)

        # 2. Vision analysis via Bedrock
        vision_attrs = await vision_service.analyze_image(image_bytes)

        # 3. Update RDS with vision attributes
        await rds_client.update_vision_attributes(product.id, vision_attrs)

        # 4. Generate combined text
        combined_text = text_utils.combine_text(product, vision_attrs)

        # 5. Generate embeddings
        text_embedding = await embedding_service.embed_text(combined_text)
        image_embedding = await embedding_service.embed_image(image_bytes)

        # 6. Store in OpenSearch
        await opensearch_client.index_embedding(
            product_id=product.id,
            text_embedding=text_embedding,
            image_embedding=image_embedding,
            metadata={...}
        )

        # 7. Update status
        await rds_client.update_embedding_status(product.id, "completed")
```

#### `app/api/routes/search.py`

**Endpoint**: `POST /search`
**Implementation**:

- Parse query and filters
- Generate query embedding
- Parallel search: text_similarity + image_similarity
- Apply RRF merging
- Deduplicate and rank
- Fetch full product details from RDS
- Return formatted response

#### `app/api/routes/health.py`

**Endpoint**: `GET /health`
**Implementation**:

- Check RDS connectivity
- Check OpenSearch connectivity
- Check Bedrock availability
- Return aggregated status

#### `app/api/routes/product.py`

**Endpoint**: `GET /product/{product_id}`
**Implementation**:

- Query RDS by product_id
- Return full product details

---

### 3. Service Layer

#### `app/services/bedrock_service.py`

**Purpose**: AWS Bedrock client wrapper
**Methods**:

- `invoke_nova_lite(image_bytes: bytes, prompt: str) -> dict` - Image analysis
- `invoke_embedding(text: str = None, image_bytes: bytes = None) -> list` - Embedding generation

**Key Considerations**:

- Handle Bedrock throttling (retry with backoff)
- Base64 encode images for API
- Parse streaming responses

#### `app/services/vision_service.py`

**Purpose**: Image analysis orchestration
**Methods**:

- `analyze_image(image_bytes: bytes) -> VisionAttributes`
- Uses Bedrock with structured system prompt
- Parses JSON response

**Prompt Engineering**:

- Structured JSON output format
- Consistent attribute naming
- Fallback for parsing failures

#### `app/services/embedding_service.py`

**Purpose**: Unified embedding generation
**Methods**:

- `embed_text(text: str) -> list[float]` - Text to 1024-dim vector
- `embed_image(image_bytes: bytes) -> list[float]` - Image to 1024-dim vector

**Key Points**:

- Same model for both modalities (unified latent space)
- Batch processing support (future)

#### `app/services/search_service.py`

**Purpose**: RRF search orchestration
**Methods**:

- `semantic_search(query: str, filters: dict, limit: int) -> SearchResults`
- `text_similarity_search(embedding: list, k: int) -> list[SearchResult]`
- `image_similarity_search(embedding: list, k: int) -> list[SearchResult]`
- `rrf_merge(text_results: list, image_results: list, k: int = 60) -> list[str]`

---

### 4. Database Layer

#### `app/db/rds_client.py`

**Purpose**: PostgreSQL operations
**Methods**:

- `create_product(product: Product) -> None`
- `update_vision_attributes(product_id: str, attrs: dict) -> None`
- `update_embedding_status(product_id: str, status: str) -> None`
- `get_product_by_id(product_id: str) -> Product`
- `get_products_by_ids(product_ids: list) -> list[Product]`

**Connection Pooling**:

- Use SQLAlchemy with connection pool
- Async support via asyncpg (optional) or sync with thread pool

#### `app/db/opensearch_client.py`

**Purpose**: Vector database operations
**Methods**:

- `index_embedding(product_id, text_emb, image_emb, metadata) -> None`
- `search_by_text_embedding(embedding, k=10) -> list[SearchHit]`
- `search_by_image_embedding(embedding, k=10) -> list[SearchHit]`
- `create_index(index_name, mappings) -> None`

**k-NN Query Format**:

```json
{
  "query": {
    "knn": {
      "text_embedding": {
        "vector": [...],
        "k": 10
      }
    }
  }
}
```

#### `app/db/models.py`

**Purpose**: SQLAlchemy ORM models
**Classes**:

- `Product` - Main product table
- `ProductAttribute` - Extended attributes (optional normalization)

---

### 5. Utility Layer

#### `app/utils/image_utils.py`

**Purpose**: Image handling
**Methods**:

- `download_image(url: str) -> bytes` - HTTP download with timeout
- `validate_image(image_bytes: bytes) -> bool` - Check format/size
- `resize_if_needed(image_bytes: bytes, max_size: tuple) -> bytes`

#### `app/utils/rrf_utils.py`

**Purpose**: RRF algorithm implementation
**Methods**:

- `calculate_rrf_score(rank: int, k: int = 60) -> float`
- `merge_rankings(text_results: list, image_results: list, k: int) -> list[tuple[str, float]]`
- `deduplicate_by_id(results: list) -> list`

#### `app/utils/text_utils.py`

**Purpose**: Text processing
**Methods**:

- `combine_product_text(product: Product, vision_attrs: dict) -> str`
- `sanitize_text(text: str) -> str` - Clean for embedding
- `extract_keywords(text: str) -> list[str]`

---

### 6. Worker Layer

#### `app/workers/catalog_processor.py`

**Purpose**: Background catalog processing
**Implementation Options**:

1. **In-process async** (MVP): Use FastAPI background tasks
2. **Celery** (Future): For large-scale processing

**MVP Approach**:

```python
from fastapi import BackgroundTasks

@app.post("/ingest-catalog")
async def ingest_catalog(catalog: CatalogRequest, background_tasks: BackgroundTasks):
    # Store products immediately
    await rds_client.batch_insert(catalog.products)

    # Process in background
    background_tasks.add_task(process_catalog_batch, catalog.products)

    return {"job_id": generate_uuid(), "status": "processing"}
```

---

## Data Flow Diagrams

### Catalog Ingestion Flow

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │      │   FastAPI    │      │   RDS (PSQL) │
│   (Next.js)  │─────▶│   Backend    │─────▶│   (Metadata) │
└──────────────┘      └──────────────┘      └──────────────┘
                             │
                             │ Background Task
                             ▼
                      ┌──────────────┐
                      │ S3 Image     │
                      │ Download     │
                      └──────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ Bedrock Nova │
                      │ 2 Lite       │
                      │ (Analysis)   │
                      └──────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ Bedrock Nova │
                      │ Embeddings   │
                      └──────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ OpenSearch   │
                      │ (Vectors)    │
                      └──────────────┘
```

### Search Flow

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │      │   FastAPI    │      │ Bedrock Nova │
│   (Next.js)  │─────▶│   Backend    │─────▶│ Embeddings   │
└──────────────┘      └──────────────┘      └──────────────┘
                             │                       │
                             │                       │
                             │         ┌─────────────┴─────────────┐
                             │         ▼                           ▼
                             │  ┌──────────────┐            ┌──────────────┐
                             │  │ OpenSearch   │            │ OpenSearch   │
                             └──│ Text k-NN    │            │ Image k-NN   │
                                └──────────────┘            └──────────────┘
                                        │                           │
                                        └───────────┬───────────────┘
                                                    ▼
                                             ┌──────────────┐
                                             │ RRF Merge    │
                                             │ Algorithm    │
                                             └──────────────┘
                                                    │
                                                    ▼
                                             ┌──────────────┐
                                             │    RDS       │
                                             │ (Get Details)│
                                             └──────────────┘
                                                    │
                                                    ▼
                                             ┌──────────────┐
                                             │  Response    │
                                             │ productId[]  │
                                             └──────────────┘
```

---

## Implementation Phases

### Phase 1: Core Infrastructure

1. Set up project structure
2. Implement configuration management
3. Create database clients (RDS, OpenSearch)
4. Set up logging and error handling

### Phase 2: AWS Integration

1. Implement Bedrock service
2. Create embedding service
3. Implement vision service with prompts
4. Test AWS connectivity

### Phase 3: API Endpoints

1. Implement health check
2. Implement catalog ingestion (sync only)
3. Add background processing
4. Implement search endpoint

### Phase 4: RRF & Optimization

1. Implement RRF algorithm
2. Add deduplication logic
3. Optimize query performance
4. Add filtering support

### Phase 5: Deployment

1. Create deployment scripts
2. Set up EC2 instance
3. Configure nginx (reverse proxy)
4. Set up systemd service

---

## Key Design Decisions

### 1. Synchronous vs Asynchronous Processing

- **Catalog Ingestion**: Background tasks (FastAPI BackgroundTasks)
- **Search**: Fully synchronous for low latency
- **Rationale**: Simple to implement, sufficient for MVP scale

### 2. Vector Storage Strategy

- Store both text and image embeddings in same document
- Enable separate k-NN fields for each embedding type
- Query both simultaneously for RRF

### 3. Error Handling Strategy

- **Catalog Ingestion**: Continue processing on individual product failures, log errors
- **Search**: Fail fast with meaningful error message
- **Vision Analysis**: Fallback to empty attributes if Bedrock fails

### 4. Authentication

- **MVP**: API Key via header (`X-API-Key`)
- **Future**: JWT tokens, OAuth2

### 5. Monitoring

- Application logs with structured JSON format

---

## Performance Considerations

### Embedding Generation

- **Latency**: ~200-500ms per embedding (Bedrock)
- **Batch Size**: 1 (Nova Embeddings doesn't support batching)
- **Optimization**: Parallel processing for catalog ingestion

### OpenSearch k-NN

- **Query Latency**: ~50-100ms
- **ef_search**: 100 (balance between speed and accuracy)
- **ef_construction**: 128 (index time)

### RDS Operations

- **Connection Pool**: 10-20 connections
- **Indexing**: product_id (primary), store_id (foreign)
- **Query Pattern**: Simple lookups by ID

---

## Risk Mitigation

| Risk                           | Mitigation                         |
| ------------------------------ | ---------------------------------- |
| Bedrock throttling             | Exponential backoff (1s, 2s, 4s)   |
| OpenSearch connection failure  | Retry with circuit breaker pattern |
| Large image downloads          | Timeout (30s), size limit (10MB)   |
| Invalid image URLs             | Validate URL, catch exceptions     |
| JSON parsing failures          | Try/except with fallback           |
| RDS connection pool exhaustion | Connection pool limits, timeouts   |

---

## Future Enhancements

1. **Caching Layer**: Redis for frequent queries
2. **Rate Limiting**: Prevent API abuse
3. **Metrics**: Prometheus/Grafana dashboards
4. **Model Fine-tuning**: Custom embeddings on fashion data
5. **Multi-modal Search**: Search by uploaded image (reverse image search)
6. **Auto-scaling**: EC2 Auto Scaling for traffic spikes
