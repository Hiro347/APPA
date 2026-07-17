import json
import random
import os

# Define lists for generation variety
PRODUCTS_DRY = [
    {"name": "Keripik Pisang Cokelat", "kbli": "10794", "type": "F&B Pangan Olahan Kering"},
    {"name": "Kopi Bubuk Robusta", "kbli": "10761", "type": "F&B Pangan Olahan Kering"},
    {"name": "Kue Kering Nastar", "kbli": "10712", "type": "F&B Pangan Olahan Kering"},
    {"name": "Rengginang Singkong", "kbli": "10794", "type": "F&B Pangan Olahan Kering"},
    {"name": "Kripik Tempe Sagu", "kbli": "10794", "type": "F&B Pangan Olahan Kering"},
    {"name": "Sambal Bawang Botolan", "kbli": "10772", "type": "F&B Pangan Olahan Kering"},
    {"name": "Bumbu Dapur Tabur", "kbli": "10772", "type": "F&B Pangan Olahan Kering"},
    {"name": "Makaroni Pedas Daun Jeruk", "kbli": "10794", "type": "F&B Pangan Olahan Kering"}
]

PRODUCTS_WET = [
    {"name": "Bakso Sapi Beku (Frozen)", "kbli": "10130", "type": "F&B Pangan Olahan Basah"},
    {"name": "Yogurt Ketan Hitam", "kbli": "10520", "type": "F&B Pangan Olahan Basah"},
    {"name": "Sosis Ayam Homemade", "kbli": "10130", "type": "F&B Pangan Olahan Basah"},
    {"name": "Siomay Ikan Frozen", "kbli": "10293", "type": "F&B Pangan Olahan Basah"},
    {"name": "Dimsum Ayam Frozen", "kbli": "10799", "type": "F&B Pangan Olahan Basah"},
    {"name": "Sambal Cumi Asin Basah", "kbli": "10293", "type": "F&B Pangan Olahan Basah"},
    {"name": "Rendang Daging Kemasan Vakum", "kbli": "10130", "type": "F&B Pangan Olahan Basah"},
    {"name": "Nugget Ayam Wortel", "kbli": "10130", "type": "F&B Pangan Olahan Basah"}
]

PRODUCTS_READY = [
    {"name": "Kopi Susu Gula Aren Kupas", "kbli": "56303", "type": "F&B Pangan Siap Saji"},
    {"name": "Nasi Goreng Gila", "kbli": "56101", "type": "F&B Pangan Siap Saji"},
    {"name": "Roti Bakar Bandung", "kbli": "56101", "type": "F&B Pangan Siap Saji"},
    {"name": "Katering Harian Kantoran", "kbli": "56210", "type": "F&B Pangan Siap Saji"},
    {"name": "Martabak Manis", "kbli": "56101", "type": "F&B Pangan Siap Saji"},
    {"name": "Ayam Geprek Sambal Korek", "kbli": "56101", "type": "F&B Pangan Siap Saji"},
    {"name": "Kedai Jus Buah Segar", "kbli": "56303", "type": "F&B Pangan Siap Saji"},
    {"name": "Mie Ayam Bakso Urat", "kbli": "56101", "type": "F&B Pangan Siap Saji"}
]

LOCATIONS = [
    "Bandung", "Surabaya", "Jakarta Selatan", "Medan", "Makassar", 
    "Semarang", "Yogyakarta", "Malang", "Tangerang", "Bekasi",
    "Depok", "Bogor", "Solo", "Palembang", "Denpasar"
]

CAPITALS = [
    {"text": "1 juta", "val": 1000000},
    {"text": "2 juta", "val": 2000000},
    {"text": "3 jt", "val": 3000000},
    {"text": "5 juta rupiah", "val": 5000000},
    {"text": "10 juta", "val": 10000000},
    {"text": "15 jt", "val": 15000000},
    {"text": "20 juta rupiah", "val": 20000000},
    {"text": "500 ribu", "val": 500000}
]

# Query Decomposition (Call 1) templates
DECOMP_TEMPLATES = [
    "Halo, saya mau jualan {product} dengan modal {capital} di {location}. Tolong riset pasarnya.",
    "Jualan {product} di {location} modalnya cuma {capital}, kira-kira untung ga ya?",
    "sy pengen bikin bisnis {product} skala rumahan di daerah {location}, modal awal {capital}. apa aja izin yg diperluin?",
    "Bagaimana cara memulai usaha {product} modal {capital} untuk pemula di {location}?",
    "Saya berencana kulakan {product} lalu dijual di {location}. Modalnya {capital}. Tolong analisis harganya.",
    "Mau tanya, kalau buat usaha {product} di {location} modal {capital} itu prospeknya gimana dan izinnya apa?",
    "permisi kak, mau tanya skema konsinyasi {product} ke warung-warung di {location} dengan modal {capital}.",
    "Saya mau bikin usaha sampingan {product} modal {capital} di kota {location}. Bagaimana cara analisis kompetitornya?"
]

DECOMP_CLARIFICATION_TEMPLATES = [
    "Halo", "Hi", "Tes", "p", "pagi", "siang", "sore", "malam",
    "Saya mau jualan makanan kering",
    "Mau nanya soal perizinan",
    "Bagaimana cara riset pasar?",
    "Saya punya modal 5 juta tapi bingung mau jualan apa di {location}",
    "Halo asisten APPA, bantu saya dong.",
    "tes sistem",
    "Ada orang?"
]

def generate_decomposition_examples():
    examples = []
    
    # 1. Generate active research route examples
    for i in range(60):
        # Mix dry, wet, and ready
        cat = random.choice([PRODUCTS_DRY, PRODUCTS_WET, PRODUCTS_READY])
        prod = random.choice(cat)
        loc = random.choice(LOCATIONS)
        cap = random.choice(CAPITALS)
        
        user_msg = random.choice(DECOMP_TEMPLATES).format(
            product=prod["name"], 
            capital=cap["text"], 
            location=loc
        )
        
        # Current profile (often empty or partially filled)
        profile = {
            "business_type": None,
            "product_category": None,
            "target_location": None,
            "capital": None,
            "hpp": None,
            "compliance_status": []
        }
        
        system_prompt = f"""Kamu adalah modul dekomposisi kueri dan ekstraksi entitas untuk APPA (Analisa Pasar Pintar & Akurat), asisten AI bisnis untuk UMKM Indonesia.

Tugas utamanya adalah:
1. Menganalisis pesan pengguna.
2. Mengekstrak entitas bisnis baru untuk memperbarui profil pengguna secara dinamis.
3. Menentukan rute respon:
   - "clarification" jika pesan pengguna sangat singkat (misal: "Halo", "hi", "tes"), tidak jelas, atau berupa obrolan santai (*chit-chat*) yang membutuhkan klarifikasi informasi produk/wilayah sebelum riset bisa dimulai.
   - "research" jika pengguna memberikan informasi ide bisnis konkret yang layak dianalisis.
4. Membuat sub-kueri pencarian Google (*search queries*) yang spesifik untuk menarik tren harga dan kompetitor secara real-time.

Profil Pengguna Saat Ini (Gunakan sebagai memori sesi):
- Jenis Bisnis: Belum diketahui
- Kategori Produk: Belum diketahui
- Lokasi Target: Belum diketahui
- Fakta Lainnya: Kosong

Format Output Wajib:
Kamu harus membalas HANYA dengan satu blok JSON yang valid, tanpa teks penjelasan tambahan, tanpa tanda pembungkus markdown selain JSON itu sendiri."""

        json_out = {
            "route": "research",
            "extracted_entities": {
                "business_type": prod["type"],
                "product_category": prod["name"],
                "target_location": loc,
                "capital": cap["val"],
                "hpp": None,
                "compliance_status": []
            },
            "sub_queries": [
                f"harga {prod['name'].lower()} {loc.lower()} terbaru 2026",
                f"kompetitor {prod['name'].lower()} {loc.lower()}"
            ]
        }
        
        examples.append({
            "system": system_prompt,
            "user": f"Pesan Pengguna: \"{user_msg}\"\n\nKembalikan data ekstraksi dalam format JSON kaku yang valid seperti contoh.",
            "json_output": json.dumps(json_out, indent=2, ensure_ascii=False)
        })
        
    # 2. Generate clarification examples
    for i in range(20):
        loc = random.choice(LOCATIONS)
        user_msg = random.choice(DECOMP_CLARIFICATION_TEMPLATES).format(location=loc)
        
        system_prompt = f"""Kamu adalah modul dekomposisi kueri dan ekstraksi entitas untuk APPA (Analisa Pasar Pintar & Akurat), asisten AI bisnis untuk UMKM Indonesia.

Tugas utamanya adalah:
1. Menganalisis pesan pengguna.
2. Mengekstrak entitas bisnis baru untuk memperbarui profil pengguna secara dinamis.
3. Menentukan rute respon:
   - "clarification" jika pesan pengguna sangat singkat (misal: "Halo", "hi", "tes"), tidak jelas, atau berupa obrolan santai (*chit-chat*) yang membutuhkan klarifikasi informasi produk/wilayah sebelum riset bisa dimulai.
   - "research" jika pengguna memberikan informasi ide bisnis konkret yang layak dianalisis.
4. Membuat sub-kueri pencarian Google (*search queries*) yang spesifik untuk menarik tren harga dan kompetitor secara real-time.

Profil Pengguna Saat Ini (Gunakan sebagai memori sesi):
- Jenis Bisnis: Belum diketahui
- Kategori Produk: Belum diketahui
- Lokasi Target: Belum diketahui
- Fakta Lainnya: Kosong

Format Output Wajib:
Kamu harus membalas HANYA dengan satu blok JSON yang valid, tanpa teks penjelasan tambahan, tanpa tanda pembungkus markdown selain JSON itu sendiri."""

        # Extracted entities might capture location if mentioned, else empty
        extracted = {
            "business_type": None,
            "product_category": None,
            "target_location": loc if "jualan apa" in user_msg else None,
            "capital": 5000000 if "5 juta" in user_msg else None,
            "hpp": None,
            "compliance_status": []
        }
        
        json_out = {
            "route": "clarification",
            "extracted_entities": extracted,
            "sub_queries": []
        }
        
        examples.append({
            "system": system_prompt,
            "user": f"Pesan Pengguna: \"{user_msg}\"\n\nKembalikan data ekstraksi dalam format JSON kaku yang valid seperti contoh.",
            "json_output": json.dumps(json_out, indent=2, ensure_ascii=False)
        })
        
    return examples

# Report Synthesis (Call 2) Generation
def generate_synthesis_examples():
    examples = []
    
    # Generate 80 synthesis examples
    for i in range(80):
        # Mix dry, wet, ready
        cat_type = random.choice(["dry", "wet", "ready"])
        loc = random.choice(LOCATIONS)
        cap_val = random.choice([1000000, 2000000, 3000000, 5000000, 10000000, 15000000])
        
        if cat_type == "dry":
            prod = random.choice(PRODUCTS_DRY)
            checklist = [
                { "title": "NIB (Nomor Induk Berusaha)", "status": "wajib", "description": "Daftar gratis di oss.go.id" },
                { "title": "SPP-IRT", "status": "wajib", "description": "Daftar online di sppirt.pom.go.id" },
                { "title": "Sertifikasi Halal Self-Declare", "status": "wajib", "description": "Gratis via SEHATI di SIHALAL (tenggat 17 Oktober 2026)" }
            ]
            reg_context = f"Kategori: Olahan Kering Rumah Tangga. Izin wajib: NIB (OSS, gratis), SPP-IRT (BPOM/Dinkes, gratis online), Halal Self-Declare (SEHATI, gratis sebelum 17 Okt 2026)."
            price_hpp = int(cap_val * 0.002) if cap_val >= 2000000 else 4000
            price_market = int(price_hpp * 2.2)
            price_rec = int(price_hpp * 1.9)
            sources = ["regulatory_rules.json", "PP 28/2025", "BPOM Per 4/2024"]
        elif cat_type == "wet":
            prod = random.choice(PRODUCTS_WET)
            checklist = [
                { "title": "NIB (Nomor Induk Berusaha)", "status": "wajib", "description": "Daftar gratis di oss.go.id" },
                { "title": "Izin Edar BPOM MD", "status": "wajib", "description": "Pendaftaran e-reg.pom.go.id dengan status sarana PSB minimal B" },
                { "title": "Sertifikasi Halal Reguler", "status": "wajib", "description": "Berbayar via SIHALAL + audit LPH (tenggat 17 Oktober 2026)" }
            ]
            reg_context = f"Kategori: Olahan Basah/Frozen. Izin wajib: NIB, BPOM MD (e-reg.pom.go.id, audit sarana PSB, bayar PNBP UMK), Halal Reguler (BPJPH SIHALAL + audit LPH, berbayar)."
            price_hpp = int(cap_val * 0.005) if cap_val >= 2000000 else 8000
            price_market = int(price_hpp * 2.5)
            price_rec = int(price_hpp * 2.1)
            sources = ["regulatory_rules.json", "PP 28/2025", "PerBPOM 27/2017"]
        else: # ready-to-eat
            prod = random.choice(PRODUCTS_READY)
            checklist = [
                { "title": "NIB (Nomor Induk Berusaha)", "status": "wajib", "description": "Daftar gratis di oss.go.id" },
                { "title": "Sertifikat Laik Higiene Sanitasi (SLHS)", "status": "wajib", "description": "Pengajuan via PB UMKU di OSS, audit kesehatan lingkungan oleh Dinkes" },
                { "title": "Sertifikasi Halal (Self-Declare / Reguler)", "status": "wajib", "description": "Daftar di SIHALAL (tenggat 17 Oktober 2026)" }
            ]
            reg_context = f"Kategori: Pangan Siap Saji / Restoran / Kedai. Izin wajib: NIB, SLHS (Laik Higiene Sanitasi, Dinkes via OSS), Sertifikat Halal (SIHALAL, tenggat 17 Okt 2026)."
            price_hpp = int(cap_val * 0.004) if cap_val >= 2000000 else 6000
            price_market = int(price_hpp * 2.3)
            price_rec = int(price_hpp * 2.0)
            sources = ["regulatory_rules.json", "PP 28/2025", "Permenkes 14/2021"]
            
        profile = {
            "product_category": prod["name"],
            "target_location": loc,
            "key_facts": {
                "capital": cap_val
            }
        }
        
        search_context = f"""Hasil Pencarian Google Shopping untuk '{prod['name']} di {loc}':
1. Toko kompetitor lokal menjual {prod['name']} seharga Rp {price_market:,} per porsi/kemasan.
2. Rata-rata kompetitor mempromosikan produk lewat Instagram dan WhatsApp Group lingkungan perumahan.
3. Permintaan pasar lokal untuk produk F&B kuliner ini sedang tinggi, terutama di sore dan malam hari."""

        system_prompt = f"""Kamu adalah mesin analisis bisnis dan perizinan utama untuk APPA (Analisa Pasar Pintar & Akurat).
Tugasmu adalah menyusun laporan kelayakan bisnis terstruktur untuk UMKM berdasarkan data profil, hasil pencarian pasar real-time, dan regulasi hukum.

Data Pengguna:
- Kategori Produk: {prod['name']}
- Lokasi Target: {loc}
- Estimasi Modal: Rp {cap_val:,}

Hasil Pencarian Web (Pasar & Kompetitor):
{search_context}

Hasil Database Vektor (Regulasi & Hukum):
{reg_context}

Aturan Penulisan Laporan:
1. Gunakan bahasa Indonesia yang ramah, sopan, namun taktis dan mudah dipahami oleh pedagang kecil (hindari jargon akademis yang terlalu rumit, terjemahkan istilah hukum menjadi langkah aksi sederhana).
2. Laporan wajib memiliki 5 bagian terstruktur:
   - **Bagian 1: Segmentasi Demografi & Psikografi** (Siapa pembeli potensial di lokasi target).
   - **Bagian 2: Analisis Hambatan Masuk Pasar** (Tingkat persaingan dan hambatan operasional).
   - **Bagian 3: Rekomendasi Harga Jual (Pricing)** (Rekomendasi harga berdasarkan data pasar vs perkiraan modal).
   - **Bagian 4: Strategi Pemasaran Murah** (Cara jualan efektif minim modal, misal: WA Group, reseller lokal, konsinyasi warung).
   - **Bagian 5: Status Kepatuhan Regulasi** (Checklist perizinan yang wajib diurus khusus untuk kategori produk pengguna, misal NIB -> SPP-IRT -> Halal untuk makanan kering, atau NIB -> BPOM MD -> Halal Reguler untuk makanan basah/frozen).
3. **Mekanisme Sitasi / Sumber:** Setiap komponen visual wajib menyertakan kunci "sources" yang berisi referensi asli (seperti nama undang-undang atau situs web pencarian) untuk membuktikan kejujuran informasi.

Format Output Wajib:
Kamu harus membalas HANYA dengan satu blok JSON yang valid, tanpa teks penjelasan tambahan, tanpa tanda pembungkus markdown selain JSON itu sendiri."""

        # Generate markdown content for the report
        markdown_content = f"""### Laporan Kelayakan Usaha {prod['name']} ({loc})

#### 1. Segmentasi Demografi & Psikografi (Target Pembeli)
* **Demografi:** Pekerja kantoran, ibu rumah tangga, dan mahasiswa/pelajar di wilayah {loc} yang menyukai kepraktisan kuliner.
* **Psikografi:** Konsumen mencari rasa autentik, kebersihan terjamin, serta harga ekonomis untuk konsumsi harian.

#### 2. Analisis Hambatan Masuk Pasar (Kompetitor)
* **Pesaing:** Sudah ada beberapa penjual {prod['name'].lower()} serupa di platform daring dan pasar fisik.
* **Tantangan:** Menjaga kebersihan olahan dan kualitas rasa yang konsisten di tengah persaingan harga yang ketat.

#### 3. Rekomendasi Harga Jual (Pricing)
* **Estimasi HPP:** Rp {price_hpp:,}
* **Harga Pasar Terdekat:** Rp {price_market:,}
* **Rekomendasi APPA:** **Rp {price_rec:,}** (Mengambil margin keuntungan sehat ~{int(((price_rec-price_hpp)/price_rec)*100)}% namun tetap kompetitif bagi pembeli pemula).

#### 4. Strategi Pemasaran Murah
* **Pemasaran WA:** Tawarkan sampel/tester gratis kepada grup arisan/warga perumahan terdekat di {loc}.
* **Sistem Reseller:** Buat skema komisi bagi tetangga/ibu rumah tangga yang ikut memasarkan produk Anda.

#### 5. Kelayakan Hukum & Perizinan (Status Kepatuhan)
* Pelaku usaha wajib segera mendaftarkan **NIB** secara online. 
* Terkait kategori produk olahan, Anda perlu memenuhi kewajiban **{checklist[1]['title']}** serta **{checklist[2]['title']}** sebelum tenggat waktu sertifikasi halal nasional pada **17 Oktober 2026**."""

        json_out = {
            "response": f"Berdasarkan analisa APPA, berikut laporan kelayakan bisnis {prod['name']} di {loc}. Silakan lihat tab laporan di atas untuk detail visualnya.",
            "artifacts": [
                {
                    "id": f"art-assessment-{100 + i}",
                    "title": f"Laporan Kelayakan Usaha {prod['name']}",
                    "sources": sources + ["SerpApi Google Shopping"],
                    "blocks": [
                        {
                            "type": "text",
                            "content": markdown_content,
                            "sources": ["Analisis Bisnis APPA"]
                        },
                        {
                            "type": "metric",
                            "data": { "hpp": price_hpp, "market_avg": price_market, "recommendation": price_rec },
                            "sources": ["Google Shopping"]
                        },
                        {
                            "type": "checklist",
                            "data": {
                                "items": checklist
                            },
                            "sources": sources
                        },
                        {
                            "type": "chart",
                            "data": {
                                "xAxis": [f"Pasar {loc}", "Rekomendasi APPA", "HPP Perkiraan"],
                                "yAxis": [price_market, price_rec, price_hpp],
                                "label": "Perbandingan Struktur Harga (Rupiah)"
                            },
                            "sources": ["Analisis Internal APPA"]
                        }
                    ]
                }
            ],
            "profile_updated": True
        }
        
        user_prompt = f"Gunakan data yang ada untuk mensintesis laporan kelayakan bisnis {prod['name']} di {loc}. Balas dengan JSON format kaku sesuai contoh."
        
        examples.append({
            "system": system_prompt,
            "user": user_prompt,
            "json_output": json.dumps(json_out, indent=2, ensure_ascii=False)
        })
        
    return examples

def main():
    print("Generating dataset examples...")
    decomp_examples = generate_decomposition_examples()
    synth_examples = generate_synthesis_examples()
    
    all_examples = decomp_examples + synth_examples
    random.shuffle(all_examples)
    
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dataset.jsonl"))
    
    print(f"Writing {len(all_examples)} examples to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        for ex in all_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            
    print("Dataset generation completed successfully!")

if __name__ == "__main__":
    main()
