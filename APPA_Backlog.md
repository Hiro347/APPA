# APPA — Project Backlog

Centang (`[x]`) tugas yang sudah selesai. Jangan lupa lakukan *commit* sesuai panduan Conventional Commits.

## V1 (Tahap Penyisihan): Foundation & Data (Minggu 1–2 | 18–31 Juli)

**Gilang (Frontend & Backend Base)**
- [x] Inisialisasi *repository* (Git) dan pasang `.pre-commit-config.yaml` & `.commitlintrc.yml`.
- [ ] *Setup* kerangka Next.js (Frontend) dengan `npx create-next-app`.
- [x] *Setup* kerangka FastAPI (Backend) dan `requirements.txt`.
- [x] Konfigurasi `docker-compose.yml` awal (3 *services*: frontend, backend, qdrant).
- [x] Buat rute API dasar `/chat` di FastAPI (tanpa LLM, kembalikan json statik dulu).
- [x] Buat sistem *Mock Profile Persistence* (In-Memory/Context) untuk V1.

**Arya (Data & AI Base)**
- [x] Bikin struktur awal `data/regulatory_rules.json` mencakup seluruh F&B (Risiko Rendah & Tinggi).
- [ ] Kumpulkan teks regulasi mentah untuk NIB, SPP-IRT, BPOM MD, dan Halal (Self-Declare & Reguler).
- [ ] *Setup script* untuk menarik data API Bapanas (Jawa Barat) dan SerpApi (Google Shopping).
- [x] Buat *script* `seed_qdrant.py` untuk memecah (*chunking*) teks dan memasukkannya ke Qdrant.
- [ ] Susun draf awal *dataset* 1.000 entri dalam format JSONL.

**Adillah (Bisnis & Validasi)**
- [ ] Lakukan riset kompetitor langsung (terutama daftar & uji coba UMKM.AI).
- [ ] Buat kerangka awal (ToC) untuk Dokumen Proposal 20 Halaman, masukkan narasi Pilot Project Jawa Barat.
- [ ] Jadwalkan dan lakukan wawancara awal dengan UMKM terkait validasi *pain point* regulasi.

---

## V1 (Tahap Penyisihan): Core Development (Minggu 3–4 | 1–14 Agustus)

**Gilang (UI/UX & AI Prompting)**
- [ ] Desain & koding UI utama Next.js menggunakan pola *Artifact Panel* (Split-pane / Modal).
- [ ] Bikin 4 komponen *Generative UI* (Markdown, Checklist, Pricing, Chart).
- [ ] Integrasikan `Recharts` untuk merender JSON dari backend menjadi grafik interaktif.
- [ ] Susun dan kunci *System Prompts* di Python untuk *The JSON Railway Pattern* (Anti-Halusinasi).

**Arya (Fine-Tuning & Deploy)**
- [ ] Selesaikan *training* QLoRA di Google Colab menggunakan *dataset* JSONL.
- [ ] Evaluasi akurasi dan perbandingan respons model sebelum vs sesudah.
- [ ] *Push* model *fine-tuned* ke HuggingFace Hub.
- [ ] Update `.env` backend dengan model ID HuggingFace yang baru.

**Adillah (Proposal & Storyboarding)**
- [ ] Tulis isi lengkap proposal (tekankan penggunaan Bapanas/SerpApi dan fokus Jawa Barat).
- [ ] Bikin naskah/skrip untuk Video Proof of Work (7 menit), *setting* persona di Jawa Barat.
- [ ] Bikin naskah/skrip untuk Video Promosi (5 menit).

---

## V1 (Tahap Penyisihan): Integration & Deliverables (Minggu 5–6 | 15–25 Agustus)

**Gilang & Arya (Testing & Bug Fixing)**
- [ ] *End-to-End Testing*: Coba jalankan aplikasi dengan *use case* yang ekstrem/rumit.
- [ ] Uji coba bongkar pasang Docker (`docker compose down -v` lalu `up --build`).
- [ ] Perbaikan *bug* tata letak (*layout*) Next.js atau *bug* *routing* di FastAPI.
- [ ] *CODE FREEZE* — dilarang menambah fitur baru.

**Adillah (Media & Submit)**
- [ ] Rekam layar (*screen record*) jalannya aplikasi untuk Video Proof of Work (Mendemonstrasikan Mock Profile).
- [ ] Buat *Voice Over* dan selesaikan *editing* Video Promosi.
- [ ] Periksa ulang format README di GitHub (Setup Guide, dll).
- [ ] *Double check* semua persyaratan pendaftaran Batch 2 dan finalisasi dokumen di *website* Compfest.
- [ ] **SUBMIT seluruh berkas ke portal AIC COMPFEST 18 sebelum 25 Agustus 23:55 WIB.**

---

## V2 (Tahap Finalis): Live Hackathon & Pitching (26–27 September)

**Gilang (Live Hackathon 10 Jam)**
- [x] Migrasi *Mock Profile Persistence* ke **SQLite Database** sesungguhnya.
- [ ] Koding UI *Mini Dashboard Evaluasi Bulanan* (Persona 6) untuk demo *live*.

**Arya**
- [ ] *Tuning* ulang latensi Qdrant dan respons `Qwen3-8B` agar stabil saat didemokan langsung di depan juri.

**Adillah**
- [ ] Presentasi *Live Pitching*, mendemonstrasikan kelancaran UI Next.js dan sistem *database* yang baru saja dirakit saat Hackathon.
