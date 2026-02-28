#!/usr/bin/env python3
"""Initialize RDS PostgreSQL database."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.rds_client import init_db
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def main():
    """Initialize database tables."""
    logger.info("initializing_database")
    try:
        init_db()
        logger.info("database_initialized_successfully")
        print("✅ Database initialized successfully!")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
