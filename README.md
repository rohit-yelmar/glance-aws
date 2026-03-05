# Glance - Visual Semantic Search Backend

AI-powered visual semantic search system for fashion e-commerce platforms. Enables natural, vibe-based product discovery using multimodal embeddings (text + image) in a unified latent space.

---

## Overview

**Problem**: Traditional keyword-based search fails on semantic queries like "summer solid light blue linen shirt"

**Solution**: A dual-path embedding system that combines:
- **Vision Understanding**: Amazon Nova 2 Lite for deep image analysis
- **Unified Latent Space**: Amazon Nova Multimodal Embeddings for text + image
- **Hybrid Retrieval**: RRF (Reciprocal Rank Fusion) for optimal results

---

## Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Next.js   │─────▶│   FastAPI        │─────▶│  Amazon Bedrock │
│   Frontend  │◀─────│   Backend        │◀─────│  (Nova Models)  │
└─────────────┘      └──────────────────┘      └─────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    ┌─────────────────┐           ┌──────────────────┐
    │  Amazon RDS     │           │    Pinecone      │
    │  (PostgreSQL)   │           │  (Vector DB)     │
    │  Product Store  │           │  Serverless      │
    └─────────────────┘           └──────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- AWS Account with Bedrock access
- AWS CLI configured

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd glance-aws

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your AWS credentials and endpoints

# Initialize databases
python scripts/init_db.py
python scripts/init_pinecone.py

# Run development server
uvicorn app.main:app --reload
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest-catalog` | Ingest product catalog for processing |
| `POST` | `/search` | Semantic product search |
| `GET` | `/health` | Health check |
| `GET` | `/product/{id}` | Get product details |

### Example: Search Products

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "summer solid light blue linen shirt",
    "limit": 3
  }'
```

**Response:**
```json
{
  "results": [
    {
      "product_id": "shirt-001",
      "name": "Classic Blue Linen Shirt",
      "price": 59.99,
      "confidence_score": 0.92,
      "match_type": "hybrid"
    }
  ],
  "total_results": 3
}
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [`requirements.md`](requirements.md) | Detailed requirements, architecture, and API specifications |
| [`plan.md`](plan.md) | Implementation plan, file structure, and design decisions |
| [`setup.md`](setup.md) | Complete deployment guide for AWS EC2 |

---

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: Amazon RDS (PostgreSQL)
- **Vector DB**: Pinecone (Serverless)
- **AI Models**: Amazon Nova 2 Lite, Nova Multimodal Embeddings
- **AWS SDK**: boto3
- **Deployment**: Amazon EC2

---

## Project Structure

```
glance-aws/
├── app/
│   ├── api/           # API routes (catalog, search, health)
│   ├── services/      # Business logic (Bedrock, embeddings, search)
│   ├── db/            # Database clients (RDS, Pinecone)
│   ├── utils/         # Utilities (image, text, RRF)
│   └── main.py        # FastAPI entry point
├── scripts/           # Setup and initialization scripts
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── requirements.md    # Detailed requirements
├── plan.md            # Implementation plan
└── setup.md           # Deployment guide
```

---

## Processing Pipeline

1. **Catalog Ingestion**: Receive product data with S3 image URLs
2. **Image Analysis**: Nova 2 Lite extracts material, style, vibe attributes
3. **Text Combination**: Merge original + AI-generated attributes
4. **Embedding Generation**: Create 1024-dim vectors for text + image
5. **Vector Storage**: Store in Pinecone with metadata (text-embeddings and image-embeddings namespaces)

## Retrieval Flow

1. **Query Embedding**: Convert search query to vector
2. **Parallel Search**: Query both text and image embeddings
3. **RRF Merge**: Combine results using Reciprocal Rank Fusion
4. **Deduplication**: Remove duplicates by product ID
5. **Return**: Top 3 most relevant products

---

## Deployment

See [`setup.md`](setup.md) for complete deployment instructions including:
- AWS service configuration (RDS, EC2)
- Pinecone setup
- IAM role setup
- Environment variables
- EC2 deployment with nginx
- HTTPS configuration

**Quick Deploy:**
```bash
# On EC2 instance
cd /opt/glance
./scripts/setup_ec2.sh
sudo systemctl start glance
```

---

## Environment Variables

Key variables required (see `.env.example` for full list):

```bash
AWS_REGION=us-east-1
DB_HOST=your-rds-endpoint
DB_PASSWORD=your-db-password
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=glance-index
API_KEY=your-secure-api-key
```

---

## License

Private - All rights reserved.

---

## Support

For setup issues, refer to the [Troubleshooting](setup.md#8-troubleshooting) section in setup.md.
