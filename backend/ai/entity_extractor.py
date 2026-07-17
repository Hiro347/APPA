import json
import re
import logging
from ai.inference import call_llm
from ai.prompts.decomposition import get_decomposition_prompt

logger = logging.getLogger(__name__)

def extract_entities_and_queries(message: str, profile: dict) -> dict:
    """
    Calls the LLM with the decomposition system prompt to extract entities,
    determine routing (clarification vs research), and generate search queries.
    """
    system_prompt = get_decomposition_prompt(profile)
    
    # User message combined with instruction to return strictly JSON
    user_prompt = (
        f"Pesan Pengguna: \"{message}\"\n\n"
        f"Kembalikan data ekstraksi dalam format JSON kaku yang valid seperti contoh."
    )
    
    llm_output = call_llm(user_prompt, system_prompt=system_prompt)
    
    return _parse_decomposition_output(llm_output, message)

def _parse_decomposition_output(output: str, original_message: str) -> dict:
    """
    Safely parse the LLM's JSON output for routing, queries, and entities.
    If parsing fails, returns a robust fallback dictionary.
    """
    cleaned_output = output.strip()
    
    # Try to find a JSON block if the LLM included markdown wrapping
    json_match = re.search(r'(\{.*\})', cleaned_output, re.DOTALL)
    if json_match:
        cleaned_output = json_match.group(1)
        
    try:
        data = json.loads(cleaned_output)
        
        # Ensure required keys exist
        if "route" not in data:
            data["route"] = "research"
        if "extracted_entities" not in data:
            data["extracted_entities"] = {}
        if "sub_queries" not in data:
            data["sub_queries"] = []
            
        return data
    except Exception as e:
        logger.warning(f"Failed to parse LLM decomposition JSON: {e}. Output was: {output}")
        
    # Python-based Regex Fallback Parser (Robustness Shield)
    return _generate_fallback_data(original_message)

def _generate_fallback_data(message: str) -> dict:
    """
    Fallback deterministic parser if the LLM fails to output valid JSON.
    """
    message_lower = message.lower()
    
    # Basic route selection
    is_clarification = len(message.split()) < 4 or any(w in message_lower for w in ["halo", "hi", "pagi", "siang", "sore", "malam", "test"])
    
    # Product category extraction
    product = None
    if "keripik" in message_lower:
        product = "Keripik Singkong"
    elif "bakso" in message_lower:
        product = "Bakso Sapi Beku"
    elif "kopi" in message_lower:
        product = "Kopi Bubuk"
        
    # Location extraction
    location = None
    if "bandung" in message_lower:
        location = "Bandung"
    elif "surabaya" in message_lower:
        location = "Surabaya"
    elif "jakarta" in message_lower:
        location = "Jakarta"
        
    # Capital extraction
    capital = None
    import re
    numbers = re.findall(r'\b\d+(?:\.\d+)?\s*(?:juta|ribu|jt)?\b', message_lower)
    if numbers:
        val_str = "".join(numbers[0].split())
        if "juta" in val_str or "jt" in val_str:
            capital = int(float(re.search(r'\d+', val_str).group()) * 1000000)
        elif "ribu" in val_str:
            capital = int(float(re.search(r'\d+', val_str).group()) * 1000)
            
    # Business type categorization
    biz_type = None
    if product:
        if "bakso" in product.lower() or "basah" in message_lower or "beku" in message_lower:
            biz_type = "F&B Pangan Olahan Basah"
        else:
            biz_type = "F&B Pangan Olahan Kering"

    return {
        "route": "clarification" if is_clarification else "research",
        "extracted_entities": {
            "business_type": biz_type,
            "product_category": product,
            "target_location": location,
            "capital": capital,
            "hpp": None,
            "compliance_status": []
        },
        "sub_queries": [
            f"harga menu {product if product else 'camilan'} gofood",
            f"daftar toko kompetitor {product if product else 'makanan'} di {location if location else 'pasar'}"
        ] if not is_clarification else []
    }
