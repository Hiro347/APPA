import json
import asyncio
import logging
from pathlib import Path
from ddgs import DDGS
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from ai.inference import call_llm
from ai.prompts.condensation import get_condensation_prompt

logger = logging.getLogger(__name__)

async def web_search(queries: list, visited_urls: set = None) -> dict:
    """
    Perform web search via DuckDuckGo.
    If search fails, falls back to local mock data.
    """
    if not queries:
        return ""
        
    query = queries[0] # Search first query as primary
    
    try:
        # 1. SEARCH: Get URLs via DuckDuckGo
        urls_to_scrape = []
        snippets = []
        
        def run_ddgs():
            import time
            for attempt in range(3):
                try:
                    with DDGS(verify=False, timeout=20) as ddgs:
                        return ddgs.text(query, max_results=3, region="id-id")
                except Exception as e:
                    if attempt == 2:
                        raise e
                    time.sleep(1)
            return []
                
        results = await asyncio.to_thread(run_ddgs)
        if results:
            for r in results:
                title = r.get("title", "")
                snippet = r.get("body", "")
                link = r.get("href", "")
                if link:
                    if visited_urls is not None:
                        if link in visited_urls:
                            continue
                        visited_urls.add(link)
                    snippets.append(f"Judul: {title}\nRingkasan: {snippet}\nSumber: {link}")
                    urls_to_scrape.append(link)

        # 2. CRAWL: Scrape top page content via Crawl4AI
        scraped_text = ""
        if urls_to_scrape:
            # Scrape up to top 3 results for more comprehensive data
            scraped_text = await scrape_pages(urls_to_scrape[:3])
            
        # 3. CONDENSE: Summarize scraped markdown via LLM + Pydantic
        condensed_json = "{}"
        if scraped_text:
            condensed_json = await condense_market_data(scraped_text)
            
        results_text = "=== HASIL PENCARIAN GOOGLE (DUCKDUCKGO) ===\n" + "\n\n".join(snippets)
        if condensed_json != "{}":
            results_text += f"\n\n=== INSIGHT TERKONDENSASI DARI {urls_to_scrape[0]} ===\n{condensed_json}"
            
        return {
            "snippets": snippets,
            "url_scraped": ", ".join(urls_to_scrape[:3]) if urls_to_scrape else None,
            "raw_markdown": scraped_text,
            "condensed_json": condensed_json,
            "combined_text": results_text
        }
    except Exception as e:
        logger.warning(f"Web search failed or timed out: {e}. Using local fallback data.")
            
    # Local fallback for offline mode or missing API key
    fallback_data = get_local_fallback_data(queries)
    return {
        "snippets": ["Offline Fallback Activated"],
        "url_scraped": None,
        "raw_markdown": fallback_data,
        "condensed_json": "{}",
        "combined_text": fallback_data
    }

async def scrape_google_shopping(keyword: str) -> dict:
    """
    Scrapes Google Shopping for the given keyword using Crawl4AI.
    Returns the extracted markdown and the condensed JSON.
    """
    url = f"https://www.google.com/search?tbm=shop&q={keyword.replace(' ', '+')}"
    logger.info(f"Scraping Google Shopping: {url}")
    
    try:
        browser_config = BrowserConfig(headless=True)
        run_config = CrawlerRunConfig(page_timeout=15000)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
            
            if result.success and result.markdown:
                condensed = await condense_market_data(result.markdown)
                return {"condensed_json": condensed, "raw_markdown": result.markdown, "url": url}
            else:
                logger.warning(f"Failed to scrape Google Shopping for {keyword}: {result.error_message}")
                
    except Exception as e:
        logger.error(f"Error executing Crawl4AI on Google Shopping: {e}")
        
    return {"condensed_json": "{}", "raw_markdown": "", "url": url}

async def scrape_pages(urls: list) -> str:
    """
    Scrapes multiple web pages using a single Crawl4AI instance and returns clean Markdown.
    """
    scraped_texts = []
    try:
        browser_config = BrowserConfig(headless=True)
        run_config = CrawlerRunConfig(page_timeout=5000)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for url in urls:
                try:
                    result = await crawler.arun(url=url, config=run_config)
                    if result.success:
                        scraped_texts.append(f"=== KONTEN DARI {url} ===\n{result.markdown}")
                    else:
                        logger.warning(f"Crawl4AI failed to scrape {url}: {result.error_message}")
                except Exception as ex:
                    logger.warning(f"Failed to scrape page {url}: {ex}")
    except Exception as e:
        logger.error(f"Crawler failed to initialize: {e}")
        
    return "\n\n".join(scraped_texts)

async def condense_market_data(markdown_text: str) -> str:
    """
    Condenses the raw Markdown using LLM and Pydantic schema to prevent info loss.
    TODO: [PRODUCTION-READY] Implement Pydantic `MarketDataSchema.validate_json(response)` 
    to enforce structural integrity and trigger LLM retries on hallucination instead of returning raw text.
    """
    # Truncate markdown to prevent hitting token limits (expanded for 3 URLs)
    markdown_text = markdown_text[:15000]
    
    system_prompt = get_condensation_prompt()
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, call_llm, markdown_text, system_prompt
        )
        return response
    except Exception as e:
        logger.error(f"Condensation failed: {e}")
        return "{}"

def get_local_fallback_data(queries: str) -> str:
    """
    Load data/fallback_mock_jabar.json to ensure the system is fully functional offline.
    TODO: [MOCK REPLACEMENT] In production, remove this local offline fallback entirely. 
    The system should fail gracefully via API error codes rather than hallucinating offline data.
    """
    # Path logic shifted because this is now in core/agent_tool/web.py
    fallback_path = Path(__file__).parent.parent.parent.parent / "data" / "fallback_mock_jabar.json"
    
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
