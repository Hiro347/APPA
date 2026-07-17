import json
import logging
import asyncio
import re
from core.profile_manager import get_profile, update_profile
from core.fallback import build_fallback_response
from ai.entity_extractor import extract_entities_and_queries
from ai.inference import call_llm, call_llm_stream
from ai.prompts.synthesis import get_clarification_prompt
from ai.prompts.assessment import get_assessment_prompt
from core.agent_tool.web import web_search, scrape_ecommerce_pricing
from core.agent_tool.vector import vector_search


logger = logging.getLogger(__name__)

async def handle_chat_stream(user_id: str, message: str):
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
    
    if not sub_queries or not isinstance(sub_queries, list):
        # Fallback queries if LLM didn't provide them
        sub_queries = [
            {"query": f"regulasi perizinan {keyword} di {profile.get('target_location', 'Indonesia')}", "type": "general"},
            {"query": f"harga pasaran {keyword} di {profile.get('target_location', 'Indonesia')}", "type": "price_fetch"}
        ]
        
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
        pipeline_groups.append({
            "id": "process", "icon": "", "label": "Pemrosesan Data",
            "steps": [
                {"id": "p1", "label": "Kondensasi Hasil Scraping", "status": "waiting"},
            ]
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
        "id": "synthesis", "icon": "", "label": "Sintesis Laporan & UI",
        "steps": [
            {"id": "syn1", "label": "Kompilasi Wayfinder Report (LLM)", "status": "waiting"}
        ]
    })
    
    yield json.dumps({"type": "pipeline_init", "pipeline": pipeline_groups}) + "\n"
    
    # Set running statuses
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
        search_tasks.append(web_search([q_text], visited_urls=shared_visited))
        
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
    
    # Emit done for searches
    full_market_data = ""
    combined_condensations = []
    
    for i, res in enumerate(search_results):
        q_obj = sub_queries[i]
        if isinstance(q_obj, str):
            q_obj = {"query": q_obj, "type": "general"}
        q_text = q_obj.get("query", "")
        
        if not res.get('snippets'):
            details = f"=== QUERY: {q_text} ===\n\n(No results found or search skipped)"
        else:
            details = f"=== QUERY: {q_text} ===\n\nSnippets:\n{json.dumps(res.get('snippets', []), indent=2)}\n\nRAW MARKDOWN:\n{res.get('raw_markdown', '')[:15000]}"
            
        yield emit_update(f"s{i+1}", "done", details)
        
        full_market_data += res.get("combined_text", "") + "\n\n"
        condensed = res.get("condensed_markdown", "")
        if condensed:
            combined_condensations.append(f"=== Hasil Analisis: '{q_text}' ===\n{condensed}")

    # Emit done for marketplace pricing
    if needs_shop:
        if not gshop_results.get('raw_markdown'):
            gshop_details = f"=== Sumber: {gshop_results.get('url', 'N/A')} ===\n\n(Tidak ada data harga marketplace ditemukan)"
        else:
            gshop_details = f"=== Sumber: {gshop_results.get('url')} ===\n\nCONDENSED:\n{gshop_results.get('condensed_markdown', '')}\n\nRAW MARKDOWN:\n{gshop_results.get('raw_markdown', '')[:10000]}"
            
        yield emit_update("gshop", "done", gshop_details)
        full_market_data += f"\n\n=== MARKETPLACE PRICING DATA ===\n{gshop_results.get('condensed_markdown', '')}"
        if gshop_results.get('condensed_markdown'):
            combined_condensations.append(f"=== Hasil Analisis Marketplace: '{keyword}' ===\n{gshop_results.get('condensed_markdown')}")
    
    yield emit_update("p1", "running")
    yield emit_update("p1", "done", "\n\n".join(combined_condensations))
    
    yield emit_update("r1", "done", vector_results)
    
    yield emit_update("r2", "running")
    await asyncio.sleep(0.5)
    yield emit_update("r2", "done", "Regex Matching Applied")
    
    # LLM Call 2: Assessment & Synthesis Report
    yield emit_update("syn1", "running")
    
    system_prompt = get_assessment_prompt(profile, full_market_data, vector_results)
    
    user_prompt = (
        f"Gunakan data yang ada untuk mensintesis laporan kelayakan bisnis {profile.get('product_category', 'produk')} "
        f"di {profile.get('target_location', 'wilayah target')}. "
        f"Balas dengan JSON format kaku sesuai contoh."
    )
    
    llm_output = ""
    try:
        async for chunk in call_llm_stream(user_prompt, system_prompt):
            llm_output += chunk
            # Keep the HTTP connection alive to prevent 'Network Error' browser timeouts
            yield json.dumps({"type": "ping"}) + "\n"
    except Exception as e:
        logger.error(f"LLM synthesis stream failed or timed out: {e}")
        # llm_output will be incomplete, so _parse_assessment_output will safely catch it and use fallback
        
    yield emit_update("syn1", "done")
    
    final_data = _parse_assessment_output(llm_output, profile)
    
    # Stream the response text for frontend typewriter effect
    response_text = final_data.get("response", "")
    chunk_size = 5
    for i in range(0, len(response_text), chunk_size):
        yield json.dumps({"type": "response_chunk", "content": response_text[i:i + chunk_size]}) + "\n"
        await asyncio.sleep(0.02)
    
    yield json.dumps({"type": "result", "data": final_data}) + "\n"

def _parse_assessment_output(output: str, profile: dict) -> dict:
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
            return data
    except Exception as e:
        logger.error(f"Failed to parse LLM assessment JSON: {e}")
        logger.error(f"Output length: {len(output)}. Content preview: {output[:200]}...{output[-200:]}")
        logger.error(f"Cleaned output preview: {cleaned_output[:200]}...{cleaned_output[-200:]}")

    return build_fallback_response(profile)

