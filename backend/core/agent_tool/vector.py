import logging
from qdrant_client import QdrantClient
from config import settings

logger = logging.getLogger(__name__)

# Initialize Qdrant Client
# We use FastEmbed model to encode queries locally without external API calls
qdrant_client = None
try:
    qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    qdrant_client.set_model("sentence-transformers/all-MiniLM-L6-v2")
except Exception as e:
    logger.error(f"Failed to connect to Qdrant: {e}. Vector search will be unavailable.")

async def vector_search(queries: list, limit: int = 3) -> str:
    """
    Search local Qdrant collection for regulations context.
    """
    if not qdrant_client:
        return "Vector database is not available. Using general knowledge for regulations."

    context_snippets = []
    
    try:
        # Check if collection exists
        collections = qdrant_client.get_collections()
        col_names = [col.name for col in collections.collections]
        if settings.QDRANT_COLLECTION not in col_names:
            return "Regulations collection is not initialized. Please run the seed script."
            
        for query in queries:
            # Query Qdrant with local embedding auto-generation
            results = qdrant_client.query(
                collection_name=settings.QDRANT_COLLECTION,
                query_text=query,
                limit=limit
            )
            for res in results:
                context_snippets.append(res.document)
                
        # Remove duplicates
        unique_snippets = list(set(context_snippets))
        return "\n\n".join(unique_snippets) if unique_snippets else "No matching regulatory documents found."
    except Exception as e:
        logger.warning(f"Error querying Qdrant: {e}")
        return "Failed to fetch rules from vector database. Using fallback rules."
