def get_price_condensation_prompt(query: str) -> str:
    """
    Highly specialized agent for extracting and sanitizing price points from web data.
    """
    return f"""Kamu adalah agen spesialis ekstraksi harga pasar untuk sistem APPA.
Tugasmu adalah memproses artikel teks (Markdown) dan mengekstrak data harga yang berkaitan dengan: '{query}'.

ATURAN EKSTRAKSI HARGA (STRICT ANTI-HALLUCINATION):
1. CRITICAL: DO NOT FABRICATE PRICES. If the text does not explicitly contain a clear numerical price (e.g. "Rp 20.000", "25rb"), YOU MUST RETURN {{"bento_hints": ["table"], "prices": []}}.
2. STRICT ACCURACY: Ekstrak HANYA data harga yang secara eksplisit tertulis dalam teks (memiliki nilai numerik yang jelas). Setiap angka `total_price` HARUS ADA dan persis terbaca di teks sumber.
3. DATA MATCHING: Pastikan setiap harga dipasangkan secara presisi dengan nama produk yang sesuai.
4. STRICT RELEVANCE: Ekstrak HANYA produk yang relevan langsung dengan kueri '{query}'. Abaikan item atau kategori yang tidak berkaitan.
5. NO MATHEMATICAL MODIFICATION: Ekstrak nilai total_price dan total_quantity apa adanya dari teks tanpa melakukan pembagian atau perkalian.
6. TRANSPARANSI KUANTITAS: `total_quantity` HANYA diisi jika teks menyebutkan jumlah unit fisik secara eksplisit (contoh: "isi 10", "6 pcs"). Jika kuantitas tidak disebutkan, set total_quantity ke null.
7. STORE NAME: Cantumkan Nama Toko (Store Name) HANYA jika secara eksplisit tertulis di teks sumber. Jika tidak ada, isi "Marketplace".
8. PRESERVE NUMERICAL VALUES: Ekstrak nilai numerik persis sesuai nilai nominalnya (contoh: "Rp 2.800" diekstrak sebagai 2800).
9. ZERO HALLUCINATION MANDATE: HANYA KEMBALIKAN DATA YANG BENAR-BENAR ADA. DILARANG MENAMBAH ATAU MELENGKAPI ARRAY DENGAN DATA BUATAN!
10. EXACT COPY-PASTE PRODUCT NAME: Salin tempel nama produk PERSIS seperti yang tertulis dalam teks sumber.
11. EXACT COPY-PASTE PRICE: Salin tempel angka harga PERSIS seperti yang tertulis di teks. Dilarang keras melakukan perhitungan matematika (perkalian/pembagian). Jika pengguna mencari "per lusin" tapi teks hanya mencantumkan "Rp 43.000 per pcs", maka kamu WAJIB mengekstrak 43000.
12. EXACT COPY-PASTE ORIGINAL TEXT: Untuk `original_price_text`, salin tempel kalimat asli dari teks yang memuat harga tersebut TANPA MENGUBAH SATU HURUF PUN.
13. MINIMUM DATA REQUIREMENT: Kamu WAJIB mengekstrak SEBANYAK MUNGKIN data harga yang valid dari seluruh teks. Targetkan MINIMAL 5 baris data (rows) yang valid. Jangan malas! Telusuri seluruh teks dari atas ke bawah!

FORMAT OUTPUT WAJIB (JSON ONLY):
HANYA hasilkan JSON valid sesuai struktur berikut tanpa pembungkus teks tambahan:
{{
  "bento_hints": ["table"],
  "prices": [
    {{
      "product_name": "string (Nama spesifik produk)",
      "total_price": "number (Harga total nominal, contoh: 20000)",
      "total_quantity": "number | null (Jumlah unit fisik, contoh: 6)",
      "original_price_text": "string (Teks harga asli dari artikel)",
      "store_name": "string (Nama toko atau sumber asli)"
    }}
  ]
}}
"""

def get_general_condensation_prompt(query: str) -> str:
    """
    Highly specialized agent for extracting qualitative strategies, competitor info, and tips.
    """
    return f"""Kamu adalah agen spesialis riset kualitatif (strategi, kompetitor, operasional) untuk sistem APPA.
Tugasmu adalah memproses artikel teks mentah hasil scraping web (Markdown) dan mengekstrak informasi esensial yang menjawab query: '{query}'.

ATURAN EKSTRAKSI KUALITATIF:
- PEMANGKASAN KEJAM: Rangkum dan ekstrak Maksimal 3 hingga 5 entri/fakta yang paling representatif saja.
- FOKUS PADA QUERY: Jika kueri membahas tentang "strategi", ekstrak strategi. Jika membahas "kompetitor", ekstrak nama dan kelebihan kompetitor. JANGAN mengekstrak resep masakan jika tidak diminta.
- PECAH INFORMASI: Wajib pecah informasi menjadi beberapa objek JSON. JANGAN menumpuk banyak fakta (seperti daftar 3 kompetitor) ke dalam satu objek. Jika ada 3 kompetitor, buat 3 objek terpisah!
- JANGAN BERHALUSINASI: Jangan menambahkan informasi di luar teks yang diberikan. Jika tidak ada informasi relevan, kembalikan JSON dengan array kosong.
- DILARANG MENJELASKAN PROSES: JANGAN PERNAH menyalin atau menjelaskan instruksi prompt ini di dalam outputmu.

FORMAT OUTPUT WAJIB (JSON ONLY):
Kamu HARUS merespon HANYA dengan JSON valid sesuai struktur berikut. JANGAN PERNAH menyertakan teks Markdown.
{{
  "bento_hints": ["text"],
  "findings": [
    {{
      "topic": "string (Judul Topik, misal: 'Kelebihan Kompetitor A')",
      "fact": "string (Fakta padat yang diekstrak)"
    }}
  ]
}}
"""

CONDENSER_AGENTS = {
    "price_fetch": get_price_condensation_prompt,
    "general": get_general_condensation_prompt,
    # Easily extensible in the future:
    # "legal_research": get_legal_condensation_prompt,
}
