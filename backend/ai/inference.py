import json
import logging
from huggingface_hub import InferenceClient
from config import settings

logger = logging.getLogger(__name__)

# Initialize Hugging Face client
# If HF_API_TOKEN is empty, we will run in mock mode for local testing
client = None
if settings.HF_API_TOKEN:
    try:
        client = InferenceClient(model=settings.HF_MODEL_ID, token=settings.HF_API_TOKEN)
    except Exception as e:
        logger.error(f"Failed to initialize HuggingFace InferenceClient: {e}")
        client = None

def call_llm(prompt: str, system_prompt: str = "") -> str:
    """
    Call the LLM using HuggingFace Inference API.
    If no token is supplied or the API call fails, falls back to a smart mock response.
    """
    if client:
        try:
            # Combine system prompt and user prompt
            full_prompt = ""
            if system_prompt:
                full_prompt += f"<|system|>\n{system_prompt}\n"
            full_prompt += f"<|user|>\n{prompt}\n<|assistant|>\n"
            
            response = client.text_generation(
                prompt=full_prompt,
                max_new_tokens=1024,
                temperature=0.3,
                repetition_penalty=1.1
            )
            return response.strip()
        except Exception as e:
            logger.warning(f"HuggingFace API call failed: {e}. Falling back to Mock LLM.")
            
    # Mock LLM fallback for local development & demonstration
    return _mock_llm_response(prompt, system_prompt)

def _mock_llm_response(prompt: str, system_prompt: str) -> str:
    """
    Generate mock responses that mimic our model's behaviour for testing.
    """
    prompt_lower = prompt.lower()
    
    # 1. Check if this is LLM Call 1 (Entity extraction / Decomposition)
    if "extract" in system_prompt.lower() or "decomposition" in system_prompt.lower():
        # Example output for Call 1: JSON containing route, sub_queries, and extracted entities
        # Let's extract some basic entities from prompt to make mock smart
        product = "Keripik Singkong"
        location = "Surabaya"
        capital = 5000000
        
        if "bakso" in prompt_lower:
            product = "Bakso Sapi Beku"
        elif "kopi" in prompt_lower:
            product = "Kopi Bubuk"
            
        if "bandung" in prompt_lower:
            location = "Bandung"
        elif "jakarta" in prompt_lower:
            location = "Jakarta"
            
        # Check for numbers representing capital
        import re
        numbers = re.findall(r'\b\d+(?:\.\d+)?\s*(?:juta|ribu|ratus|jt)?\b', prompt_lower)
        if numbers:
            # simple mock parsing
            val_str = "".join(numbers[0].split())
            if "juta" in val_str or "jt" in val_str:
                capital = int(float(re.search(r'\d+', val_str).group()) * 1000000)
            elif "ribu" in val_str:
                capital = int(float(re.search(r'\d+', val_str).group()) * 1000)
                
        # Define route (clarification vs research)
        # If user prompt is very short or greeting, route is clarification
        is_clarification = len(prompt.split()) < 4 or any(w in prompt_lower for w in ["halo", "hi", "pagi", "siang", "sore", "malam", "test"])
        
        result = {
            "route": "clarification" if is_clarification else "research",
            "extracted_entities": {
                "business_type": "F&B Pangan Olahan Kering" if "keripik" in product.lower() or "kopi" in product.lower() else "F&B Pangan Olahan Basah",
                "product_category": product,
                "target_location": location,
                "capital": capital,
                "hpp": 5000,
                "compliance_status": []
            },
            "sub_queries": [
                f"harga {product} di {location}",
                f"kompetitor {product} terdekat di {location}"
            ]
        }
        return json.dumps(result)
        
    # 2. Check if this is LLM Call 2 (Assessment / Synthesis Report)
    elif "assessment" in system_prompt.lower() or "synthesis" in system_prompt.lower():
        # Example output for Call 2: Final synthesis
        product = "Produk"
        location = "Indonesia"
        if "bakso" in prompt_lower:
            product = "Bakso Sapi Beku"
        elif "keripik" in prompt_lower:
            product = "Keripik Singkong"
        elif "kopi" in prompt_lower:
            product = "Kopi Bubuk"
            
        # Extracted location
        if "bandung" in prompt_lower:
            location = "Bandung"
        elif "surabaya" in prompt_lower:
            location = "Surabaya"
        elif "jakarta" in prompt_lower:
            location = "Jakarta"
            
        # Determine if F&B Basah (BPOM) or Kering (SPP-IRT)
        is_basah = "bakso" in product.lower() or "basah" in prompt_lower or "beku" in prompt_lower
        
        if is_basah:
            compliance_desc = (
                "**Status Regulasi (F&B Pangan Olahan Basah - Risiko Menengah/Tinggi):**\n"
                "1. **NIB (Nomor Induk Berusaha):** Wajib dimiliki (Bebas Biaya di oss.go.id).\n"
                "2. **Izin Edar BPOM MD:** Wajib diurus karena produk Anda merupakan pangan olahan beku/basah. Biaya UMK Rp 100.000 - Rp 300.000 via e-reg.pom.go.id. Membutuhkan audit sarana.\n"
                "3. **Sertifikasi Halal Reguler:** Wajib dipenuhi sebelum tenggat 17 Oktober 2026. Biaya UMK berbayar Rp 300.000 - Rp 650.000 via SIHALAL."
            )
            checklist_items = [
                {"title": "NIB", "status": "wajib"},
                {"title": "Izin Edar BPOM MD", "status": "wajib"},
                {"title": "Sertifikasi Halal Reguler", "status": "wajib"}
            ]
        else:
            compliance_desc = (
                "**Status Regulasi (F&B Pangan Olahan Kering - Risiko Rendah):**\n"
                "1. **NIB (Nomor Induk Berusaha):** Wajib dimiliki (Bebas Biaya di oss.go.id).\n"
                "2. **SPP-IRT:** Wajib diurus secara online gratis di sppirt.pom.go.id. Terbit instan.\n"
                "3. **Sertifikasi Halal Self-Declare:** Wajib dipenuhi sebelum tenggat 17 Oktober 2026. Gratis via Program SEHATI di akun SIHALAL."
            )
            checklist_items = [
                {"title": "NIB", "status": "wajib"},
                {"title": "SPP-IRT", "status": "wajib"},
                {"title": "Sertifikasi Halal Self-Declare", "status": "wajib"}
            ]
            
        result_content = f"""### Laporan Analisa Pasar Pintar & Akurat: {product} di {location}

1. **Segmentasi Demografi & Psikografi:**
   * **Target Utama:** Keluarga muda, mahasiswa, dan pekerja kantoran yang menyukai kepraktisan dan makanan ringan/cepat saji di {location}.
   * **Perilaku Belanja:** Cenderung membeli secara online (e-commerce/WhatsApp) untuk stok mingguan, atau membeli langsung di warung kelontong terdekat untuk konsumsi instan.

2. **Analisis Hambatan Masuk Pasar:**
   * **Kompetitor:** Tingkat kompetisi menengah. Terdapat beberapa pemain lokal yang sudah aktif di {location}.
   * **Hambatan Utama:** Konsistensi rasa, ketahanan produk tanpa pengawet kimia, dan pemenuhan izin legalitas agar produk dapat masuk ke ritel modern.

3. **Rekomendasi Harga Jual (Pricing):**
   * **Rata-rata Pasar:** Rp 12.000 - Rp 15.000 per kemasan.
   * **Rekomendasi Harga Anda:** Rp 10.000 - Rp 12.000 per kemasan (berdasarkan perkiraan HPP Rp 5.000 dengan margin keuntungan ~100%).

4. **Strategi Pemasaran Murah:**
   * Memasarkan melalui WhatsApp Group warga dan komunitas lokal di {location}.
   * Skema konsinyasi (titip jual) di warung kelontong sekitar atau kantin sekolah/kantor.
   * Memberikan sampel produk gratis kepada influencer lokal skala mikro untuk ulasan di media sosial.

5. {compliance_desc}
"""
        
        # Structure as Generative UI response
        response_json = {
            "components": [
                {
                    "ui_type": "text",
                    "content": result_content,
                    "sources": ["Analisis Data Internal APPA", "Google Search Real-time"]
                },
                {
                    "ui_type": "checklist",
                    "items": checklist_items,
                    "sources": ["data/regulatory_rules.json", "PP 28/2025"]
                },
                {
                    "ui_type": "pricing",
                    "hpp": 5000,
                    "market_avg": 13500,
                    "recommendation": 10000,
                    "sources": ["SerpApi Google Shopping", "Hasil Crawling Pasar"]
                }
            ],
            "profile_updated": True
        }
        return json.dumps(response_json)
        
    # 3. Default fallback if prompt is chit-chat/clarification
    else:
        return "Halo! Saya APPA (Analisa Pasar Pintar & Akurat). Saya bisa membantu Anda melakukan riset pasar secara cepat dan memandu perizinan bisnis Anda. Ingin jualan apa dan di kota mana hari ini?"
