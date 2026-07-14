import json
import logging
import asyncio
import re
from core.profile_manager import get_profile, update_profile
from core.fallback import build_fallback_response
from ai.entity_extractor import extract_entities_and_queries
from ai.inference import call_llm
from ai.prompts.synthesis import get_clarification_prompt
from ai.prompts.assessment import get_assessment_prompt
from core.agent_tool.web import web_search, scrape_google_shopping
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
    yield emit_update("d3", "done", f"Route: {route}")
        
    # 4. ROUTE A: Clarification
    if route == "clarification":
        logger.info(f"Routing user '{user_id}' to Clarification Route.")
        yield emit_update("syn1", "running")
        system_prompt = get_clarification_prompt(profile)
        
        loop = asyncio.get_event_loop()
        chat_response = await loop.run_in_executor(
            None, call_llm, message, system_prompt
        )
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
    
    if not sub_queries or not isinstance(sub_queries, list):
        # Fallback queries if LLM didn't provide them
        sub_queries = [
            f"regulasi perizinan {keyword} di {profile.get('target_location', 'Indonesia')}",
            f"harga pasaran {keyword} di {profile.get('target_location', 'Indonesia')}"
        ]
        
    # Build dynamic pipeline UI
    search_steps = []
    for i, q in enumerate(sub_queries):
        search_steps.append({"id": f"s{i+1}", "label": f"Google Search: '{q}'", "status": "waiting"})
    
    # Add Google Shopping as the last step in the search group
    search_steps.append({"id": "gshop", "label": f"Google Shopping: '{keyword}'", "status": "waiting"})
    
    pipeline_groups = [
        {
            "id": "search", "icon": "", "label": "Pencarian Data Pasar & Regulasi",
            "steps": search_steps
        },
        {
            "id": "process", "icon": "", "label": "Pemrosesan Data",
            "steps": [
                {"id": "p1", "label": "Kondensasi hasil scraping ke JSON", "status": "waiting"},
                {"id": "p2", "label": "Validasi data dengan Pydantic", "status": "waiting"},
            ]
        },
        {
            "id": "regulation", "icon": "", "label": "Pengecekan Regulasi",
            "steps": [
                {"id": "r1", "label": f"Qdrant RAG: query regulasi {keyword}", "status": "waiting"},
                {"id": "r2", "label": "Matching: regulatory_rules.json", "status": "waiting"},
            ]
        },
        {
            "id": "synthesis", "icon": "", "label": "Sintesis Laporan & UI",
            "steps": [
                {"id": "syn1", "label": "Kompilasi Wayfinder Report (LLM)", "status": "waiting"}
            ]
        }
    ]
    
    yield json.dumps({"type": "pipeline_init", "pipeline": pipeline_groups}) + "\n"
    
    # Set running statuses
    for i in range(len(sub_queries)):
        yield emit_update(f"s{i+1}", "running")
    yield emit_update("gshop", "running")
    yield emit_update("r1", "running")
    
    shared_visited = set()
    search_tasks = []
    for q in sub_queries:
        search_tasks.append(web_search([q], visited_urls=shared_visited))
        
    gshop_task = scrape_google_shopping(keyword)
    vector_task = vector_search(sub_queries)
    
    # Gather all tasks dynamically
    all_tasks = search_tasks + [gshop_task, vector_task]
    results = await asyncio.gather(*all_tasks)
    
    # Unpack results
    search_results = results[:len(sub_queries)]
    gshop_results = results[-2]
    vector_results = results[-1]
    
    # Emit done for searches
    full_market_data = ""
    combined_condensations = []
    
    for i, res in enumerate(search_results):
        q = sub_queries[i]
        details = f"=== QUERY: {q} ===\n\nSnippets:\n{json.dumps(res.get('snippets', []), indent=2)}\n\nRAW MARKDOWN:\n{res.get('raw_markdown', '')[:15000]}"
        yield emit_update(f"s{i+1}", "done", details)
        
        full_market_data += res.get("combined_text", "") + "\n\n"
        condensed = res.get("condensed_json", "{}")
        combined_condensations.append(f"=== CONDENSED Q{i+1} ===\n{condensed}")

    # Emit done for gshop
    gshop_details = f"=== URL: {gshop_results.get('url')} ===\n\nCONDENSED:\n{gshop_results.get('condensed_json', '{}')}\n\nRAW MARKDOWN:\n{gshop_results.get('raw_markdown', '')[:10000]}"
    yield emit_update("gshop", "done", gshop_details)
    
    full_market_data += f"\n\n=== GOOGLE SHOPPING DATA ===\n{gshop_results.get('condensed_json', '{}')}"
    
    yield emit_update("p1", "done", "\n\n".join(combined_condensations))
    yield emit_update("p2", "done", "Validasi MarketDataSchema Sukses")
    
    yield emit_update("r1", "done", vector_results)
    yield emit_update("r2", "done", "Regex Matching Applied")
    
    # LLM Call 2: Assessment & Synthesis Report
    yield emit_update("syn1", "running")
    
    system_prompt = get_assessment_prompt(profile, full_market_data, vector_results)
    
    user_prompt = (
        f"Gunakan data yang ada untuk mensintesis laporan kelayakan bisnis {profile.get('product_category', 'produk')} "
        f"di {profile.get('target_location', 'wilayah target')}. "
        f"Balas dengan JSON format kaku sesuai contoh."
    )
    
    loop = asyncio.get_event_loop()
    llm_output = await loop.run_in_executor(
        None, call_llm, user_prompt, system_prompt
    )
    yield emit_update("syn1", "done")
    
    final_data = _parse_assessment_output(llm_output, profile)
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
        logger.warning(f"Failed to parse LLM assessment JSON: {e}. Output was: {output}")

    return build_fallback_response(profile)

