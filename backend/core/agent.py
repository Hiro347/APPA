import json
import logging
import asyncio
import re
from core.profile_manager import get_profile, update_profile
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
        
        # Package into standard Generative UI payload
        return {
            "components": [
                {
                    "ui_type": "text",
                    "content": chat_response,
                    "sources": []
                }
            ],
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
    Cleans and parses the LLM Call 2 output. 
    If parsing fails, generates a robust fallback Generative UI JSON.
    """
    cleaned_output = output.strip()
    
    # Find JSON blocks
    json_match = re.search(r'(\{.*\})', cleaned_output, re.DOTALL)
    if json_match:
        cleaned_output = json_match.group(1)
        
    try:
        data = json.loads(cleaned_output)
        if "components" in data and isinstance(data["components"], list):
            return data
    except Exception as e:
        logger.warning(f"Failed to parse LLM assessment JSON: {e}. Output was: {output}")
        
    # Fallback response formatting if LLM response is corrupted or plain text
    fallback_content = (
        f"### Laporan Hasil Analisa Pasar & Regulasi: {profile.get('product_category', 'Produk')} ({profile.get('target_location', 'Wilayah')})\n\n"
        f"Maaf, saya mengalami kendala teknis saat memformat laporan. Namun, berikut poin-poin penting yang berhasil dihimpun:\n\n"
        f"1. **Analisa Pasar:** Permintaan pasar tergolong sedang-tinggi di {profile.get('target_location')}. Pastikan Anda menguji coba harga produk agar bersaing.\n"
        f"2. **Aspek Legalitas:** Disarankan segera mengurus NIB gratis secara online. "
    )
    
    # Check if F&B Basah or Kering for generic fallback perizinan
    product_cat = profile.get('product_category', '').lower()
    is_basah = "bakso" in product_cat or "frozen" in product_cat or "daging" in product_cat
    
    if is_basah:
        fallback_content += "Karena termasuk pangan basah/beku, produk Anda memerlukan Izin Edar BPOM MD dan Sertifikat Halal Reguler."
        checklist = [
            {"title": "NIB", "status": "wajib"},
            {"title": "Izin Edar BPOM MD", "status": "wajib"},
            {"title": "Sertifikasi Halal Reguler", "status": "wajib"}
        ]
    else:
        fallback_content += "Untuk produk kering, Anda cukup mendaftarkan SPP-IRT secara online dan mengajukan Halal Self-Declare (SEHATI) gratis."
        checklist = [
            {"title": "NIB", "status": "wajib"},
            {"title": "SPP-IRT", "status": "wajib"},
            {"title": "Sertifikasi Halal Self-Declare", "status": "wajib"}
        ]
        
    return {
        "components": [
            {
                "ui_type": "text",
                "content": fallback_content,
                "sources": ["Data Fallback internal APPA"]
            },
            {
                "ui_type": "checklist",
                "items": checklist,
                "sources": ["data/regulatory_rules.json"]
            }
        ],
        "profile_updated": True
    }
