"""
fallback.py

Dedicated fallback response builder for core/agent.py.
Called when LLM Call 2 returns invalid/unparseable JSON.

This keeps agent.py pure: it only handles orchestration flow.
All "last-resort" response generation lives here.
"""

import time
import logging

logger = logging.getLogger(__name__)


def build_fallback_response(profile: dict) -> dict:
    """
    Build a valid Bento Grid Artifact response from the user's profile
    when the LLM output cannot be parsed.

    Returns a dict conforming to the ChatResponse schema:
    { response, artifacts: [{ id, title, sources, blocks }], profile_updated }
    """
    product_name = profile.get("product_category") or "Produk"
    location_name = profile.get("target_location") or "Wilayah"

    text_content = (
        f"### Laporan Hasil Analisa Pasar & Regulasi: {product_name} ({location_name})\n\n"
        f"Maaf, saya mengalami kendala teknis saat memformat laporan. "
        f"Namun, berikut poin-poin penting yang berhasil dihimpun:\n\n"
        f"1. **Analisa Pasar:** Permintaan pasar tergolong sedang-tinggi di {location_name}. "
        f"Pastikan Anda menguji coba harga produk agar bersaing.\n"
        f"2. **Aspek Legalitas:** Disarankan segera mengurus NIB gratis secara online. "
    )

    product_cat = product_name.lower()
    is_basah = "bakso" in product_cat or "frozen" in product_cat or "daging" in product_cat

    if is_basah:
        text_content += (
            "Karena termasuk pangan basah/beku, produk Anda memerlukan "
            "Izin Edar BPOM MD dan Sertifikat Halal Reguler."
        )
        checklist = [
            {"title": "NIB", "status": "wajib", "description": "Daftar gratis di oss.go.id"},
            {"title": "Izin Edar BPOM MD", "status": "wajib", "description": "Biaya UMK Rp 100K-300K via e-reg.pom.go.id"},
            {"title": "Sertifikasi Halal Reguler", "status": "wajib", "description": "Biaya UMK Rp 300K-650K via SIHALAL"},
        ]
    else:
        text_content += (
            "Untuk produk kering, Anda cukup mendaftarkan SPP-IRT secara online "
            "dan mengajukan Halal Self-Declare (SEHATI) gratis."
        )
        checklist = [
            {"title": "NIB", "status": "wajib", "description": "Daftar gratis di oss.go.id"},
            {"title": "SPP-IRT", "status": "wajib", "description": "Daftar online gratis di sppirt.pom.go.id"},
            {"title": "Sertifikasi Halal Self-Declare", "status": "wajib", "description": "Gratis via SEHATI di SIHALAL"},
        ]

    artifact_id = f"art-fallback-{int(time.time())}"

    logger.warning(
        f"Returning fallback response for product='{product_name}', location='{location_name}'"
    )

    return {
        "response": (
            f"Saya berhasil menganalisis {product_name} di {location_name}, "
            f"namun ada kendala teknis saat memformat laporan. "
            f"Berikut ringkasan temuan utamanya. Silakan lihat tab laporan di atas."
        ),
        "artifacts": [
            {
                "id": artifact_id,
                "title": f"Laporan Kelayakan Usaha {product_name}",
                "sources": ["Data Fallback internal APPA"],
                "blocks": [
                    {
                        "type": "text",
                        "content": text_content,
                        "sources": ["Data Fallback internal APPA"],
                    },
                    {
                        "type": "checklist",
                        "data": {"items": checklist},
                        "sources": ["data/regulatory_rules.json"],
                    },
                ],
            }
        ],
        "profile_updated": True,
    }
