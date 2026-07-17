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
- [x] Bikin struktur awal `data/regulatory_rules.json` mencakup seluruh F&B (Risiko Rendah & Tinggi).
- [x] Buat *script* `seed_qdrant.py` untuk memecah (*chunking*) teks dan memasukkannya ke Qdrant.

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
- [x] **Dynamic Search Pipeline:** Rombak `agent.py` dan `useChat.ts` agar *frontend* 100% patuh pada struktur `pipeline_init` dinamis dari LLM (tidak ada lagi *hardcode* `s1` dan `s2`).
- [ ] **Condensation Pipeline (Menunggu LLM Ini):**
  - [ ] Ubah output `condense_market_data` dari JSON (`MarketDataSchema`) menjadi **ringkasan Markdown** — karena konsumer satu-satunya adalah LLM Sintesis (Call 2) yang membaca *natural language*, bukan mesin parser.
  - [ ] Refactor `condensation.py`: Hapus `MarketDataSchema` Pydantic, ganti system prompt menjadi instruksi ringkas Markdown (ekstrak harga, kompetitor, insight kualitatif dalam format *bullet points*).
  - [ ] Tambahkan **BM25ContentFilter** dari Crawl4AI di `scrape_pages()` dan `scrape_google_shopping()` untuk memfilter noise sebelum masuk LLM (`result.markdown.fit_markdown`).
  - [ ] Ganti `mock_llm.py` dengan panggilan HuggingFace asli (`call_llm`) untuk fungsi `condense_market_data`.
  - [ ] Hapus `asyncio.sleep` mock di `agent.py` untuk step `p1`/`p2` dan sambungkan ke eksekusi pipeline asli.
  - [ ] Update label pipeline UI: `p1` → "Kondensasi Hasil Scraping" (tanpa "ke JSON"), hapus `p2` (Validasi Pydantic) karena tidak lagi relevan.
- [x] Pastikan integrasi *database* ke endpoint API berjalan lancar (saat ini frontend masih pakai MOCK_PROFILE, backend sudah SQLite).

### 🧠 Workstream B: AI Training & Data (PIC: Arya)
- [ ] Kumpulkan teks regulasi mentah untuk NIB, SPP-IRT, BPOM MD, dan Halal (Self-Declare & Reguler).
- [x] *Setup script* Web Scraper menggunakan kombinasi `duckduckgo-search` dan `Crawl4AI` untuk mengekstrak data harga pasar/kompetitor secara *open-source*.
- [ ] Susun draf awal *dataset* 1.000 entri dalam format JSONL.
- [ ] Selesaikan *training* QLoRA di Google Colab menggunakan *dataset* JSONL.
- [ ] Evaluasi akurasi dan perbandingan respons model sebelum vs sesudah.
- [ ] *Push* model *fine-tuned* ke HuggingFace Hub.
- [ ] Update `.env` backend dengan model ID HuggingFace yang baru.

### 💼 Workstream C: Bisnis, Deliverables & Frontend Integration (PIC: Adillah)
- [ ] Lakukan riset kompetitor langsung (terutama daftar & uji coba UMKM.AI).
- [ ] Buat kerangka awal (ToC) untuk Dokumen Proposal 20 Halaman, masukkan narasi Pilot Project Jawa Barat.
- [ ] Tulis isi lengkap proposal (tekankan penggunaan Bapanas/SerpApi dan fokus Jawa Barat).
- [ ] Bikin naskah/skrip untuk Video Proof of Work (7 menit), *setting* persona di Jawa Barat.
- [ ] Bikin naskah/skrip untuk Video Promosi (5 menit).
- [x] **Pipeline Transparency (Frontend):** Koding integrasi *client-side* SSE/WebSockets di Next.js untuk merender *streaming* data dari backend.

---

## 🧩 INTEGRATION & TESTING (Setelah Sprint Paralel Selesai)
*Fase penyatuan seluruh komponen, pencarian bug, dan finalisasi berkas.*

**Gilang & Arya (Testing & Bug Fixing):**
- [ ] *End-to-End Testing*: Coba jalankan aplikasi dengan *use case* yang ekstrem/rumit.
- [ ] **Tuning Prompt Engineering:** Perbaiki prompt secara iteratif saat menemukan *edge cases* atau halusinasi JSON selama testing berjalan.
- [ ] **Uji Sliding Window Context:** Pastikan *chat history* terpotong dengan benar (10 pesan terakhir) agar tidak kena limit token HuggingFace.
  - [x] Frontend (`api.ts`): Memastikan `chat_history.slice(-10)` sudah terkirim di body *request*.
  - [ ] Backend (`routes.py`): Meneruskan parameter `request.chat_history` ke dalam fungsi orchestrator `handle_chat_stream`.
  - [ ] Backend (`agent.py` & `inference.py`): Menginjeksikan `chat_history` ke dalam prompt LLM agar agen memiliki kesadaran konteks percakapan sebelumnya.
- [ ] Uji coba bongkar pasang Docker (`docker compose down -v` lalu `up --build`).
- [x] Perbaikan *bug* tata letak (*layout*) Next.js atau *bug* *routing* di FastAPI.
- [x] **Polishing & UX (Tambahan):** Selesaikan animasi FLIP *smooth-resize* untuk *chat input*, indikator *gradient scroll*, dan perbaiki *bug* agresif pada *auto-scroll* chat.
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
  - [ ] Gunakan **SerpApi Google Shopping API** (`gl=id`, location sesuai kota user) yang sudah ada di `.env` (`SEARCH_API_KEY`) — **BUKAN** *direct scraping* Tokopedia/Shopee (anti-bot terlalu kuat, risiko gagal saat demo *live*).
  - [ ] Render hasil pencarian supplier ke dalam komponen `<TableBlock />` yang sudah ada (kolom: Nama Toko, Harga Grosir, Platform, Link Langsung).
  - [ ] LLM Call 2 (Sintesis) menghitung estimasi HPP berdasarkan harga grosir terverifikasi dari Google Shopping, dan menyarankan user untuk negosiasi langsung ke Pasar Induk jika volume sudah besar.
  - *Catatan: Komponen `<MapBlock />` untuk lokasi fisik supplier sengaja di-DROP karena Google Shopping tidak mengembalikan alamat fisik penjual secara reliabel. Cukup `<TableBlock />`.*

**Arya**
- [ ] *Tuning* ulang latensi Qdrant dan respons `Qwen3-8B` agar stabil saat didemokan langsung di depan juri.

**Adillah (Pitching & UI Dev)**
- [ ] Koding UI *Mini Dashboard Evaluasi Bulanan* (Persona 6) untuk demo *live* (selama 10 jam Hackathon).
- [ ] Presentasi *Live Pitching*, mendemonstrasikan kelancaran UI Next.js dan sistem *database* yang baru saja dirakit saat Hackathon.

---
**Status Audit File:**
- [x] Seluruh file core Backend & Frontend telah diaudit secara presisi.
