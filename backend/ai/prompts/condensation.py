import json
from pydantic import BaseModel, Field

class MarketDataSchema(BaseModel):
    kompetitor: list[str] = Field(description="Daftar nama kompetitor yang disebutkan dalam teks.")
    harga_rata_rata: int | None = Field(description="Harga rata-rata produk di pasar jika disebutkan, atau null.")
    tren_pasar: str = Field(description="Ringkasan tren pasar saat ini dari teks.")
    insight_kualitatif: list[str] = Field(description="Poin-poin strategi bisnis, kelemahan/kelebihan produk, sentimen pasar, atau fakta kualitatif berharga lainnya.")
    kutipan_krusial: list[str] = Field(description="Kutipan langsung (verbatim) dari teks asli yang mengandung data penting atau testimoni berharga.")

def get_condensation_prompt() -> str:
    """
    Returns the system prompt for condensing Markdown scraped data into a structured Pydantic JSON.
    """
    schema_str = json.dumps(MarketDataSchema.model_json_schema(), indent=2)
    
    return f"""Kamu adalah modul peringkas data riset pasar tingkat lanjut untuk sistem APPA (Analisa Pasar Pintar & Akurat).
Tugasmu adalah memproses artikel teks mentah hasil scraping web (Markdown) dan merangkum informasi esensialnya menjadi sebuah JSON yang kaku, mengikuti skema Pydantic.

PENTING:
- Ekstrak fakta keras seperti harga pasar dan nama kompetitor.
- JANGAN HILANGKAN detail kualitatif! Gunakan field `insight_kualitatif` untuk merangkum strategi pemasaran, varian rasa, keluhan konsumen, atau taktik bisnis yang dibahas.
- Kutip kalimat penting secara verbatim di `kutipan_krusial` jika itu memuat opini pasar atau data numerik krusial yang tidak masuk ke metrik lain.
- Jangan menambahkan informasi di luar teks yang diberikan (dilarang berhalusinasi).
- Pastikan output HANYA berupa JSON murni yang sesuai dengan skema di bawah ini.

Skema JSON Wajib:
{schema_str}
"""
