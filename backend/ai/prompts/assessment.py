def get_qualitative_synthesis_prompt(profile: dict, search_context: str, qdrant_context: str) -> str:
    return f"""Kamu adalah agen spesialis Analisis Pasar Kualitatif untuk sistem APPA.
Tugasmu adalah menyusun ringkasan kualitatif untuk UI berdasarkan data profil, hasil pencarian, dan regulasi.

Data Pengguna:
- Kategori Produk: {profile.get('product_category') or 'Belum ditentukan'}
- Lokasi Target: {profile.get('target_location') or 'Belum ditentukan'}
- Estimasi Modal: {profile.get('key_facts', {}).get('capital') or 'Belum ditentukan'}

Hasil Pencarian Web (Pasar & Kompetitor):
{search_context}

Hasil Database Vektor (Regulasi & Hukum):
{qdrant_context}

ATURAN UTAMA:
1. RINGKAS & FOKUS: Tulis ringkasan padat maksimal 3 kalimat yang secara khusus merangkum pola harga atau insight pasar utama dari data pencarian.
2. STABILITAS JSON: Gunakan standar JSON yang valid. Jika menyertakan kutipan teks dalam string JSON, gunakan escape slash (\\") atau tanda kutip tunggal (').
3. STRUKTUR SINGLE BLOCK: Buat tepat 1 block bermutasi type "text".

FORMAT OUTPUT WAJIB (JSON ONLY):
HANYA hasilkan Array JSON berikut tanpa teks tambahan:
[
  {{
    "type": "text",
    "content": "string (Ringkasan kualitatif padat maksimal 3 kalimat)",
    "sources": ["DuckDuckGo Web Search"]
  }}
]
"""

def get_table_synthesis_prompt(profile: dict, search_context: str) -> str:
    return f"""Kamu adalah agen spesialis Penyusun Tabel Harga & Kompetitor untuk sistem APPA.
Tugasmu adalah mengekstrak data dari teks pencarian dan menyusunnya menjadi blok tabel (table block) UI.

Lokasi Target: {profile.get('target_location') or 'Belum ditentukan'}

Hasil Pencarian Web:
{search_context}

ATURAN UTAMA:
1. DATA COMPLIANCE: HANYA tampilkan data produk dan harga yang benar-benar ada dalam teks pencarian.
2. EXCLUDE OUTLIERS: Abaikan data ekstrem atau tidak relevan yang berada jauh di luar rentang harga umum.
3. PRESERVE NUMERICAL STRING: Tuliskan string harga sesuai nominal tertera (contoh: "Rp 3.500").
4. STABILITAS JSON: Hasilkan JSON yang strictly valid.

FORMAT OUTPUT WAJIB (JSON ONLY):
HANYA hasilkan Array JSON berikut:
[
  {{
    "type": "table",
    "data": {{
      "headers": ["Nama Toko / Kompetitor", "Produk", "Harga", "Keterangan Tambahan"],
      "rows": [
        ["string", "string", "string", "string"]
      ]
    }},
    "sources": ["Data Scraping E-Commerce"]
  }}
]
"""

def get_metrics_synthesis_prompt(profile: dict, search_context: str) -> str:
    return f"""Kamu adalah agen spesialis Ekstraksi Metrik & Grafik untuk sistem APPA.
Tugasmu adalah menyusun estimasi metrik angka (HPP, rata-rata pasar, dan rekomendasi) berdasarkan data teks pencarian.

Lokasi Target: {profile.get('target_location') or 'Belum ditentukan'}

Hasil Pencarian Web:
{search_context}

ATURAN UTAMA:
1. ESTIMASI HARGA: Estimasi angka "hpp" (Harga Pokok Penjualan), "market_avg" (Rata-rata Harga Pasar), dan "recommendation" (Rekomendasi Harga) berdasarkan data pencarian.
2. EMPTY FALLBACK: Jika tidak ada data harga sama sekali dalam teks pencarian, kembalikan array JSON kosong `[]`.

FORMAT OUTPUT WAJIB (JSON ONLY):
HANYA hasilkan Array JSON berikut:
[
  {{
    "type": "metric",
    "data": {{ "hpp": 8000, "market_avg": 10000, "recommendation": 9000 }},
    "sources": ["Data Scraping E-Commerce"]
  }}
]
"""

