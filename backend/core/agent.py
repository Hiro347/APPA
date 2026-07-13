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
from core.tool_executor import web_search, vector_search

logger = logging.getLogger(__name__)

async def handle_chat(user_id: str, message: str) -> dict:
    """
    Core Agent Orchestrator implementing the JSON Railway Pattern.
    """
    logger.info(f"Received message from user '{user_id}': {message}")
    
    # 1. Fetch current user profile from SQLite
    profile = get_profile(user_id)
    
    # 2. LLM Call 1: Entity Extraction & Routing & Query Generation
    try:
        # Running synchronous LLM call inside threadpool to keep it non-blocking
        loop = asyncio.get_event_loop()
        call1_result = await loop.run_in_executor(
            None, extract_entities_and_queries, message, profile
        )
    except Exception as e:
        logger.error(f"Error during LLM Call 1 (decomposition): {e}")
        call1_result = {
            "route": "clarification",
            "extracted_entities": {},
            "sub_queries": []
        }
        
    route = call1_result.get("route", "clarification")
    extracted_entities = call1_result.get("extracted_entities", {})
    sub_queries = call1_result.get("sub_queries", [])
    
    # 3. Update SQLite profile implicitly before synthesis
    if extracted_entities:
        profile = update_profile(user_id, extracted_entities)
        
    # 4. ROUTE A: Clarification (Chit-chat / Greeting / Incomplete details)
    if route == "clarification":
        logger.info(f"Routing user '{user_id}' to Clarification Route.")
        system_prompt = get_clarification_prompt(profile)
        
        loop = asyncio.get_event_loop()
        chat_response = await loop.run_in_executor(
            None, call_llm, message, system_prompt
        )
        
        # Package into standard Bento Grid payload (no artifacts for clarification)
        return {
            "response": chat_response,
            "artifacts": [],
            "profile_updated": True
        }
        
    # 5. ROUTE B: Deep Research (Full Market Research + Regulations)
    logger.info(f"Routing user '{user_id}' to Deep Research Route with queries: {sub_queries}")
    
    # Run parallel RAG and Web Search to keep response times fast (< 100% sync timeout)
    search_task = web_search(sub_queries)
    vector_task = vector_search(sub_queries)
    
    search_results, vector_results = await asyncio.gather(search_task, vector_task)
    
    # LLM Call 2: Assessment & Synthesis Report
    system_prompt = get_assessment_prompt(profile, search_results, vector_results)
    
    user_prompt = (
        f"Gunakan data yang ada untuk mensintesis laporan kelayakan bisnis {profile.get('product_category', 'produk')} "
        f"di {profile.get('target_location', 'wilayah target')}. "
        f"Balas dengan JSON format kaku sesuai contoh."
    )
    
    loop = asyncio.get_event_loop()
    llm_output = await loop.run_in_executor(
        None, call_llm, user_prompt, system_prompt
    )
    
    return _parse_assessment_output(llm_output, profile)

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

