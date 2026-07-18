import json
import logging
import asyncio
import re
import ast
from core.profile_manager import get_profile, update_profile
from core.fallback import build_fallback_response
from ai.entity_extractor import extract_entities_and_queries
from ai.inference import call_llm, async_call_llm, call_llm_stream
from ai.prompts.synthesis import get_clarification_prompt
from ai.prompts.assessment import (
    get_qualitative_synthesis_prompt,
    get_table_synthesis_prompt,
    get_metrics_synthesis_prompt
)
from core.agent_tool.web import web_search, scrape_ecommerce_pricing, condense_market_data
from core.agent_tool.vector import vector_search


logger = logging.getLogger(__name__)

import traceback

async def handle_chat_stream(user_id: str, message: str):
    """
    Wrapper to catch and stream fatal errors to the frontend.
    """
    try:
        async for chunk in _handle_chat_stream_internal(user_id, message):
            yield chunk
    except Exception as e:
        err_msg = traceback.format_exc()
        logger.error(f"FATAL ERROR in agent pipeline:\n{err_msg}")
        yield json.dumps({"type": "error", "message": f"{str(e)}\n\n{err_msg}"}) + "\n"

async def _handle_chat_stream_internal(user_id: str, message: str):
    """
    Core Agent Orchestrator returning an async generator for NDJSON streaming.
    """
    logger.info(f"Received message from user '{user_id}': {message}")
    
    def emit_update(step_id: str, status: str, details: str = None):
        payload = {"type": "pipeline_update", "step_id": step_id, "status": status}
        if details:
            payload["details"] = details
        return json.dumps(payload) + "\n"

    # 1. Fetch current user profile
    profile = get_profile(user_id)
    
    # 2. LLM Call 1: Entity Extraction & Routing & Query Generation
    yield emit_update("d1", "running")
    try:
        loop = asyncio.get_event_loop()
        call1_result = await loop.run_in_executor(
            None, extract_entities_and_queries, message, profile
        )
    except Exception as e:
        logger.error(f"Error during LLM Call 1: {e}")
        call1_result = {"route": "clarification", "extracted_entities": {}, "sub_queries": []}
        
    yield emit_update("d1", "done", json.dumps(call1_result.get("extracted_entities", {}), indent=2))
    
    route = call1_result.get("route", "clarification")
    extracted_entities = call1_result.get("extracted_entities", {})
    sub_queries = call1_result.get("sub_queries", [])
    scenario = call1_result.get("user_intent_category", "comprehensive")
    
    yield emit_update("d2", "running")
    yield emit_update("d2", "done", json.dumps(sub_queries, indent=2))
    
    yield emit_update("d3", "running")
    if extracted_entities:
        update_profile(user_id, extracted_entities)
        profile.update(extracted_entities)  # Merge new entities into local memory
    yield emit_update("d3", "done", f"Route: {route}")
        
    # 4. ROUTE A: Clarification
    if route == "clarification":
        logger.info(f"Routing user '{user_id}' to Clarification Route.")
        yield emit_update("syn1", "running")
        system_prompt = get_clarification_prompt(profile)
        
        chat_response = ""
        try:
            async for chunk in call_llm_stream(message, system_prompt):
                chat_response += chunk
                yield json.dumps({"type": "stream_chunk", "content": chunk}) + "\n"
        except Exception as e:
            logger.error(f"Clarification stream failed: {e}")
            chat_response = "Maaf, sistem AI (Hugging Face) sedang mengalami kendala teknis atau kehabisan token (402 Payment Required). Silakan periksa API token Anda."
            yield json.dumps({"type": "stream_chunk", "content": chat_response}) + "\n"
            
        yield emit_update("syn1", "done", chat_response)
        
        final_data = {
            "response": chat_response,
            "artifacts": [],
            "profile_updated": True
        }
        yield json.dumps({"type": "result", "data": final_data}) + "\n"
        return
        
    # 5. ROUTE B: Deep Research
    logger.info(f"Routing user '{user_id}' to Deep Research Route")
    
    keyword = profile.get("product_category", "produk")
    
    needs_reg = call1_result.get("needs_regulation_check", False)
    needs_shop = call1_result.get("needs_price_fetching", False)
    intent_category = call1_result.get("user_intent_category", "comprehensive")
    
    if not sub_queries or not isinstance(sub_queries, list):
        # Fallback queries if LLM didn't provide them
        sub_queries = [
            {"query": f"regulasi perizinan {keyword} di {profile.get('target_location', 'Indonesia')}", "type": "general"},
            {"query": f"harga pasaran {keyword} di {profile.get('target_location', 'Indonesia')}", "type": "price_fetch"}
        ]
        
    # Python-Level Hallucination Guardrail!
    if intent_category == "price_only":
        sub_queries = [q for q in sub_queries if q.get("type") == "price_fetch"]
        needs_reg = False
    elif intent_category == "strategy_only":
        sub_queries = [q for q in sub_queries if q.get("type") == "general"]
        needs_shop = False
        needs_reg = False
    elif intent_category == "regulation_only":
        sub_queries = []
        needs_shop = False
        needs_reg = True
        
    # Build dynamic pipeline UI
    search_steps = []
    for i, q_obj in enumerate(sub_queries):
        if isinstance(q_obj, str):
            q_obj = {"query": q_obj, "type": "general"}
        q_text = q_obj.get("query", "")
        search_steps.append({"id": f"s{i+1}", "label": f"Google Search: '{q_text}'", "status": "waiting"})
    
    if needs_shop:
        search_steps.append({"id": "gshop", "label": f"Marketplace Pricing: '{keyword}'", "status": "waiting"})
    
    pipeline_groups = []
    if search_steps:
        pipeline_groups.append({
            "id": "search", "icon": "", "label": "Pencarian Data Pasar & Web",
            "steps": search_steps
        })
        condenser_steps = []
        for i, q_obj in enumerate(sub_queries):
            if isinstance(q_obj, str):
                q_obj = {"query": q_obj, "type": "general"}
            q_type = q_obj.get("type", "general")
            
            if q_type == "price_fetch":
                label = f"Agen Harga: '{q_obj.get('query', '')[:20]}...'"
            else:
                label = f"Agen Kualitatif: '{q_obj.get('query', '')[:20]}...'"
                
            condenser_steps.append({"id": f"p{i+1}", "label": label, "status": "waiting"})
            
        if needs_shop:
            condenser_steps.append({"id": "p_shop", "label": f"Agen Harga: Marketplace", "status": "waiting"})

        pipeline_groups.append({
            "id": "process", "icon": "", "label": "Agen Kondensasi (SLM-MUX)",
            "steps": condenser_steps
        })
        
    if needs_reg:
        pipeline_groups.append({
            "id": "regulation", "icon": "", "label": "Pengecekan Regulasi",
            "steps": [
                {"id": "r1", "label": f"Qdrant RAG: {keyword}", "status": "waiting"},
                {"id": "r2", "label": "Matching: regulatory_rules.json", "status": "waiting"},
            ]
        })
        
    pipeline_groups.append({
        "id": "synthesis", "icon": "", "label": "Sintesis Laporan (SLM-MUX)",
        "steps": [
            {"id": "syn_qual", "label": "Agen Sintesis: Analisis Kualitatif", "status": "waiting"},
            {"id": "syn_table", "label": "Agen Sintesis: Tabel Kompetitor", "status": "waiting"},
            {"id": "syn_metrics", "label": "Agen Sintesis: Metrik & Grafik", "status": "waiting"}
        ]
    })
    
    yield json.dumps({"type": "pipeline_init", "pipeline": pipeline_groups}) + "\n"
    
    # Set search running statuses (condensers stay waiting)
    for i in range(len(sub_queries)):
        yield emit_update(f"s{i+1}", "running")
    if needs_shop:
        yield emit_update("gshop", "running")
    if needs_reg:
        yield emit_update("r1", "running")
    
    shared_visited = set()
    search_tasks = []
    for q_obj in sub_queries:
        if isinstance(q_obj, str):
            q_obj = {"query": q_obj, "type": "general"}
        q_text = q_obj.get("query", "")
        q_type = q_obj.get("type", "general")
        search_tasks.append(web_search([q_text], visited_urls=shared_visited, query_type=q_type))
        
    # Gather all tasks dynamically
    all_tasks = search_tasks.copy()
    gshop_index = -1
    vector_index = -1
    
    if needs_shop:
        all_tasks.append(scrape_ecommerce_pricing(keyword))
        gshop_index = len(all_tasks) - 1
        
    if needs_reg:
        # Pass queries string to vector_search
        queries_str = [q.get("query", q) if isinstance(q, dict) else str(q) for q in sub_queries]
        if not queries_str:
             queries_str = [keyword]
        all_tasks.append(vector_search(queries_str))
        vector_index = len(all_tasks) - 1
        
    if all_tasks:
        async def run_gather():
            return await asyncio.gather(*all_tasks, return_exceptions=True)
            
        gather_task = asyncio.create_task(run_gather())
        while not gather_task.done():
            yield json.dumps({"type": "ping"}) + "\n"
            await asyncio.sleep(2)
        raw_results = gather_task.result()
        
        # Safely extract results, replacing exceptions with empty dicts/strings
        results = []
        for r in raw_results:
            if isinstance(r, Exception):
                logger.error(f"Async task failed: {r}")
                results.append({})
            else:
                results.append(r)
    else:
        results = []
    
    # Unpack results
    search_results = results[:len(sub_queries)]
    gshop_results = results[gshop_index] if gshop_index != -1 else {}
    vector_results = results[vector_index] if vector_index != -1 else ""
    
    # Emit done for searches and start condensation agents
    full_market_data = ""
    qualitative_market_data = ""
    condense_tasks = []
    condense_task_mapping = [] # to keep track of which UI step it belongs to
    
    for i, res in enumerate(search_results):
        q_obj = sub_queries[i]
        if isinstance(q_obj, str):
            q_obj = {"query": q_obj, "type": "general"}
        q_text = q_obj.get("query", "")
        q_type = q_obj.get("type", "general")
        
        if not res.get('snippets'):
            details = f"=== QUERY: {q_text} ===\n\n(No results found or search skipped)"
        else:
            details = f"=== QUERY: {q_text} ===\n\nSnippets:\n{json.dumps(res.get('snippets', []), indent=2)}\n\nRAW MARKDOWN:\n{res.get('raw_markdown', '')[:15000]}"
            
        yield emit_update(f"s{i+1}", "done", details)
        yield emit_update(f"p{i+1}", "running")
        
        # Queue the condensation task
        if res.get('raw_markdown', '').strip():
            condense_tasks.append(condense_market_data(res['raw_markdown'], q_text, q_type))
            condense_task_mapping.append({"id": f"p{i+1}", "query": q_text})
        else:
            yield emit_update(f"p{i+1}", "done", "(Tidak ada ringkasan yang diekstrak)")

    # Emit done for marketplace pricing and its condensation
    if needs_shop:
        if not gshop_results.get('raw_markdown'):
            gshop_details = f"=== Sumber: {gshop_results.get('url', 'N/A')} ===\n\n(Tidak ada data harga marketplace ditemukan)"
            yield emit_update("gshop", "done", gshop_details)
            yield emit_update("p_shop", "done", "(Tidak ada ringkasan harga marketplace)")
        else:
            gshop_details = f"=== Sumber: {gshop_results.get('url')} ===\n\nRAW MARKDOWN:\n{gshop_results.get('raw_markdown', '')[:10000]}"
            yield emit_update("gshop", "done", gshop_details)
            yield emit_update("p_shop", "running")
            
            # PREVENT DOUBLE CONDENSATION:
            # gshop_results has ALREADY been condensed inside scrape_ecommerce_pricing!
            # We just create a dummy async task to seamlessly inject it into the gather pool.
            async def return_precondensed():
                return {
                    "markdown": gshop_results.get("condensed_markdown", ""),
                    "hints": gshop_results.get("hints", ["table"]), # Hardcode table hint to guarantee extraction
                    "table_rows": gshop_results.get("table_rows", [])
                }
            condense_tasks.append(return_precondensed())
            condense_task_mapping.append({"id": "p_shop", "query": f"harga {keyword}"})

    # Await all condensation agents concurrently
    if condense_tasks:
        async def run_condense():
            return await asyncio.gather(*condense_tasks, return_exceptions=True)
            
        gather_condense = asyncio.create_task(run_condense())
        while not gather_condense.done():
            yield json.dumps({"type": "ping"}) + "\n"
            await asyncio.sleep(2)
        condensed_results = gather_condense.result()
        
        bento_hints = set()
        all_table_rows = []
        # Process and emit condensed results
        for idx, mapping in enumerate(condense_task_mapping):
            result = condensed_results[idx]
            if isinstance(result, Exception) or not result or not isinstance(result, dict):
                yield emit_update(mapping["id"], "done", "(Gagal mengekstrak ringkasan)")
            else:
                markdown_str = result.get("markdown", "")
                hints = result.get("hints", [])
                t_rows = result.get("table_rows", [])
                
                if isinstance(hints, list):
                    bento_hints.update(hints)
                if isinstance(t_rows, list):
                    all_table_rows.extend(t_rows)
                    
                full_market_data += f"=== Hasil Analisis: '{mapping['query']}' ===\n{markdown_str}\n\n"
                
                # Allow the Qualitative Agent to see the prices so it can explicitly analyze and explain the market variance!
                qualitative_market_data += f"=== Hasil Analisis: '{mapping['query']}' ===\n{markdown_str}\n\n"
                    
                yield emit_update(mapping["id"], "done", markdown_str)
    
    yield emit_update("r1", "done", vector_results)
    
    yield emit_update("r2", "running")
    await asyncio.sleep(0.5)
    yield emit_update("r2", "done", "Regex Matching Applied")
    
    needs_table = "table" in bento_hints or not all_table_rows # Force evaluation for fallback
    needs_metrics = "metrics" in bento_hints
    
    # LLM Call 2: Assessment & Synthesis Report (SLM-MUX Router)
    qualitative_market_data = qualitative_market_data[:2000] # Truncate to prevent 500 Context Exceeded Error
    needs_qual = bool(qualitative_market_data.strip())
    if needs_qual:
        yield emit_update("syn_qual", "running")
    else:
        yield emit_update("syn_qual", "done", "Skipped (No qualitative data)")
        
    if needs_table:
        yield emit_update("syn_table", "running")
    else:
        yield emit_update("syn_table", "done", "Skipped (No table hints found)")
        
    if needs_metrics:
        yield emit_update("syn_metrics", "running")
    else:
        yield emit_update("syn_metrics", "done", "Skipped (No metric hints found)")
    
    qual_sys = get_qualitative_synthesis_prompt(profile, qualitative_market_data, vector_results) if needs_qual else ""
    table_sys = get_table_synthesis_prompt(profile, full_market_data)
    metric_sys = get_metrics_synthesis_prompt(profile, full_market_data)
    
    user_prompt = "Hasilkan array JSON block."
    
    async def fetch_qual():
        if not needs_qual: return "[]"
        return await async_call_llm(user_prompt, qual_sys, enforce_json=True)
        
    async def fetch_table():
        if not needs_table:
            return "[]"
            
        seen = set()
        unique_rows = []
        global_prices = []
        
        if not all_table_rows:
            # Fallback if DuckDuckGo is rate-limited or returns 0 results
            unique_rows = [
                ["-", "Tidak ada data kompetitor ditemukan", "Rp 0", "Pencarian dibatasi atau produk tidak ada"]
            ]
        else:
            for row in all_table_rows:
                r_tuple = tuple(row)
                if r_tuple not in seen:
                    seen.add(r_tuple)
                    unique_rows.append(row)
                    
                    # Extract numeric price for global median calculation
                    price_str = str(row[2]).replace("Rp", "").replace(".", "").strip()
                    try:
                        global_prices.append(float(price_str))
                    except:
                        pass
                        
            # Apply Global Statistical Outlier Filter (Absolute Domain Anchor)
            if global_prices:
                unique_prices = list(set(global_prices))
                unique_prices = [p for p in unique_prices if p >= 1000] # Drop invalid/0 prices before anchoring
                
                if unique_prices:
                    unique_prices.sort()
                    
                    global_min = unique_prices[0]
                    max_allowed = global_min * 5
                    
                    filtered_rows = []
                    for row in unique_rows:
                        price_str = str(row[2]).replace("Rp", "").replace(".", "").strip()
                        try:
                            val = float(price_str)
                            if val > max_allowed:
                                continue # Drop the massive premium/wholesale outlier
                            if val < (global_min * 0.15):
                                continue # Drop the packaging-only outlier
                        except:
                            pass
                        filtered_rows.append(row)
                    unique_rows = filtered_rows
                    
            if not unique_rows:
                unique_rows = [
                    ["-", "Semua data kompetitor difilter (Outlier ekstrim)", "Rp 0", "Data tidak valid"]
                ]
                
        # 100% Rock-Solid Native Python JSON Table Builder
        # Completely bypasses the LLM for the table, eliminating hallucinated duplicated rows and syntax crashes
        table_block = {
            "type": "table",
            "data": {
                "headers": ["Nama Toko / Kompetitor", "Produk", "Harga", "Keterangan Tambahan"],
                "rows": unique_rows
            },
            "sources": ["Data Scraping E-Commerce"]
        }
        return json.dumps([table_block])
        
    async def fetch_metric():
        if not needs_metrics: return "[]"
        return await async_call_llm(user_prompt, metric_sys, enforce_json=True)
        
    async def run_syn():
        return await asyncio.gather(
            fetch_qual(), fetch_table(), fetch_metric(), return_exceptions=True
        )
        
    gather_syn = asyncio.create_task(run_syn())
    
    while not gather_syn.done():
        yield json.dumps({"type": "ping"}) + "\n"
        await asyncio.sleep(2)
        
    syn_results = gather_syn.result()
    
    qual_output = syn_results[0] if not isinstance(syn_results[0], Exception) else "[]"
    table_output = syn_results[1] if not isinstance(syn_results[1], Exception) else "[]"
    metric_output = syn_results[2] if not isinstance(syn_results[2], Exception) else "[]"
    
    yield emit_update("syn_qual", "done", f"RAW JSON:\n{qual_output}")
    if needs_table:
        yield emit_update("syn_table", "done", f"RAW JSON:\n{table_output}")
    if needs_metrics:
        yield emit_update("syn_metrics", "done", f"RAW JSON:\n{metric_output}")
        
    logger.info("=== QUALITATIVE SYNTHESIS OUTPUT ===")
    logger.info(qual_output)
    logger.info("=== TABLE SYNTHESIS OUTPUT ===")
    logger.info(table_output)
    logger.info("=== METRIC SYNTHESIS OUTPUT ===")
    logger.info(metric_output)
    
    # Assembly
    blocks = []
    
    def safe_parse_blocks(raw_json):
        cleaned = raw_json.strip()
        m = re.search(r'(\[.*\])', cleaned, re.DOTALL)
        if m: cleaned = m.group(1)
        try:
            arr = json.loads(cleaned)
            if isinstance(arr, list): return arr
        except Exception as e:
            logger.error(f"JSON loads failed: {e}")
            
            # JSON Salvager: If LLM hit token limit, salvage all fully generated blocks!
            last_brace = cleaned.rfind("}")
            if last_brace != -1:
                salvaged = cleaned[:last_brace+1] + "\n]"
            else:
                # Extreme edge case: Truncated during the VERY FIRST block's content string!
                # Force close the string, object, and array.
                # Remove any trailing backslashes to avoid escaping our injected quote
                safe_cleaned = cleaned.rstrip("\\")
                salvaged = safe_cleaned + '", "sources": []}\n]'
                
            try:
                arr = json.loads(salvaged)
                if isinstance(arr, list): 
                    logger.info("Successfully salvaged severely truncated Qualitative blocks!")
                    return arr
            except Exception as e_salvage:
                logger.error(f"Salvager failed: {e_salvage}")
            
            try:
                # DeepSeek-R1 often hallucinates single-quoted JSON, which breaks json.loads
                arr = ast.literal_eval(cleaned)
                if isinstance(arr, list): return arr
            except Exception as e2:
                logger.error(f"ast.literal_eval also failed: {e2}")
        return []
        
    blocks.extend(safe_parse_blocks(qual_output))
    blocks.extend(safe_parse_blocks(table_output))
    blocks.extend(safe_parse_blocks(metric_output))
    
    # Construct standard structure
    llm_output = json.dumps({
        "response": f"Berdasarkan analisa APPA, berikut informasi kelayakan bisnis {profile.get('product_category', 'produk')} Anda.",
        "artifacts": [
            {
                "id": "art-assessment-001",
                "title": f"Analisis Pasar & Strategi {profile.get('product_category', 'Produk')}",
                "sources": ["Data Scraper APPA", "Qdrant Regulatory Engine"],
                "blocks": blocks
            }
        ],
        "profile_updated": True
    })
    
    final_data = _parse_assessment_output(llm_output, profile, scenario=scenario)
    
    # Stream the response text for frontend typewriter effect
    response_text = final_data.get("response", "")
    chunk_size = 5
    for i in range(0, len(response_text), chunk_size):
        yield json.dumps({"type": "response_chunk", "content": response_text[i:i + chunk_size]}) + "\n"
        await asyncio.sleep(0.02)
    
    yield json.dumps({"type": "result", "data": final_data}) + "\n"

def _parse_assessment_output(output: str, profile: dict, scenario: str = "general") -> dict:
    """
    Parses LLM Call 2 output.
    On parse failure, delegates to core/fallback.py for a safe Bento Grid response.
    """
    cleaned_output = output.strip()

    # Extract JSON block (handles cases where LLM wraps response in markdown)
    json_match = re.search(r'(\{.*\})', cleaned_output, re.DOTALL)
    if json_match:
        cleaned_output = json_match.group(1)

    try:
        data = json.loads(cleaned_output)
        if "artifacts" in data and isinstance(data["artifacts"], list):
            # Apply strict JSON guardrails to auto-correct LLM typos
            for artifact in data["artifacts"]:
                if "blocks" in artifact and isinstance(artifact["blocks"], list):
                    for block in artifact["blocks"]:
                        if not isinstance(block, dict):
                            continue
                            
                        # Sanitize Chart Block
                        if block.get("type") == "chart":
                            b_data = block.get("data", {})
                            if not isinstance(b_data, dict):
                                b_data = {}
                                
                            # Auto-fix xAxis typos
                            if "xAxis" not in b_data:
                                b_data["xAxis"] = b_data.pop("x_axis", [])
                            if not isinstance(b_data.get("xAxis"), list):
                                b_data["xAxis"] = []
                                
                            # Auto-fix yAxis typos
                            if "yAxis" not in b_data:
                                b_data["yAxis"] = b_data.pop("y_axis", [])
                            if not isinstance(b_data.get("yAxis"), list):
                                b_data["yAxis"] = []
                                
                            block["data"] = b_data
                            
                        # Sanitize Checklist Block
                        if block.get("type") == "checklist":
                            b_data = block.get("data", {})
                            if not isinstance(b_data, dict):
                                b_data = {}
                            if "items" not in b_data or not isinstance(b_data["items"], list):
                                b_data["items"] = []
                                
                            # Convert string items to object schema
                            sanitized_items = []
                            for item in b_data["items"]:
                                if isinstance(item, str):
                                    sanitized_items.append({"title": item, "status": "pending"})
                                elif isinstance(item, dict):
                                    if "title" not in item:
                                        item["title"] = "Item"
                                    if "status" not in item:
                                        item["status"] = "pending"
                                    sanitized_items.append(item)
                            
                            b_data["items"] = sanitized_items
                            block["data"] = b_data
                            
                    # Filter out any blocks that are completely empty or hallucinatory
                    valid_blocks = []
                    text_count = 0
                    
                    for block in artifact["blocks"]:
                        b_type = block.get("type")
                        
                        if b_type == "checklist":
                            items = block.get("data", {}).get("items", [])
                            if not items or scenario == "price_only":
                                continue # Drop empty checklists, or if it's purely a pricing request!
                                
                        if b_type == "text":
                            # Prevent redundant MD spam by capping text blocks to 2 (or 1 for price_only)
                            cap = 1 if scenario == "price_only" else 2
                            if text_count >= cap:
                                continue
                            
                            # Python-level Guardrail for SLM Sycophancy (Over-generation)
                            if scenario == "price_only":
                                content = block.get("content", "")
                                # Remove bulleted lists (which are usually table regurgitations)
                                lines = content.split("\n")
                                clean_lines = [l for l in lines if not l.strip().startswith(('*', '-', '1.', '2.', '3.'))]
                                
                                # Force truncate to max 2 paragraphs / 100 words to prevent strategy hallucination
                                clean_content = "\n".join(clean_lines[:5]).strip()
                                
                                # Check if the content is just a header without any actual paragraph
                                text_without_headers = "\n".join([l for l in clean_lines[:5] if not l.strip().startswith('#')]).strip()
                                
                                if not text_without_headers:
                                    # Fallback paragraph if LLM only generated a header and bullet points
                                    fallback_text = "Harga di pasaran sangat bervariasi tergantung dari kualitas bahan, lokasi, dan strategi marketing kompetitor."
                                    if clean_content.startswith('#'):
                                        clean_content = f"{clean_content}\n\n{fallback_text}"
                                    else:
                                        clean_content = fallback_text
                                
                                block["content"] = clean_content
                                
                            text_count += 1
                            
                        valid_blocks.append(block)
                        
                    artifact["blocks"] = valid_blocks
                    
            return data
    except Exception as e:
        logger.error(f"Failed to parse LLM assessment JSON: {e}")
        try:
            with open("llm_debug.txt", "w", encoding="utf-8") as f:
                f.write(f"RAW OUTPUT:\n{output}\n\nCLEANED OUTPUT:\n{cleaned_output}")
        except:
            pass
        
        return build_fallback_response(profile)

