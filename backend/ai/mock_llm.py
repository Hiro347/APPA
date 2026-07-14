"""
mock_llm.py

Dedicated mock LLM module for local development and offline demo fallback.
This module is ONLY imported by inference.py when no HF_API_TOKEN is present
or when the HuggingFace API call fails.

DO NOT mix production logic into this file.
"""

import json
import re
import time
import logging
import asyncio

logger = logging.getLogger(__name__)


def mock_decomposition(prompt: str) -> str:
    """
    Simulate LLM Call 1: Entity extraction & routing.
    Returns a JSON string with route, extracted_entities, and sub_queries.
    """
    prompt_lower = prompt.lower()

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

    numbers = re.findall(r'\b\d+(?:\.\d+)?\s*(?:juta|ribu|ratus|jt)?\b', prompt_lower)
    if numbers:
        val_str = "".join(numbers[0].split())
        if "juta" in val_str or "jt" in val_str:
            capital = int(float(re.search(r'\d+', val_str).group()) * 1_000_000)
        elif "ribu" in val_str:
            capital = int(float(re.search(r'\d+', val_str).group()) * 1_000)

    is_clarification = len(prompt.split()) < 4 or any(
        w in prompt_lower for w in ["halo", "hi", "pagi", "siang", "sore", "malam", "test"]
    )

    result = {
        "route": "clarification" if is_clarification else "research",
        "extracted_entities": {
            "business_type": (
                "F&B Pangan Olahan Kering"
                if "keripik" in product.lower() or "kopi" in product.lower()
                else "F&B Pangan Olahan Basah"
            ),
            "product_category": product,
            "target_location": location,
            "capital": capital,
            "hpp": 5000,
            "compliance_status": [],
        },
        "sub_queries": [
            f"harga {product} di {location}",
            f"kompetitor {product} terdekat di {location}",
        ],
    }
    return json.dumps(result)


def mock_assessment(prompt: str) -> str:
    """
    Simulate LLM Call 2: Full market & regulatory assessment.
    Returns a JSON string conforming to the Bento Grid Artifact schema.
    """
    prompt_lower = prompt.lower()

    product = "Produk"
    location = "Indonesia"

    if "bakso" in prompt_lower:
        product = "Bakso Sapi Beku"
    elif "keripik" in prompt_lower:
        product = "Keripik Singkong"
    elif "kopi" in prompt_lower:
        product = "Kopi Bubuk"

    if "bandung" in prompt_lower:
        location = "Bandung"
    elif "surabaya" in prompt_lower:
        location = "Surabaya"
    elif "jakarta" in prompt_lower:
        location = "Jakarta"

    is_basah = "bakso" in product.lower() or "basah" in prompt_lower or "beku" in prompt_lower

    if is_basah:
        compliance_desc = (
            "**Status Regulasi (F&B Pangan Olahan Basah - Risiko Menengah/Tinggi):**\n"
            "1. **NIB (Nomor Induk Berusaha):** Wajib dimiliki (Bebas Biaya di oss.go.id).\n"
            "2. **Izin Edar BPOM MD:** Wajib diurus karena produk Anda merupakan pangan olahan beku/basah. "
            "Biaya UMK Rp 100.000 - Rp 300.000 via e-reg.pom.go.id. Membutuhkan audit sarana.\n"
            "3. **Sertifikasi Halal Reguler:** Wajib dipenuhi sebelum tenggat 17 Oktober 2026. "
            "Biaya UMK berbayar Rp 300.000 - Rp 650.000 via SIHALAL."
        )
        checklist_items = [
            {"title": "NIB", "status": "wajib", "description": "Daftar gratis di oss.go.id"},
            {"title": "Izin Edar BPOM MD", "status": "wajib", "description": "Biaya UMK Rp 100K-300K via e-reg.pom.go.id"},
            {"title": "Sertifikasi Halal Reguler", "status": "wajib", "description": "Biaya UMK Rp 300K-650K via SIHALAL"},
        ]
    else:
        compliance_desc = (
            "**Status Regulasi (F&B Pangan Olahan Kering - Risiko Rendah):**\n"
            "1. **NIB (Nomor Induk Berusaha):** Wajib dimiliki (Bebas Biaya di oss.go.id).\n"
            "2. **SPP-IRT:** Wajib diurus secara online gratis di sppirt.pom.go.id. Terbit instan.\n"
            "3. **Sertifikasi Halal Self-Declare:** Wajib dipenuhi sebelum tenggat 17 Oktober 2026. "
            "Gratis via Program SEHATI di akun SIHALAL."
        )
        checklist_items = [
            {"title": "NIB", "status": "wajib", "description": "Daftar gratis di oss.go.id"},
            {"title": "SPP-IRT", "status": "wajib", "description": "Daftar online gratis di sppirt.pom.go.id"},
            {"title": "Sertifikasi Halal Self-Declare", "status": "wajib", "description": "Gratis via SEHATI di SIHALAL"},
        ]

    text_content = f"""### Laporan Analisa Pasar Pintar & Akurat: {product} di {location}

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

    artifact_id = f"art-mock-{int(time.time())}"

    result = {
        "response": (
            f"Berdasarkan analisa yang saya lakukan, saya telah menyusun laporan kelayakan usaha "
            f"{product} di {location} untuk Anda. Silakan lihat tab laporan di atas untuk detail visualnya."
        ),
        "artifacts": [
            {
                "id": artifact_id,
                "title": f"Laporan Kelayakan Usaha {product}",
                "sources": ["Analisis Data Internal APPA", "Google Search Real-time", "PP 28/2025"],
                "blocks": [
                    {
                        "type": "text",
                        "content": text_content,
                        "sources": ["Analisis Data Internal APPA", "Google Search Real-time"],
                    },
                    {
                        "type": "metric",
                        "data": {"hpp": 5000, "market_avg": 13500, "recommendation": 10000},
                        "sources": ["SerpApi Google Shopping", "Hasil Crawling Pasar"],
                    },
                    {
                        "type": "chart",
                        "data": {
                            "chartType": "line",
                            "xAxis": ["Produk 1", "Produk 2", "Produk 3", "Produk 4", "Produk 5", "Produk 6", "Produk 7", "Produk 8"],
                            "yAxis": [8900, 14000, 26500, 28950, 30000, 32400, 34500, 36950],
                            "label": "Distribusi Harga Kompetitor",
                        },
                        "sources": ["Google Shopping"],
                    },
                    {
                        "type": "checklist",
                        "data": {"items": checklist_items},
                        "sources": ["data/regulatory_rules.json", "PP 28/2025"],
                    },
                ],
            }
        ],
        "profile_updated": True,
    }
    return json.dumps(result)


def mock_clarification() -> str:
    """
    Simulate a generic clarification/chit-chat response.
    """
    return (
        "Halo! Saya APPA (Analisa Pasar Pintar & Akurat). "
        "Saya bisa membantu Anda melakukan riset pasar secara cepat dan memandu perizinan bisnis Anda. "
        "Ingin jualan apa dan di kota mana hari ini?"
    )


def mock_condensation(prompt: str) -> str:
    """
    Simulate LLM condensing raw markdown into MarketDataSchema JSON.
    Uses robust heuristic parsing to extract Top 5 Shopee and Top 5 Tokopedia products directly!
    """
    lines = [line.strip() for line in prompt.split('\n') if line.strip()]
    products = []
    
    for i, line in enumerate(lines):
        if line.startswith('Rp '):
            # Extract price integer
            price_match = re.search(r'Rp\s?(\d{1,3}(?:\.\d{3})*|\d+)', line)
            if not price_match: continue
            price = int(price_match.group(1).replace('.', ''))
            
            # Find title (look backwards up to 7 lines)
            title = "Unknown"
            for j in range(i-1, max(-1, i-7), -1):
                t = lines[j]
                # Filter out garbage lines
                if (not t.startswith('[') and 
                    not t.startswith('!') and 
                    not t.startswith('*') and 
                    not t.startswith('Rp') and 
                    not re.match(r'^[0-9,.]+(?:\([0-9]+\))?$', t) and
                    len(t) > 10 and 
                    'Jelajahi' not in t and 
                    'Lainnya' not in t and
                    t not in ['Lazada Indonesia', 'Shopee', 'Tokopedia', 'Blibli', 'shopee.co.id', 'tokopedia.com'] and
                    'Ctrl' not in t):
                    title = t
                    break
            
            # Find marketplace (look forwards up to 5 lines)
            market = "Unknown"
            for j in range(i+1, min(len(lines), i+5)):
                t = lines[j].strip()
                # Ignore image tags, rating lines, and prices
                if (not t.startswith('!') and 
                    not t.startswith('[') and 
                    not t.startswith('Rp') and 
                    len(t) > 3 and
                    not re.match(r'^[0-9,.]+(?:\([0-9]+\))?$', t)):
                    
                    if 'shopee' in t.lower(): market = 'Shopee'
                    elif 'tokopedia' in t.lower(): market = 'Tokopedia'
                    elif 'lazada' in t.lower(): market = 'Lazada'
                    elif 'blibli' in t.lower(): market = 'Blibli'
                    else: market = t.title()
                    
                    break
                    
            if market != "Unknown" and title != "Unknown":
                products.append({
                    "marketplace": market,
                    "title": title,
                    "price": price
                })
                
    # Filter top 10 overall (using a set to deduplicate exact same titles)
    seen_t = set()
    top_products = []
    for p in products:
        if p['title'].lower() not in seen_t:
            top_products.append(p)
            seen_t.add(p['title'].lower())
            if len(top_products) == 10: break
            
    if not top_products:
        return json.dumps({
            "ringkasan_artikel": "Berhasil mengekstrak informasi regulasi dan tren pasar dari artikel web.",
            "insight_utama": ["Kewajiban NIB", "Potensi pasar yang stabil", "Pentingnya strategi pemasaran digital"]
        }, indent=2)

    return json.dumps({
        "agregat": top_products
    }, indent=2)


def get_mock_response(prompt: str, system_prompt: str) -> str:
    """
    Entry point for mock LLM dispatch.
    Routes to the correct mock function based on system_prompt content.
    Only checks the first 300 characters to prevent false positives from search context.
    """
    sp_lower = system_prompt[:300].lower()

    if "ekstraksi" in sp_lower or "dekomposisi" in sp_lower or "orkestrator" in sp_lower:
        return mock_decomposition(prompt)

    if "kondensasi" in sp_lower or "peringkas data" in sp_lower or "condensation" in sp_lower or "analis data" in sp_lower:
        return mock_condensation(prompt)

    if "menyapa pengguna" in sp_lower or "chit-chat" in sp_lower:
        return mock_clarification()

    # Default to assessment for deep dive
    return mock_assessment(prompt)

async def get_mock_response_stream(prompt: str, system_prompt: str):
    """
    Streaming version of get_mock_response.
    Simulates token generation by yielding chunks of the string.
    """
    result = get_mock_response(prompt, system_prompt)
    
    # Chunk size of 3 characters, sleeping to simulate 20-30 tokens/sec
    chunk_size = 5
    for i in range(0, len(result), chunk_size):
        yield result[i:i + chunk_size]
        await asyncio.sleep(0.015)
