# APPA — Project Backlog & Alur Kerja Paralel

Centang (`[x]`) tugas yang sudah selesai. Jangan lupa lakukan *commit* sesuai panduan Conventional Commits.
Backlog ini disusun berdasarkan *Workstream* agar seluruh anggota tim dapat mengeksekusi tugasnya secara **paralel** tanpa saling memblokir.

---

## 🏁 FOUNDATION (Selesai)
*Infrastruktur dasar agar semua Workstream bisa berjalan serentak.*

**Gilang (Frontend & Backend Base):**
- [x] Inisialisasi *repository* (Git) dan pasang `.pre-commit-config.yaml` & `.commitlintrc.yml`.
- [x] *Setup* kerangka Next.js (Frontend) dengan `npx create-next-app`.
- [x] *Setup* kerangka FastAPI (Backend) dan `requirements.txt`.
- [x] Konfigurasi `docker-compose.yml` awal (3 *services*: frontend, backend, qdrant).
- [x] Buat rute API dasar `/chat` di FastAPI (tanpa LLM, kembalikan json statik dulu).
- [x] Buat sistem *Mock Profile Persistence* (In-Memory/Context) untuk V1. (Selesai lebih awal: Backend sudah menggunakan SQLite di `models.py`!)

**Arya (Data & AI Base):**
- [ ] Bikin struktur awal `data/regulatory_rules.json` mencakup seluruh F&B (Risiko Rendah & Tinggi).
- [ ] Buat *script* `seed_qdrant.py` untuk memecah (*chunking*) teks dan memasukkannya ke Qdrant.

**Adillah (Bisnis, Validasi & UI Dev):**
- [ ] Koding komponen UI statis pendukung di Next.js (layout, typography, styling dasar).

**Gilang (UI/UX - Selesai):**
- [x] Desain & koding UI utama Next.js menggunakan pola *Bento Grid Artifact System* (satu tab laporan terkonsolidasi).
- [x] Bikin komponen orchestrator `ArtifactView` (blok konten disatukan dalam satu file tanpa sub-komponen terpisah, dan bersifat read-only untuk user).
- [x] Terapkan sistem update blok artifact secara dinamis oleh AI Agent (berbasis instruksi chat) tanpa form edit manual dari user.
- [x] Integrasikan `Recharts` untuk merender JSON dari backend menjadi grafik interaktif (`ChartBlock`).

---

## 🚀 PARALLEL SPRINT (Fase Berjalan)
*Ketiga Workstream di bawah ini dieksekusi secara bersamaan (Paralel).*

### 🛠️ Workstream A: Core Engine & Sinkronisasi (PIC: Gilang)
- [x] **Sinkronisasi Backend:** *Refactor* Pydantic schema (`routes.py`), *mock response* (`inference.py`), dan *System Prompt* (`assessment.py`) agar me-*return* JSON dengan struktur Bento Grid `artifacts`/`blocks` terbaru.
- [x] **Pipeline Transparency (Backend):** Implementasi Server-Sent Events (SSE) atau WebSockets di FastAPI untuk *streaming* status *Agent Orchestrator* secara *real-time*.
- [x] Susun dan kunci *System Prompts* di Python untuk *The JSON Railway Pattern* (Anti-Halusinasi) dengan struktur output Dynamic Artifacts yang mencantumkan sumber rujukan (sources) pada level blok/subkomponen.
- [x] **SearchArsenal & Multi-Tier Fallback:** Implementasi `SearchArsenal` di `web.py` dengan *exponential backoff* dan *jitter* untuk mengamankan 100% uptime dari pemblokiran bot (DuckDuckGo Tor -> SearXNG -> Yahoo Scraper).
- [x] **Sovereign Local Stack:** Integrasikan container lokal `tor`, `searxng`, dan `llama.cpp` ke dalam `docker-compose.yml` agar aplikasi dapat berjalan 100% lokal tanpa ketergantungan API pihak ketiga (bebas dari error 429 atau internet *down*).
- [x] **Fallback Module:** Buat modul `fallback.py` mandiri untuk merender *Generative UI* yang valid jika LLM Call 2 rusak/halusinasi JSON, memisahkan logika darurat dari *Core Orchestrator*.
- [x] **Condensation Pipeline (Menunggu LLM Ini):**
  - [x] Ubah output `condense_market_data` dari JSON (`MarketDataSchema`) menjadi **ringkasan Markdown** — karena konsumer satu-satunya adalah LLM Sintesis (Call 2) yang membaca *natural language*, bukan mesin parser (SLM-MUX Pattern).
  - [x] Refactor `condensation.py`: Hapus `MarketDataSchema` Pydantic, ganti system prompt menjadi instruksi ringkas Markdown (ekstrak harga, kompetitor, insight kualitatif dalam format *bullet points*).
  - [x] Tambahkan **BM25ContentFilter** dari Crawl4AI di `scrape_pages()` dan `scrape_google_shopping()` untuk memfilter noise sebelum masuk LLM (`result.markdown.fit_markdown`).
  - [x] Ganti `mock_llm.py` dengan panggilan HuggingFace asli (`call_llm`) untuk fungsi `condense_market_data`.
  - [x] Hapus `asyncio.sleep` mock di `agent.py` untuk step `p1`/`p2` dan sambungkan ke eksekusi pipeline asli.
  - [x] Update label pipeline UI: `p1` → "Kondensasi Hasil Scraping" (tanpa "ke JSON"), hapus `p2` (Validasi Pydantic) karena tidak lagi relevan.
  - [x] **Context Window Protection:** Batasi markdown scraping maksimal 1500 karakter sebelum diproses SLM untuk mencegah kebocoran memori (500 Server Error) selama *heavy load iteratif*.
- [x] Pastikan integrasi *database* ke endpoint API berjalan lancar (saat ini frontend masih pakai MOCK_PROFILE, backend sudah SQLite).

### 🧠 Workstream B: AI Training & Data (PIC: Arya)
- [ ] **Riset Entity Extractor:** Evaluasi apakah akan menggunakan direct API call ke model utama atau menggunakan model NER terpisah untuk ekstraksi entitas yang lebih optimal.
- [ ] Kumpulkan teks regulasi mentah untuk NIB, SPP-IRT, BPOM MD, dan Halal (Self-Declare & Reguler).
- [x] *Setup script* Web Scraper menggunakan kombinasi `duckduckgo-search` dan `Crawl4AI` untuk mengekstrak data harga pasar/kompetitor secara *open-source*.
- [ ] Susun draf awal *dataset* 1.000 entri dalam format JSONL.
- [x] Selesaikan *training* QLoRA di Google Colab menggunakan *dataset* JSONL.
- [x] Evaluasi akurasi dan perbandingan respons model sebelum vs sesudah.
- [x] **Local AI Sovereign Deployment:** Kuantisasi hasil model menjadi format `.gguf` dan *load* menggunakan Docker container `llama.cpp` dengan eksekusi CUDA secara lokal, menggantikan ketergantungan pada HuggingFace API.
- [x] Update `.env` backend dengan `LOCAL_LLM_URL` yang menunjuk ke container `llama.cpp`.

### 💼 Workstream C: Bisnis, Deliverables & Frontend Integration (PIC: Adillah)
- [ ] Lakukan riset kompetitor langsung (terutama daftar & uji coba UMKM.AI).
- [ ] Buat kerangka awal (ToC) untuk Dokumen Proposal 20 Halaman, masukkan narasi Pilot Project Jawa Barat.
- [ ] Tulis isi lengkap proposal (tekankan penggunaan Bapanas/SerpApi dan fokus Jawa Barat).
- [ ] Bikin naskah/skrip untuk Video Proof of Work (7 menit), *setting* persona di Jawa Barat.
- [ ] Bikin naskah/skrip untuk Video Promosi (5 menit).
- [x] **Pipeline Transparency (Frontend):** Koding integrasi *client-side* SSE/WebSockets di Next.js untuk merender *streaming* data dari backend.

### 🔄 Workstream D: Architectural Refactor (Dynamic Agent) (PIC: Gilang)
- [ ] **Dynamic Regulation Query:** Buat pemanggilan `vector_search` (Qdrant) bersifat opsional/dinamis. LLM hanya akan memanggilnya jika pertanyaan user membutuhkan informasi regulasi atau hukum.
- [x] **Prompt Engineering (Dynamic Architecture):**
  - [x] **Intent-Driven Queries (`decomposition.py`):** Rombak sistem prompt. Kueri pencarian tidak boleh lagi statis/kaku ("harga menu", "kompetitor"). Biarkan agen secara bebas merumuskan list of `sub_queries` beserta *intent* (`price_fetch` vs `general`) berdasarkan apa yang ditanyakan user.
  - [x] **Bento Synthesis (`assessment.py`):** Sesuaikan prompt agar LLM memahami format JSON baru yang lebih bebas, memungkinkannya memilih komponen visual mana yang akan di-render.
- [x] **Modular Web Search (with Guardrails):** Modifikasi web search tool agar berfungsi selayaknya chatbot web search umum namun tetap terkontrol. Pisahkan *scraping pipeline* berdasarkan *intent*:
  - Jika agen mencari harga (`price_fetch`), gunakan *pipeline* GIGO saat ini yang sangat teroptimasi.
  - Jika agen mencari hal lain, gunakan *pipeline* umum (*general search*) tanpa GIGO filter ketat.
- [ ] **Dynamic E-Commerce Dorking:** Buat pemanggilan `scrape_ecommerce_pricing` (DuckDuckGo Dorking spesifik Tokopedia/Shopee) menjadi opsional di `agent.py`. Hanya dipanggil jika `decomposition.py` mengeluarkan *flag* `needs_price_fetching`.
- [x] **Bento UI Overhaul:**
  - [x] Pecah Markdown component agar tidak terlalu penuh (maksimal 1 topik per 1 block komponen).
  - [x] Ganti default `bar chart` menjadi `line chart` agar lebih masuk akal untuk memvisualisasikan tren pasar/harga.
  - [x] Biarkan LLM (`assessment.py`) secara bebas dan dinamis menyusun komponen Bento grid yang benar-benar relevan dengan *intent* pengguna, bukan memaksakan format kaku.

---

## 🧩 INTEGRATION & TESTING (Setelah Sprint Paralel Selesai)
*Fase penyatuan seluruh komponen, pencarian bug, dan finalisasi berkas.*

**Gilang & Arya (Testing & Bug Fixing):**
- [x] **End-to-End & Edge Case Testing:**
  - [x] Uji coba skenario *Rate Limit* (429) API Hugging Face & WAF Proxy: pastikan agen berhasil menangkap *error* dan melakukan *fallback* tanpa merusak UI (*crash*). (Selesai via SearchArsenal & fallback.py)
  - [x] Uji coba multi-turn chat: kirim pesan lanjutan (follow-up) dan pastikan agen tidak kebingungan.
  - [x] Uji coba UI di resolusi Mobile (layar kecil): pastikan Bento Grid reflow dan indikator *scroll* input chat berfungsi dengan baik di *smartphone*.
  - [x] Uji coba dengan produk aneh/langka untuk melihat bagaimana model beradaptasi merender komponen (apakah halusinasi?).
  - [x] Uji Coba Ultimate 20x Regression: Memastikan isolasi state *Profile Database* antar sesi menggunakan generator `user_id` dinamis pada script test.
- [x] **Tuning Prompt Engineering & Guardrails:** Perbaiki prompt secara iteratif saat menemukan *edge cases* atau halusinasi JSON selama testing berjalan.
  - [x] **Python-Level Guardrails:** Terapkan sanitasi `price_only` di `agent.py` untuk secara paksa menghapus format *bullet points* jika LLM berhalusinasi mengulang isi tabel.
  - [x] Tambahkan *Regex Quantity Fallback* pada kondensasi harga untuk menangkap variasi tulisan "isi 50 pcs" demi keakuratan harga per-satuan.
- [x] **Uji Sliding Window Context:** Pastikan *chat history* terpotong dengan benar (10 pesan terakhir) agar tidak kena limit token HuggingFace.
  - [x] Frontend (`api.ts`): Memastikan `chat_history.slice(-10)` sudah terkirim di body *request*.
  - [x] Backend (`routes.py`): Meneruskan parameter `request.chat_history` ke dalam fungsi orchestrator `handle_chat_stream`.
  - [x] Backend (`agent.py` & `inference.py`): Menginjeksikan `chat_history` ke dalam prompt LLM agar agen memiliki kesadaran konteks percakapan sebelumnya.
- [x] Uji coba bongkar pasang Docker (`docker compose down -v` lalu `up --build`).
- [x] Perbaikan *bug* tata letak (*layout*) Next.js atau *bug* *routing* di FastAPI.
  - [x] **Bento Grid Refactor:** Migrasi dari CSS Grid kaku (`grid-cols-3`) ke Flexbox (`flex-wrap`, `basis`, `flex-1`) untuk menghilangkan *gaping hole* (ruang kosong) secara dinamis.
  - [x] **Metric Fallback:** Tambahkan *null checks* (`|| 0`) pada `MetricBlockRenderer` agar Next.js tidak crash (TypeError) saat LLM gagal me-return struktur angka yang valid.
- [x] **Polishing & UX (Tambahan):** Selesaikan animasi FLIP *smooth-resize* untuk *chat input*, indikator *gradient scroll*, dan perbaiki *bug* agresif pada *auto-scroll* chat.
  - [x] **Pipeline Details Polishing:** Rombak format `agent.py` (SSE) agar hasil kondensasi marketplace dan fallback message dirender dengan lebih rapi di UI dropdown.
- [x] **HuggingFace Limit Optimization:** Kurangi batas pemotongan string markdown mentah dari 15.000 ke 8.000 karakter (`web.py`) agar terhindar dari limit *max input tokens* di API Inference gratisan.
- [ ] *CODE FREEZE* — dilarang menambah fitur baru.

**Adillah (Media, Submit & UI Bug Fixing):**
- [ ] Lakukan perbaikan *bug layout* (UI Fixing) di Next.js hasil dari *End-to-End Testing*.
- [ ] Rekam layar (*screen record*) jalannya aplikasi untuk Video Proof of Work (Mendemonstrasikan Mock Profile).
- [ ] Buat *Voice Over* dan selesaikan *editing* Video Promosi.
- [ ] Periksa ulang format README di GitHub (Setup Guide, dll).
- [ ] *Double check* semua persyaratan pendaftaran Batch 2 dan finalisasi dokumen di *website* Compfest.
- [ ] **SUBMIT seluruh berkas ke portal AIC COMPFEST 18 sebelum 25 Agustus 23:55 WIB.**

---

## 🏆 HACKATHON LIVE (V2 - 26 & 27 September)
*Persiapan presentasi final 10 jam offline.*

**Gilang (Live Hackathon 10 Jam)**
- [x] Migrasi *Mock Profile Persistence* ke **SQLite Database** sesungguhnya. (Selesai lebih awal di Foundation!)
- [ ] **[BONUS] Pencarian Supplier Bahan Baku Grosir:**
  - [ ] Tambahkan *prompt variant* baru di `decomposition.py` agar LLM Call 1 men-*generate* query pencarian supplier (misal: `"Grosir Singkong Surabaya"`) ketika user bertanya soal sumber bahan baku.
  - [ ] Gunakan fungsi **DuckDuckGo Dorking khusus E-Commerce** (seperti `site:tokopedia.com`) di `web.py` — **BUKAN** SerpApi atau Google Shopping API (untuk menghindari *rate limit* dan biaya).
  - [ ] Render hasil pencarian supplier ke dalam komponen `<TableBlock />` yang sudah ada (kolom: Nama Toko, Harga Grosir, Platform, Link Langsung).
  - [ ] LLM Call 2 (Sintesis) menghitung estimasi HPP berdasarkan harga grosir terverifikasi.

**Arya**
- [ ] *Tuning* ulang latensi Qdrant dan respons `Qwen3-8B` agar stabil saat didemokan langsung di depan juri.

**Adillah (Pitching & UI Dev)**
- [ ] Koding UI *Mini Dashboard Evaluasi Bulanan* (Persona 6) untuk demo *live* (selama 10 jam Hackathon).
- [ ] Presentasi *Live Pitching*, mendemonstrasikan kelancaran UI Next.js dan sistem *database* yang baru saja dirakit saat Hackathon.

---
**Status Audit File:**
- [x] Seluruh file core Backend & Frontend telah diaudit secara presisi.
