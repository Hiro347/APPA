import json
import asyncio
import logging
from pathlib import Path
from ddgs import DDGS
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter
from ai.inference import async_call_llm
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
                    
                    # Skip scraping social media domains because headless browsers usually fail on them
                    blocked_domains = [
                        "tiktok.com", "instagram.com", "facebook.com", "youtube.com", 
                        "twitter.com", "x.com", "gofood.co.id", "grab.com", 
                        "shopee.co.id", "tokopedia.com", "lemon8-app.com"
                    ]
                    if not any(domain in link.lower() for domain in blocked_domains):
                        urls_to_scrape.append(link)

        # 2. CRAWL: Scrape top page content via Crawl4AI
        scraped_text = ""
        if urls_to_scrape:
            # Scrape up to top 3 results for more comprehensive data
            scraped_text = await scrape_pages(urls_to_scrape[:3], query)
            
        # 3. CONDENSE: Summarize scraped markdown AND snippets via LLM
        condensed_markdown = ""
        raw_combined = "=== HASIL PENCARIAN GOOGLE (DUCKDUCKGO) ===\n" + "\n\n".join(snippets)
        if scraped_text:
            raw_combined += "\n\n=== KONTEN WEBSITE (SCRAPED) ===\n" + scraped_text
            
        if raw_combined.strip():
            condensed_markdown = await condense_market_data(raw_combined, query)
            
        return {
            "snippets": snippets,
            "url_scraped": ", ".join(urls_to_scrape[:3]) if urls_to_scrape else None,
            "raw_markdown": raw_combined,
            "condensed_markdown": condensed_markdown,
            "combined_text": condensed_markdown if condensed_markdown else raw_combined
        }
    except Exception as e:
        logger.warning(f"Web search failed or timed out: {e}.")
            
    return {
        "snippets": [],
        "url_scraped": None,
        "raw_markdown": "",
        "condensed_markdown": "",
        "combined_text": ""
    }

async def scrape_ecommerce_pricing(keyword: str) -> dict:
    """
    Fetches marketplace pricing data by querying DuckDuckGo with site: operators
    targeting Tokopedia and Shopee. This is free, unlimited, and CAPTCHA-proof.
    Returns the extracted snippets as markdown and the condensed Markdown.
    """
    logger.info(f"Fetching marketplace pricing data for: {keyword}")
    
    # Two focused Tokopedia queries with proven DDG dorks:
    # Q1 '"pcs"': finds individual product listing pages (e.g. "Dimsum Siomay isi 100 pcs @ Rp.2500")
    # Q2 '"@ Rp"': finds store pages with multi-product listings and explicit prices per item
    platforms = [
        ("Tokopedia", f'site:tokopedia.com "{keyword}" "Rp" "pcs"'),
        ("Tokopedia", f'site:tokopedia.com "{keyword}" "@ Rp"'),
    ]
    
    all_snippets = []
    
    try:
        def run_marketplace_search():
            import time
            results_map = {}
            for platform_name, query in platforms:
                for attempt in range(3):
                    try:
                        with DDGS(verify=False, timeout=20) as ddgs:
                            results = ddgs.text(query, max_results=8, region="id-id")
                            results_map[platform_name] = list(results) if results else []
                            break
                    except Exception as e:
                        if attempt == 2:
                            logger.warning(f"DDG search failed for {platform_name}: {e}")
                            results_map[platform_name] = []
                        time.sleep(1)
            return results_map
        
        results_map = await asyncio.to_thread(run_marketplace_search)
        
        for platform_name, results in results_map.items():
            if results:
                platform_snippets = []
                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    link = r.get("href", "")
                    
                    # GIGO Protection (Garbage In, Garbage Out):
                    # Filter raw data BEFORE it hits the LLM. Only keep snippets that explicitly 
                    # contain both a price and a unit/quantity.
                    combined_text = f"{title} {body}".lower()
                    has_price = "rp" in combined_text
                    has_quantity = any(kw in combined_text for kw in [
                        "pcs", "isi", "gram", "pack", "box", "lembar", "kg",
                        "liter", "ml", "botol", "cup", "porsi", # Liquids / Foods
                        "lusin", "kodi", "pasang", "potong", "ukuran", "size" # Apparel / Bulk
                    ])
                    
                    if has_price and has_quantity:
                        platform_snippets.append(f"- **{title}**\n  {body}\n  Sumber: {link}")
                    else:
                        logger.debug(f"Filtered out low-quality snippet (GIGO protection): {title}")
                        
                if platform_snippets:
                    all_snippets.append(f"### {platform_name}")
                    all_snippets.extend(platform_snippets)
                    
    except Exception as e:
        logger.error(f"Marketplace pricing search failed: {e}")
    
    if not all_snippets:
        logger.warning("No marketplace pricing data found.")
        return {"condensed_markdown": "", "raw_markdown": "", "url": ""}
    
    raw_markdown = f"## Harga Marketplace untuk: {keyword}\n" + "\n".join(all_snippets)
    
    # Condense using LLM
    condensed = await condense_market_data(raw_markdown, f"harga {keyword}")
    
    return {"condensed_markdown": condensed, "raw_markdown": raw_markdown, "url": "Tokopedia (via DuckDuckGo)"}

async def scrape_pages(urls: list, query: str = "") -> str:
    """
    Scrapes multiple web pages using a single Crawl4AI instance and returns clean Markdown.
    """
    scraped_texts = []
    try:
        browser_config = BrowserConfig(headless=True)
        # Use query if provided, else use generic filter
        md_generator = DefaultMarkdownGenerator(
            content_filter=BM25ContentFilter(user_query=query, bm25_threshold=1.0)
        ) if query else DefaultMarkdownGenerator()
        
        run_config = CrawlerRunConfig(page_timeout=15000, markdown_generator=md_generator)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for url in urls:
                try:
                    result = await crawler.arun(url=url, config=run_config)
                    if result.success:
                        md_content = getattr(result.markdown, 'fit_markdown', None)
                        if not md_content:
                            md_content = getattr(result.markdown, 'raw_markdown', result.markdown)
                            
                        scraped_texts.append(f"=== KONTEN DARI {url} ===\n{md_content}")
                    else:
                        logger.warning(f"Crawl4AI failed to scrape {url}: {result.error_message}")
                except Exception as ex:
                    logger.warning(f"Failed to scrape page {url}: {ex}")
    except Exception as e:
        logger.error(f"Crawler failed to initialize: {e}")
        
    return "\n\n".join(scraped_texts)

async def condense_market_data(markdown_text: str, query: str) -> str:
    """
    Condenses the raw Markdown using LLM into a concise Markdown summary.
    TODO: [PRODUCTION-READY] Ensure BM25ContentFilter is applied before this step to reduce token usage. 
    The output should be Markdown prose, NOT JSON, as it will be consumed by the Assessment LLM later.
    """
    # Truncate markdown to prevent hitting token limits on free Hugging Face API
    markdown_text = markdown_text[:8000]
    
    system_prompt = get_condensation_prompt(query)
    
    # HuggingFace API is prone to 503 Model Loading, Rate Limits, and Timeouts.
    # We must retry the LLM call to prevent returning an empty string.
    for attempt in range(3):
        try:
            response = await async_call_llm(markdown_text, system_prompt)
            return response
        except Exception as e:
            logger.error(f"Condensation LLM call failed (attempt {attempt+1}/3): {e}")
            if attempt < 2:
                await asyncio.sleep(2)  # Wait before retrying
                
    logger.error("All condensation attempts failed, returning empty string.")
    return ""


