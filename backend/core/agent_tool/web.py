import asyncio
import json
import logging
import re
import os
import urllib.parse
import requests
from bs4 import BeautifulSoup

from config import settings
from ai.inference import async_call_llm
from ai.prompts.condensation import CONDENSER_AGENTS, get_general_condensation_prompt
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

logger = logging.getLogger(__name__)

# Suppress urllib3 insecure request warnings when bypassing local proxies
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

IGNORED_DOMAINS = [
    "bing.com", "yahoo.com", "x.com", "facebook.com", "youtube.com", "vimeo.com",
    "dailymotion.com", "google.com", "play.google.com", "apps.apple.com",
    "wikipedia.org", "huangyuhui.net", "lowyat.net", "microsoft.com",
    "sportsnet.ca", "prohockeyrumors.com", "nhlrumors.com", "foodierate.com", "biggo.id", "traveloka.com"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
}

class SearchArsenal:
    """
    Lean & robust Search Engine provider using direct HTTP scrapers and APIs.
    Aggregates Yahoo, DDG HTML, SearXNG, and Google CSE with key rotation.
    """
    def __init__(self):
        self.searxng_url = os.getenv("SEARXNG_URL", "http://searxng:8080")
        keys_str = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GOOGLE_SEARCH_API_KEY", "")
        self.google_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        self.google_cx = os.getenv("GOOGLE_CX_ID")
        self.telemetry = {}

    def _google_search(self, query: str, max_results: int = 10, domain_filter: str = None) -> list:
        if not self.google_keys or not self.google_cx:
            self.telemetry["GoogleAPI"] = "SKIPPED (No Keys)"
            return []

        for key in self.google_keys:
            try:
                params = {
                    "key": key,
                    "cx": self.google_cx,
                    "q": query,
                    "gl": "id",
                    "num": min(max_results, 10)
                }
                resp = requests.get("https://customsearch.googleapis.com/customsearch/v1", params=params, timeout=5)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    results = []
                    for item in items:
                        href = item.get("link", "")
                        if any(domain in href.lower() for domain in IGNORED_DOMAINS):
                            continue
                        if domain_filter and domain_filter.lower() not in href.lower():
                            continue
                        results.append({"title": item.get("title", ""), "body": item.get("snippet", ""), "href": href})
                    self.telemetry["GoogleAPI"] = f"SUCCESS ({len(results)} results)"
                    return results
                elif resp.status_code == 429:
                    self.telemetry["GoogleAPI"] = "RATE_LIMITED (429)"
                    continue
            except Exception as e:
                logger.warning(f"Google API Search error: {e}")
                self.telemetry["GoogleAPI"] = f"FAILED ({type(e).__name__})"
        return []

    def _yahoo_search(self, query: str, max_results: int = 5, domain_filter: str = None) -> list:
        try:
            search_q = f"site:{domain_filter} {query}" if domain_filter and "site:" not in query else query
            url = f"https://search.yahoo.com/search?p={urllib.parse.quote(search_q)}"
            resp = requests.get(url, headers=HEADERS, timeout=6, verify=False)
            results = []
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for algo in soup.find_all('div', class_=lambda x: x and 'algo' in x):
                    title_el = algo.find('h3')
                    link_el = algo.find('a')
                    desc_el = algo.find('div', class_='compText')
                    if title_el and link_el and desc_el:
                        href = link_el.get('href', '')
                        ru_match = re.search(r'RU=([^/]+)', href)
                        if ru_match:
                            href = urllib.parse.unquote(ru_match.group(1))
                        if any(ignored in href.lower() for ignored in IGNORED_DOMAINS):
                            continue
                        if domain_filter and domain_filter.lower() not in href.lower():
                            continue
                        results.append({
                            "title": title_el.text.strip(),
                            "body": desc_el.text.strip(),
                            "href": href
                        })
                        if len(results) >= max_results:
                            break
                self.telemetry["Yahoo"] = f"SUCCESS ({len(results)} results)"
                return results
            self.telemetry["Yahoo"] = f"HTTP_{resp.status_code}"
            return []
        except Exception as e:
            logger.warning(f"Yahoo Search failed: {e}")
            self.telemetry["Yahoo"] = "FAILED"
            return []

    def _ddg_html_search(self, query: str, max_results: int = 10, domain_filter: str = None) -> list:
        try:
            url = "https://html.duckduckgo.com/html/"
            data = {"q": query, "b": "", "kl": "id-id"}
            resp = requests.post(url, data=data, headers=HEADERS, timeout=5, verify=False)
            results = []
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for res in soup.find_all('div', class_='result'):
                    title_el = res.find('a', class_='result__a')
                    snippet_el = res.find('a', class_='result__snippet')
                    if title_el:
                        href = title_el.get('href', '')
                        if href.startswith('//duckduckgo.com/l/?uddg='):
                            ru = re.search(r'uddg=([^&]+)', href)
                            if ru:
                                href = urllib.parse.unquote(ru.group(1))
                        if any(ignored in href.lower() for ignored in IGNORED_DOMAINS):
                            continue
                        if domain_filter and domain_filter.lower() not in href.lower():
                            continue
                        results.append({
                            "title": title_el.text.strip(),
                            "body": snippet_el.text.strip() if snippet_el else "",
                            "href": href
                        })
                        if len(results) >= max_results:
                            break
                self.telemetry["DDG_HTML"] = f"SUCCESS ({len(results)} results)"
                return results
            self.telemetry["DDG_HTML"] = f"HTTP_{resp.status_code}"
            return []
        except requests.exceptions.RequestException as e:
            logger.debug(f"DDG HTML search failed (Network/SSL): {e}")
            self.telemetry["DDG_HTML"] = "FAILED (Network/SSL)"
            return []
        except Exception as e:
            logger.warning(f"DDG HTML search failed: {e}")
            self.telemetry["DDG_HTML"] = "FAILED"
            return []

    def _searxng_search(self, query: str, max_results: int = 5, domain_filter: str = None) -> list:
        try:
            params = {"q": query, "format": "json", "engines": "google,bing,duckduckgo,qwant,yahoo"}
            try:
                resp = requests.get(f"{self.searxng_url}/search", params=params, timeout=5)
            except requests.exceptions.RequestException:
                resp = requests.get("http://localhost:8081/search", params=params, timeout=5)

            if resp.status_code == 200:
                data = resp.json()
                results = []
                for r in data.get("results", []):
                    href = r.get("url", "")
                    if any(ignored in href.lower() for ignored in IGNORED_DOMAINS):
                        continue
                    if domain_filter and domain_filter.lower() not in href.lower():
                        continue
                    results.append({"title": r.get("title", ""), "body": r.get("content", ""), "href": href})
                    if len(results) >= max_results:
                        break
                self.telemetry["SearXNG"] = f"SUCCESS ({len(results)} results)"
                return results
            self.telemetry["SearXNG"] = f"HTTP_{resp.status_code}"
            return []
        except Exception as e:
            logger.warning(f"SearXNG search failed: {e}")
            self.telemetry["SearXNG"] = "FAILED"
            return []

    def execute(self, query: str, max_results: int = 15, use_google: bool = True, domain_filter: str = None) -> list:
        self.telemetry = {"GoogleAPI": "SKIPPED", "Yahoo": "SKIPPED", "DDG_HTML": "SKIPPED", "SearXNG": "SKIPPED"}
        combined = {}

        # 1. Google Custom Search (if key is set)
        if use_google:
            g_res = self._google_search(query, max_results=max_results, domain_filter=domain_filter)
            for r in g_res:
                combined[r["href"]] = r

        # 2. Yahoo Search
        y_res = self._yahoo_search(query, max_results=max_results, domain_filter=domain_filter)
        for r in y_res:
            combined[r["href"]] = r

        # 3. DuckDuckGo HTML Scraper
        ddg_res = self._ddg_html_search(query, max_results=max_results, domain_filter=domain_filter)
        for r in ddg_res:
            combined[r["href"]] = r

        # 4. SearXNG Metasearch (Fallback)
        sx_res = self._searxng_search(query, max_results=max_results, domain_filter=domain_filter)
        for r in sx_res:
            combined[r["href"]] = r

        return list(combined.values())


def _is_product_page(url: str) -> bool:
    url_lower = url.lower()
    url_clean = re.sub(r'^https?://(www\.)?', '', url_lower)
    if url_clean in ["tokopedia.com", "tokopedia.com/", "shopee.co.id", "shopee.co.id/", "lazada.co.id", "lazada.co.id/", "tiktok.com", "tiktok.com/"]:
        return False
    if "tokopedia.com" in url_lower:
        ignore_paths = ["/find/", "/search", "/discovery", "/p/", "/category", "/toko/", "/brand/", "/people/", "/blog/", "/help/", "/promo/"]
        return not any(p in url_lower for p in ignore_paths)
    if "shopee.co.id" in url_lower:
        return "-i." in url_lower or "/product/" in url_lower
    if "lazada.co.id" in url_lower:
        if "/products/" in url_lower:
            return not any(p in url_lower for p in ["/tag/", "/category/", "/shop/"])
        return False
    if "tiktok.com" in url_lower:
        return "/video/" in url_lower or "/t/" in url_lower
    ignore_general = ["/category", "/search", "/tag", "/blog", "/about", "/contact", "/author", "/page/"]
    return not any(p in url_lower for p in ignore_general)


async def scrape_pages(urls: list, query: str = "") -> str:
    """
    Scrapes web pages using Crawl4AI and returns clean Markdown.
    """
    scraped_texts = []
    try:
        browser_config = BrowserConfig(headless=True, ignore_https_errors=True)
        from crawl4ai.content_filter_strategy import PruningContentFilter
        md_generator = DefaultMarkdownGenerator(content_filter=PruningContentFilter(threshold=0.48, threshold_type="dynamic"))
        
        run_config = CrawlerRunConfig(
            page_timeout=10000, 
            markdown_generator=md_generator,
            delay_before_return_html=1.5,
            cache_mode=CacheMode.BYPASS,
            magic=True
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for url in urls:
                try:
                    result = await crawler.arun(url=url, config=run_config)
                    if result.success:
                        md_content = getattr(result.markdown, 'fit_markdown', None) or getattr(result.markdown, 'raw_markdown', str(result.markdown))
                        # Ignore anti-bot / login block pages
                        if any(block_term in md_content.lower() for block_term in ["halaman tidak tersedia", "sepertinya anda belum masuk", "please enable javascript", "captcha"]):
                            continue
                        scraped_texts.append(f"=== KONTEN DARI {url} ===\n{md_content}")
                    else:
                        logger.warning(f"Crawl4AI failed for {url}: {result.error_message}")
                except Exception as ex:
                    logger.warning(f"Failed to scrape page {url}: {ex}")
    except Exception as e:
        logger.error(f"Crawler failed to initialize: {e}")
        
    return "\n\n".join(scraped_texts)


async def scrape_ecommerce_pricing(keyword: str) -> dict:
    """
    Queries e-commerce platforms and extracts marketplace pricing data.
    """
    logger.info(f"Fetching marketplace pricing data for: {keyword}")
    
    platforms = [
        ("Tokopedia", f'harga {keyword} tokopedia', True, "tokopedia.com"),
        ("Shopee", f'harga {keyword} shopee', True, "shopee.co.id"),
        ("TikTok Shop", f'harga {keyword} tiktok', False, "tiktok.com"),
        ("Lazada", f'harga {keyword} lazada', True, "lazada.co.id"),
        ("Marketplace General", f'harga {keyword}', True, ""),
    ]
    
    all_snippets = []
    telemetry_map = {}
    urls_to_crawl = []
    
    try:
        def search_platform(platform_name, search_query, use_google, domain_filter):
            arsenal = SearchArsenal()
            results = arsenal.execute(search_query, max_results=15, use_google=use_google, domain_filter=domain_filter)
            return platform_name, results, arsenal.telemetry

        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(None, search_platform, p, q, ug, df) for p, q, ug, df in platforms]
        results_list = await asyncio.gather(*tasks)

        for platform_name, results, telemetry in results_list:
            telemetry_map[platform_name] = telemetry
            if results:
                platform_snippets = []
                added_count = 0
                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    link = r.get("href", "")
                    if not any(bad in link.lower() for bad in ["buyer/login", "account-link/goto", "homepage", "/web"]):
                        platform_snippets.append(f"- **{title}**\n  {body}\n  Sumber: {link}")
                        if _is_product_page(link) and link not in urls_to_crawl and added_count < 2:
                            urls_to_crawl.append(link)
                            added_count += 1

                if platform_snippets:
                    all_snippets.append(f"### {platform_name}")
                    all_snippets.extend(platform_snippets)

        scraped_text = ""
        if urls_to_crawl:
            scraped_text = await scrape_pages(urls_to_crawl[:5], keyword)

    except Exception as e:
        logger.error(f"Marketplace pricing search failed: {e}")

    raw_markdown = f"## Harga Marketplace untuk: {keyword}\n"
    if scraped_text:
        raw_markdown += f"\n## Hasil Crawl4AI (Deep Scrape Product Detail Pages)\n{scraped_text}\n\n"
    raw_markdown += "## Hasil Snippet Pencarian Marketplace\n" + "\n".join(all_snippets)

    res = await condense_market_data(raw_markdown, f"harga {keyword}", query_type="price_fetch")

    return {
        "condensed_markdown": res.get("markdown", ""),
        "raw_markdown": raw_markdown,
        "url": "Data Scraping E-Commerce",
        "table_rows": res.get("table_rows", []),
        "raw_llm_json": res.get("raw_llm_json", {}),
        "telemetry": telemetry_map
    }


async def web_search(queries: list, visited_urls: set = None, query_type: str = "general") -> dict:
    """
    Performs multi-provider web search and summarizes results.
    """
    if visited_urls is None:
        visited_urls = set()

    logger.info(f"Searching web for queries: {queries}")
    snippets = []
    urls_to_scrape = []

    try:
        def run_search():
            arsenal = SearchArsenal()
            all_res = []
            for q in queries:
                res = arsenal.execute(q, max_results=8, use_google=False)
                if res:
                    all_res.extend(res)
            return all_res

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, run_search)

        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")
            link = r.get("href", "")
            snippets.append(f"Judul: {title}\nRingkasan: {body}\nSumber: {link}")
            if link and not link.endswith(".pdf") and link not in visited_urls:
                urls_to_scrape.append(link)
                visited_urls.add(link)

        snippets.sort()
        scraped_text = ""
        if urls_to_scrape:
            scraped_text = await scrape_pages(urls_to_scrape[:3], queries[0] if queries else "")

        raw_combined = "=== HASIL PENCARIAN WEB ===\n" + "\n\n".join(snippets)
        if scraped_text:
            raw_combined += "\n\n=== KONTEN WEBSITE (SCRAPED) ===\n" + scraped_text

        condensed_markdown = ""
        if raw_combined.strip():
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
        logger.warning(f"Web search failed: {e}")

    return {
        "snippets": [],
        "url_scraped": None,
        "raw_markdown": "",
        "condensed_markdown": "",
        "combined_text": ""
    }


def _verify_price_in_text(price: float, text: str) -> bool:
    if not text or price <= 0:
        return False
    text = text.lower()
    price_int = int(price)
    price_str = str(price_int)
    price_dot = f"{price_int:,}".replace(",", ".")
    price_comma = f"{price_int:,}"
    
    if price_str in text or price_dot in text or price_comma in text:
        return True
        
    if price_int % 1000 == 0:
        thousands = price_int // 1000
        k_patterns = [f"{thousands}rb", f"{thousands} rb", f"{thousands}k", f"{thousands} k", f"{thousands}ribu", f"{thousands} ribu"]
        if any(pat in text for pat in k_patterns):
            return True
            
    if f"{price_dot},00" in text or f"{price_comma}.00" in text:
        return True
        
    return False


async def condense_market_data(markdown_text: str, query: str, query_type: str = "general") -> dict:
    """
    Condenses raw Markdown using specialized LLM prompts.
    """
    markdown_text = re.sub(r'\(https?://[^\)]+\)', '', markdown_text)
    markdown_text = re.sub(r'https?://\S+', '', markdown_text)
    markdown_text = markdown_text[:12000]

    prompt_generator = CONDENSER_AGENTS.get(query_type, get_general_condensation_prompt)
    system_prompt = prompt_generator(query)

    for attempt in range(3):
        try:
            response = await async_call_llm(markdown_text, system_prompt, enforce_json=True)
            cleaned = response
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as e:
                last_brace = cleaned.rfind("}")
                if last_brace != -1:
                    salvaged = cleaned[:last_brace+1] + "\n  ]\n}"
                    data = json.loads(salvaged)
                else:
                    raise e

            md_lines = []
            table_rows = []

            prices = data.get("prices", [])
            if prices:
                candidate_items = []
                for p in prices:
                    p_name = p.get("product_name", "Produk")
                    lower_name = p_name.lower()
                    
                    # Exclude packaging materials
                    if any(bad in lower_name for bad in ["foil", "tray", "kemasan", "plastik", "wadah", "alumunium", "botol", "dus"]):
                        continue

                    # Exclude machinery for service queries
                    if not any(k in query.lower() for k in ["mesin", "printer", "alat", "seri"]):
                        if any(bad in lower_name for bad in ["mesin", "printer", "head", "tinta", "sparepart", "software", "hardware"]):
                            continue

                    total_price = p.get("total_price")
                    if total_price is None:
                        continue
                    try:
                        total_price = float(total_price)
                        if total_price <= 0:
                            continue
                    except (ValueError, TypeError):
                        continue

                    if total_price < 1000 and re.search(r'(ribu|rb|k\b)', p.get("original_price_text", "").lower()):
                        total_price *= 1000

                    try:
                        total_qty = float(p.get("total_quantity", 1.0) or 1.0)
                    except (ValueError, TypeError):
                        total_qty = 1.0
                    if total_qty <= 0:
                        total_qty = 1.0

                    calc_price = round(total_price / total_qty)
                    p_store = p.get("store_name", "Tidak Diketahui")
                    p_orig = p.get("original_price_text", "")

                    # Anti-Hallucination: verify price string exists in source text
                    if not _verify_price_in_text(total_price, markdown_text):
                        logger.warning(f"Dropping unverified price for {p_name}: '{total_price}'")
                        continue

                    candidate_items.append({
                        "store": p_store,
                        "name": p_name,
                        "calc_price": calc_price,
                        "total_price": total_price,
                        "total_qty": total_qty,
                        "orig": p_orig
                    })

                md_lines.append("### Data Harga & Kompetitor")
                for item in candidate_items:
                    p_price = f"{int(item['calc_price']):,}".replace(",", ".")
                    unit_label = " / pcs" if item['total_qty'] > 1.0 else ""
                    md_lines.append(f"- **{item['name']}**: Rp {p_price}{unit_label} (Toko: {item['store']})")
                    if item['orig']:
                        md_lines.append(f"  *Info Asli: {item['orig']}*")
                    
                    total_info = f"Info Asli: {item['orig']}" if item['orig'] else f"Total: Rp {int(item['total_price']):,}".replace(",", ".")
                    table_rows.append([item['store'], item['name'], f"Rp {p_price}{unit_label}", total_info])

            findings = data.get("findings", [])
            if findings:
                md_lines.append("### Temuan Riset")
                for f in findings:
                    topic = f.get("topic", "Topik")
                    det = f.get("detail", "")
                    md_lines.append(f"- **{topic}**: {det}")

            return {
                "markdown": "\n".join(md_lines),
                "table_rows": table_rows,
                "raw_llm_json": data
            }

        except Exception as e:
            logger.error(f"Condensation LLM call failed (attempt {attempt+1}/3): {e}")
            if attempt < 2:
                await asyncio.sleep(1)

    return {"markdown": "", "hints": [], "table_rows": [], "raw_llm_json": {}}
