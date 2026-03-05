#!/usr/bin/env python3
"""Initialize Pinecone index."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.pinecone_client import get_pinecone_client
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def main():
    """Initialize Pinecone index."""
    logger.info("initializing_pinecone")
    try:
        client = get_pinecone_client()
        created = client.create_index()
        if created:
            logger.info("pinecone_index_created")
            print("✅ Pinecone index created successfully!")
        else:
            logger.info("pinecone_index_already_exists")
            print("ℹ️ Pinecone index already exists.")
    except Exception as e:
        logger.error("pinecone_initialization_failed", error=str(e))
        print(f"❌ Pinecone initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
