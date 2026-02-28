#!/usr/bin/env python3
"""Initialize OpenSearch index."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.opensearch_client import get_opensearch_client
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def main():
    """Initialize OpenSearch index."""
    logger.info("initializing_opensearch")
    try:
        client = get_opensearch_client()
        created = client.create_index()
        if created:
            logger.info("opensearch_index_created")
            print("✅ OpenSearch index created successfully!")
        else:
            logger.info("opensearch_index_already_exists")
            print("ℹ️ OpenSearch index already exists.")
    except Exception as e:
        logger.error("opensearch_initialization_failed", error=str(e))
        print(f"❌ OpenSearch initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
