import os
import httpx
import logging
import asyncio
import json
from pathlib import Path
from bs4 import BeautifulSoup
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

async def web_search(queries: list) -> str:
    """
    Perform web search via SerpAPI or Google Search API.
    If search API fails or is not configured, falls back to local mock data.
    """
    if not queries:
        return ""
        
    query = queries[0] # Search first query as primary
    
    if settings.SEARCH_API_KEY:
        try:
            # Connect to SerpAPI
            url = "https://serpapi.com/search.json"
            params = {
                "q": query,
                "api_key": settings.SEARCH_API_KEY,
                "engine": "google",
                "hl": "id",
                "gl": "id"
            }
            
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract organic search results
                    organic_results = data.get("organic_results", [])
                    snippets = []
                    urls_to_scrape = []
                    
                    for r in organic_results[:3]: # take top 3
                        title = r.get("title", "")
                        snippet = r.get("snippet", "")
                        link = r.get("link", "")
                        snippets.append(f"Judul: {title}\nRingkasan: {snippet}\nSumber: {link}")
                        if link:
                            urls_to_scrape.append(link)
                            
                    # Optional: Scrape top page content for deeper context
                    scraped_text = ""
                    if urls_to_scrape:
                        scraped_text = await scrape_page(urls_to_scrape[0])
                        
                    results_text = "=== HASIL PENCARIAN GOOGLE ===\n" + "\n\n".join(snippets)
                    if scraped_text:
                        results_text += f"\n\n=== KONTEN TERPERINCI DARI {urls_to_scrape[0]} ===\n{scraped_text}"
                    return results_text
        except Exception as e:
            logger.warning(f"Web search failed or timed out: {e}. Using local fallback data.")
            
    # Local fallback for offline mode or missing API key
    return get_local_fallback_data(queries)

async def scrape_page(url: str) -> str:
    """
    Scrapes a web page and returns clean text content.
    Includes a 2-second timeout.
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                    
                # Get text
                text = soup.get_text()
                
                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase for line in lines for phrase in line.split("  "))
                text = "\n".join(chunk for chunk in chunks if chunk)
                
                # Return first 1000 characters
                return text[:1000] + "..." if len(text) > 1000 else text
    except Exception as e:
        logger.warning(f"Failed to scrape page {url}: {e}")
    return ""

def get_local_fallback_data(queries: str) -> str:
    """
    Load data/fallback_mock_jabar.json to ensure the system is fully functional offline.
    """
    fallback_path = Path(__file__).parent.parent.parent / "data" / "fallback_mock_jabar.json"
    
    if fallback_path.exists():
        try:
            with open(fallback_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Search query matching
            combined_queries = " ".join(queries).lower()
            
            # Simple matching logic
            if "bakso" in combined_queries:
                return json.dumps(data.get("bakso_sapi_beku", {}), indent=2)
            elif "kopi" in combined_queries:
                return json.dumps(data.get("kopi_bubuk_lokal", {}), indent=2)
            elif "keripik" in combined_queries:
                return json.dumps(data.get("keripik_singkong_pedas", {}), indent=2)
                
            # Default to general marketplace info
            return json.dumps(data.get("default_market", {}), indent=2)
        except Exception as e:
            logger.error(f"Failed to parse fallback mock JSON: {e}")
            
    # Inline fallback if the file doesn't exist yet
    return (
        "=== HASIL PENCARIAN PASAR OFFLINE (FALLBACK) ===\n"
        "1. Tren Kuliner: Makanan pedas dan olahan praktis (frozen food) mengalami pertumbuhan penjualan 25% YoY.\n"
        "2. Kisaran Harga: Harga jual di tingkat konsumen untuk makanan ringan berkisar Rp 10.000 - Rp 15.000, sedangkan frozen food Rp 25.000 - Rp 45.000.\n"
        "3. Bahan Baku: Harga komoditas singkong mentah rata-rata Rp 4.500/kg, cabai rawit Rp 45.000/kg."
    )
