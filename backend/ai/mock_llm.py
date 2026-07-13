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
                            "xAxis": ["Tokopedia", "Shopee", "Rekomendasi"],
                            "yAxis": [12000, 11500, 10000],
                            "label": "Analisis Komparasi Harga Jual",
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


def get_mock_response(prompt: str, system_prompt: str) -> str:
    """
    Entry point for mock LLM dispatch.
    Routes to the correct mock function based on system_prompt content.
    """
    sp_lower = system_prompt.lower()

    if "extract" in sp_lower or "decomposition" in sp_lower:
        return mock_decomposition(prompt)

    if "assessment" in sp_lower or "synthesis" in sp_lower:
        return mock_assessment(prompt)

    return mock_clarification()
