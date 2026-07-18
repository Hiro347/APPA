import asyncio
import json
import logging
import re
import os
import random
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from config import settings
from ai.inference import async_call_llm
from ai.prompts.condensation import CONDENSER_AGENTS, get_general_condensation_prompt
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter

logger = logging.getLogger(__name__)

class SearchArsenal:
    """
    Robust Search Provider Arsenal to guarantee uptime and prevent IP bans.
    Implements a fallback chain: DuckDuckGo (via Tor) -> SearXNG -> Yahoo HTML.
    Includes Exponential Backoff and Randomized Jitter to evade anti-bot WAFs.
    """
    def __init__(self):
        # We expect PROXY_URL from .env, but default to tor proxy if available
        self.proxy_url = os.getenv("PROXY_URL", "socks5h://tor:9050")
        self.searxng_url = os.getenv("SEARXNG_URL", "http://searxng:8080")
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
    def _jitter(self):
        """Randomized delay to mimic human behavior and evade rate limits."""
        time.sleep(random.uniform(0.5, 2.0))

    def _ddgs_search(self, query, max_results=5, region="id-id"):
        try:
            # We attempt the search via Tor proxy
            with DDGS(proxy=self.proxy_url, timeout=20) as ddgs:
                self._jitter()
                return list(ddgs.text(query, max_results=max_results, region=region))
        except Exception as e:
            logger.warning(f"DDGS (Proxy/Tor) failed: {e}")
            return None

    def _searxng_search(self, query, max_results=5):
        try:
            self._jitter()
            params = {"q": query, "format": "json"}
            resp = requests.get(f"{self.searxng_url}/search", params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for r in data.get("results", [])[:max_results]:
                    results.append({
                        "title": r.get("title", ""),
                        "body": r.get("content", ""),
                        "href": r.get("url", "")
                    })
                return results
            else:
                return None
        except Exception as e:
            logger.warning(f"SearXNG failed: {e}")
            return None

    def _yahoo_search(self, query, max_results=5):
        try:
            self._jitter()
            encoded = urllib.parse.quote(query)
            url = f"https://search.yahoo.com/search?p={encoded}"
            resp = requests.get(url, headers=self.headers, timeout=10)
            results = []
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for algo in soup.find_all('div', class_=lambda x: x and 'algo' in x):
                    title_el = algo.find('h3')
                    link_el = algo.find('a')
                    desc_el = algo.find('div', class_='compText')
                    if title_el and link_el and desc_el:
                        results.append({
                            "title": title_el.text.strip(),
                            "body": desc_el.text.strip(),
                            "href": link_el.get('href')
                        })
                        if len(results) >= max_results:
                            break
            return results
        except Exception as e:
            logger.warning(f"Yahoo Search failed: {e}")
            return []

    def execute(self, query, max_results=5, region="id-id"):
        """Executes the search strategy falling back gracefully."""
        # 1. Primary: DuckDuckGo with Proxies
        res = self._ddgs_search(query, max_results, region)
        if res: return res
            
        # 2. Secondary: SearXNG Metasearch
        res = self._searxng_search(query, max_results)
        if res: return res
            
        # 3. Tertiary: Yahoo HTML Scraper
        res = self._yahoo_search(query, max_results)
        return res if res else []


async def web_search(queries: list, visited_urls: set = None, query_type: str = "general") -> dict:
    """
    Performs DuckDuckGo web searches for a list of queries.
    """
    if visited_urls is None:
        visited_urls = set()
        
    logger.info(f"Searching web for queries: {queries}")
    snippets = []
    urls_to_scrape = []
    
    try:
        def run_search():
            arsenal = SearchArsenal()
            all_results = []
            for query in queries:
                results = arsenal.execute(query, max_results=5)
                if results:
                    all_results.extend(results)
            return all_results
                
        results = await asyncio.to_thread(run_search)
        
        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")
            link = r.get("href", "")
            snippets.append(f"Judul: {title}\nRingkasan: {body}\nSumber: {link}")
            if link and not link.endswith(".pdf") and link not in visited_urls:
                urls_to_scrape.append(link)
                visited_urls.add(link)
                
        # Alphabetical sort to prevent async race condition non-determinism
        snippets.sort()
                
        # 2. CRAWL: Scrape top page content via Crawl4AI
        scraped_text = ""
        if urls_to_scrape:
            # Scrape up to top 3 results for more comprehensive data
            scraped_text = await scrape_pages(urls_to_scrape[:3], queries[0] if queries else "")
            
        # 3. CONDENSE: Summarize scraped markdown AND snippets via LLM
        condensed_markdown = ""
        raw_combined = "=== HASIL PENCARIAN GOOGLE (DUCKDUCKGO) ===\n" + "\n\n".join(snippets)
        if scraped_text:
            raw_combined += "\n\n=== KONTEN WEBSITE (SCRAPED) ===\n" + scraped_text
            
        if raw_combined.strip():
            # Pass query_type to use the correct condensation agent
            res = await condense_market_data(raw_combined, queries[0] if queries else "", query_type=query_type)
            condensed_markdown = res.get("markdown", "")
            
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
    Fetches marketplace pricing data by querying DuckDuckGo with site: operators.
    """
    logger.info(f"Fetching marketplace pricing data for: {keyword}")
    
    platforms = [
        ("Tokopedia", f'site:tokopedia.com {keyword} harga'),
        ("Shopee", f'site:shopee.co.id {keyword} harga'),
        ("Lazada", f'site:lazada.co.id {keyword} harga'),
        ("TikTok Shop", f'site:tiktok.com {keyword} shop harga'),
        ("Instagram", f'site:instagram.com {keyword} harga'),
    ]
    
    all_snippets = []
    
    try:
        def run_marketplace_search():
            arsenal = SearchArsenal()
            results_map = {}
            for platform_name, search_query in platforms:
                results = arsenal.execute(search_query, max_results=8)
                results_map[platform_name] = results if results else []
            return results_map
        
        results_map = await asyncio.to_thread(run_marketplace_search)
        
        for platform_name, results in results_map.items():
            if results:
                platform_snippets = []
                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    link = r.get("href", "")
                    
                    combined_text = f"{title} {body}".lower()
                    
                    # We remove the aggressive Python-level quantity/price filters here
                    # because the LLM (condense_market_data) is fully equipped to parse
                    # and filter out invalid/missing prices via its system prompt.
                    platform_snippets.append(f"- **{title}**\n  {body}\n  Sumber: {link}")
                        
                if platform_snippets:
                    platform_snippets.sort() # Alphabetical sorting for determinism
                    all_snippets.append(f"### {platform_name}")
                    all_snippets.extend(platform_snippets)
                    
    except Exception as e:
        logger.error(f"Marketplace pricing search failed: {e}")
    
    if not all_snippets:
        logger.warning("No marketplace pricing data found via DDG.")
        return {"condensed_markdown": "", "raw_markdown": "", "url": "", "table_rows": []}
            
    raw_markdown = f"## Harga Marketplace untuk: {keyword}\n" + "\n".join(all_snippets)
    
    # Condense using LLM with price_fetch specialized prompt
    res = await condense_market_data(raw_markdown, f"harga {keyword}", query_type="price_fetch")
    
    return {
        "condensed_markdown": res.get("markdown", ""), 
        "raw_markdown": raw_markdown, 
        "url": "Data Scraping E-Commerce",
        "table_rows": res.get("table_rows", [])
    }

async def scrape_pages(urls: list, query: str = "") -> str:
    """
    Scrapes multiple web pages using a single Crawl4AI instance and returns clean Markdown.
    """
    scraped_texts = []
    try:
        browser_config = BrowserConfig(headless=True)
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

async def condense_market_data(markdown_text: str, query: str, query_type: str = "general") -> dict:
    """
    Condenses the raw Markdown using the SLM-MUX pattern. Routes to specialized agents based on query_type.
    """
    # Truncate markdown aggressively to prevent hitting token limits on local LLM context window (500 Error)
    # The freezing occurred because of Context Size memory leaks during heavy 10x iteration!
    markdown_text = markdown_text[:1500]
    
    prompt_generator = CONDENSER_AGENTS.get(query_type, get_general_condensation_prompt)
    system_prompt = prompt_generator(query)
    
    for attempt in range(3):
        try:
            # Force JSON mode
            response = await async_call_llm(markdown_text, system_prompt, enforce_json=True)
            logger.info(f"=== CONDENSER RAW JSON (Type: {query_type}) ===\n{response}")
            
            # Clean json
            cleaned = response
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
                
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as e:
                # LLM ignored extraction limits and hit the token cap, truncating the JSON mid-generation.
                # Salvage all fully generated objects by slicing to the last closing brace and sealing the array.
                logger.warning(f"JSON truncated. Attempting to salvage... {e}")
                last_brace = cleaned.rfind("}")
                if last_brace != -1:
                    salvaged = cleaned[:last_brace+1] + "\n  ]\n}"
                    try:
                        data = json.loads(salvaged)
                        logger.info("Successfully salvaged truncated JSON.")
                    except json.JSONDecodeError:
                        raise e
                else:
                    raise e
            
            # Build clean markdown and structured table rows
            md_lines = []
            table_rows = []
            
            prices = data.get("prices", [])
            if prices:
                md_lines.append("### Data Harga & Kompetitor")
                for p in prices:
                    p_name = p.get("product_name", "Produk")
                    
                    # Python-level Guardrail 1: Strictly ban packaging materials
                    lower_name = p_name.lower()
                    if any(bad in lower_name for bad in ["foil", "tray", "kemasan", "plastik", "wadah", "alumunium", "botol", "dus"]):
                        continue
                        
                    try:
                        total_price = float(p.get("total_price", 0))
                        
                        # Python-level Guardrail 3: LLM Zero-drop Fix
                        if 0 < total_price < 1000:
                            total_price *= 1000
                            
                        total_qty = float(p.get("total_quantity", 1))
                        
                        # Python-level Guardrail 4: Regex Quantity Fallback
                        if total_qty <= 1:
                            p_orig = p.get("original_price_text", "").lower()
                            qty_match = re.search(r'isi\s*(\d+)|(\d+)\s*(pcs|biji|porsi|box|pack|paket|buah|lembar)', p_name.lower() + " " + p_orig)
                            if qty_match:
                                total_qty = float(qty_match.group(1) or qty_match.group(2))
                                
                        if total_qty <= 0:
                            total_qty = 1
                            
                        # Normalize to per-pcs price
                        calculated_price = round(total_price / total_qty)
                        p_price = f"{calculated_price:,}".replace(",", ".")
                            
                    except (ValueError, TypeError):
                        continue
                        
                    p_store = p.get("store_name", "Tidak Diketahui")
                    p_orig = p.get("original_price_text", "")
                    
                    md_lines.append(f"- **{p_name}**: Rp {p_price} (Toko: {p_store})")
                    if p_orig:
                        md_lines.append(f"  *Info Asli: {p_orig}*")
                        
                    # Add to python structured table rows to bypass LLM table generation
                    table_rows.append([p_store, p_name, f"Rp {p_price}", f"Info Asli: {p_orig}" if p_orig else ""])
            
            findings = data.get("findings", [])
            if findings:
                md_lines.append("### Temuan Riset")
                for f in findings:
                    topic = f.get("topic", "Topik")
                    det = f.get("detail", "")
                    md_lines.append(f"- **{topic}**: {det}")
                    
            bento_hints = data.get("bento_hints", [])
            
            return {
                "markdown": "\n".join(md_lines),
                "hints": bento_hints,
                "table_rows": table_rows
            }
            
        except Exception as e:
            logger.error(f"Condensation LLM call failed (attempt {attempt+1}/3): {e}")
            if attempt < 2:
                await asyncio.sleep(2)
                
    logger.error("All condensation attempts failed, returning empty dict.")
    return {"markdown": "", "hints": [], "table_rows": []}

