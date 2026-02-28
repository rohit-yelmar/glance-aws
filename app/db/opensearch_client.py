"""OpenSearch client for vector storage and similarity search."""

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.helpers import bulk

from app.config import get_settings
from app.core.constants import OPENSEARCH_EF_SEARCH
from app.core.exceptions import OpenSearchException
from app.core.logging import get_logger

logger = get_logger(__name__)


class AWSV4SignerAuth:
    """AWS Signature V4 authentication for OpenSearch."""
    
    def __init__(self, region: str):
        self.region = region
        self.credentials = boto3.Session().get_credentials()
    
    def __call__(self, method, url, body=None):
        request = AWSRequest(method=method, url=url, data=body)
        SigV4Auth(self.credentials, "es", self.region).add_auth(request)
        return request.headers.items()


class OpenSearchClient:
    """Client for OpenSearch vector database operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = self._create_client()
        self.index_name = self.settings.OPENSEARCH_INDEX
    
    def _create_client(self) -> OpenSearch:
        """Create OpenSearch client with AWS authentication."""
        settings = self.settings
        
        # Determine authentication method
        auth = None
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            # Use explicit credentials
            auth = (settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        else:
            # Use IAM role / AWS V4 signing
            auth = AWSV4SignerAuth(settings.OPENSEARCH_AWS_REGION)
        
        client = OpenSearch(
            hosts=[{
                "host": settings.OPENSEARCH_HOST,
                "port": settings.OPENSEARCH_PORT
            }],
            http_auth=auth,
            use_ssl=settings.OPENSEARCH_USE_SSL,
            verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
            connection_class=RequestsHttpConnection,
            timeout=30,
        )
        
        return client
    
    def create_index(self) -> bool:
        """Create OpenSearch index with k-NN mapping.
        
        Returns:
            True if index created or already exists
        """
        settings = self.settings
        
        # Check if index exists
        if self.client.indices.exists(index=self.index_name):
            logger.info("index_already_exists", index=self.index_name)
            return True
        
        # Index configuration with k-NN
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": OPENSEARCH_EF_SEARCH,
                },
                "number_of_shards": 1,
                "number_of_replicas": 0,
            },
            "mappings": {
                "properties": {
                    "product_id": {"type": "keyword"},
                    "store_id": {"type": "keyword"},
                    "embedding_type": {"type": "keyword"},
                    "text_embedding": {
                        "type": "knn_vector",
                        "dimension": settings.EMBEDDING_DIMENSIONS,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 24
                            }
                        }
                    },
                    "image_embedding": {
                        "type": "knn_vector",
                        "dimension": settings.EMBEDDING_DIMENSIONS,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 24
                            }
                        }
                    },
                    "combined_text": {"type": "text"},
                    "metadata": {
                        "properties": {
                            "category": {"type": "keyword"},
                            "price": {"type": "float"},
                            "color": {"type": "keyword"}
                        }
                    },
                    "created_at": {"type": "date"}
                }
            }
        }
        
        try:
            response = self.client.indices.create(
                index=self.index_name,
                body=index_body
            )
            logger.info("index_created", index=self.index_name, response=response)
            return True
        except Exception as e:
            logger.error("index_creation_error", index=self.index_name, error=str(e))
            raise OpenSearchException(f"Failed to create index: {str(e)}")
    
    def index_embedding(
        self,
        product_id: str,
        store_id: str,
        text_embedding: list,
        image_embedding: list,
        combined_text: str,
        metadata: dict = None
    ) -> bool:
        """Index product embeddings.
        
        Args:
            product_id: Product identifier
            store_id: Store identifier
            text_embedding: Text embedding vector
            image_embedding: Image embedding vector
            combined_text: Combined text for reference
            metadata: Optional metadata dict
            
        Returns:
            True if indexed successfully
        """
        from datetime import datetime
        
        document = {
            "product_id": product_id,
            "store_id": store_id,
            "text_embedding": text_embedding,
            "image_embedding": image_embedding,
            "combined_text": combined_text,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            response = self.client.index(
                index=self.index_name,
                body=document,
                id=product_id
            )
            logger.info("embedding_indexed", product_id=product_id, doc_id=response.get("_id"))
            return True
        except Exception as e:
            logger.error("index_embedding_error", product_id=product_id, error=str(e))
            raise OpenSearchException(f"Failed to index embedding: {str(e)}")
    
    def search_by_text_embedding(
        self,
        embedding: list,
        k: int = 10,
        store_id: str = None
    ) -> list:
        """Search by text embedding similarity.
        
        Args:
            embedding: Query embedding vector
            k: Number of results
            store_id: Optional store filter
            
        Returns:
            List of search results with product_id and score
        """
        query = {
            "size": k,
            "query": {
                "knn": {
                    "text_embedding": {
                        "vector": embedding,
                        "k": k
                    }
                }
            },
            "_source": ["product_id", "store_id", "combined_text", "metadata"]
        }
        
        # Add store filter if provided
        if store_id:
            query["query"] = {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "text_embedding": {
                                    "vector": embedding,
                                    "k": k
                                }
                            }
                        },
                        {"term": {"store_id": store_id}}
                    ]
                }
            }
        
        try:
            response = self.client.search(index=self.index_name, body=query)
            
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "product_id": hit["_source"]["product_id"],
                    "score": hit["_score"],
                    "source": hit["_source"]
                })
            
            logger.debug("text_search_complete", k=k, results=len(results))
            return results
            
        except Exception as e:
            logger.error("text_search_error", error=str(e))
            raise OpenSearchException(f"Text search failed: {str(e)}")
    
    def search_by_image_embedding(
        self,
        embedding: list,
        k: int = 10,
        store_id: str = None
    ) -> list:
        """Search by image embedding similarity.
        
        Args:
            embedding: Query embedding vector
            k: Number of results
            store_id: Optional store filter
            
        Returns:
            List of search results with product_id and score
        """
        query = {
            "size": k,
            "query": {
                "knn": {
                    "image_embedding": {
                        "vector": embedding,
                        "k": k
                    }
                }
            },
            "_source": ["product_id", "store_id", "combined_text", "metadata"]
        }
        
        # Add store filter if provided
        if store_id:
            query["query"] = {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "image_embedding": {
                                    "vector": embedding,
                                    "k": k
                                }
                            }
                        },
                        {"term": {"store_id": store_id}}
                    ]
                }
            }
        
        try:
            response = self.client.search(index=self.index_name, body=query)
            
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "product_id": hit["_source"]["product_id"],
                    "score": hit["_score"],
                    "source": hit["_source"]
                })
            
            logger.debug("image_search_complete", k=k, results=len(results))
            return results
            
        except Exception as e:
            logger.error("image_search_error", error=str(e))
            raise OpenSearchException(f"Image search failed: {str(e)}")
    
    def delete_by_product_id(self, product_id: str) -> bool:
        """Delete embedding by product ID.
        
        Args:
            product_id: Product identifier
            
        Returns:
            True if deleted
        """
        try:
            self.client.delete(index=self.index_name, id=product_id)
            logger.info("embedding_deleted", product_id=product_id)
            return True
        except Exception as e:
            logger.error("delete_error", product_id=product_id, error=str(e))
            return False
    
    def health_check(self) -> bool:
        """Check OpenSearch connectivity.
        
        Returns:
            True if OpenSearch is accessible
        """
        try:
            response = self.client.cluster.health()
            status = response.get("status")
            logger.debug("opensearch_health", status=status)
            return status in ["green", "yellow"]
        except Exception as e:
            logger.error("health_check_failed", error=str(e))
            return False


# Singleton instance
_opensearch_client = None


def get_opensearch_client() -> OpenSearchClient:
    """Get singleton OpenSearch client instance."""
    global _opensearch_client
    if _opensearch_client is None:
        _opensearch_client = OpenSearchClient()
    return _opensearch_client
