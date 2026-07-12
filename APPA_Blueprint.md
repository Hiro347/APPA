# Cetak Biru Proyek: APPA (Analisa Pasar Pintar & Akurat)

### AI Market Research & Business Copilot untuk UMKM Indonesia

APPA (**Analisa Pasar Pintar & Akurat**) membantu pelaku UMKM Indonesia melakukan riset pasar secara cerdas sekaligus mendeteksi kesiapan regulasi usaha mereka. APPA menjawab tiga pertanyaan tersulit: **apakah ide ini layak (analisis pasar & kompetitor), izin apa saja yang dibutuhkan secara legal (checklist regulasi jika dibutuhkan), dan dari mana modal datang (rekomendasi pembiayaan)** — lewat satu asisten chatbot yang mengingat profil bisnis penggunanya seiring waktu.

> **Dokumen ini adalah panduan bisnis & produk tim.** Berisi positioning, persona, konten regulasi, diferensiasi, dan model bisnis — bahan utama untuk proposal dan pitching. Untuk arsitektur, stack teknologi, dan panduan development, lihat [Tech Spec](APPA_Tech_Spec.md).

---

## 1. Positioning & Elevator Pitch

**Nama produk tetap APPA** (singkatan dari **Analisa Pasar Pintar & Akurat**).

**Subjudul:** *"Asisten AI untuk Riset Pasar Pintar dan Kesiapan Regulasi Usaha UMKM Indonesia — dari Ide sampai Siap Berjualan Legal secara Efektif."*

**Kategori posisi (headline utama, ditebalkan):**

| Opsi | Kapan dipakai |
|---|---|
| **AI Market Intelligence & Business Copilot** *(rekomendasi)* | Judul slide utama |
| AI Business Intelligence untuk UMKM | Kalau juri berlatar korporat/data |
| Smart Commerce & Compliance Assistant | Kalimat pendukung saat fokus ke modul kelayakan & legalitas |

**Elevator pitch:**
> "74% UMKM Indonesia meluncurkan produk baru tanpa riset pasar terlebih dahulu karena biaya riset pasar konvensional yang mahal. Selain itu, banyak pelaku usaha yang belum memiliki izin legalitas dasar seperti NIB, SPP-IRT, dan sertifikasi Halal yang wajib dipenuhi menjelang tenggat 17 Oktober 2026. APPA (Analisa Pasar Pintar & Akurat) adalah AI chatbot riset pasar terintegrasi yang membantu UMKM menganalisis kelayakan pasar, harga jual, dan kompetitor secara real-time, sekaligus memandu kesiapan perizinan usaha mereka secara bertahap dan mengingat profil bisnis mereka lintas sesi."

**Mantra pitching (ulangi terus ke juri):** *"Kami bukan chatbot. Kami mengubah birokrasi dan informasi bisnis yang tersebar menjadi checklist dan rencana aksi yang bisa langsung dijalankan."* Ini tidak mengklaim "lebih pintar dari ChatGPT" — prinsip *vertical specialist* ini dipertahankan dari v2/v3 karena sudah sejalan dengan rekomendasi *Critical Review*.

**Prinsip format output (rujukan: Wayfinder, lablab.ai/Bright Data Hackathon 2026):** Output final APPA bukan sekadar checklist bercentang, tapi **satu laporan konsolidasi** yang menyatukan kelayakan usaha, urutan izin dengan tenggat, opsi pembiayaan, dan sinyal risiko pasar dalam satu dokumen. "Kami bukan chatbot" dibuktikan lewat bentuk output, bukan cuma diklaim di slide — dan harus tercermin literal di UI demo.

**Kenapa positioning ini kredibel — bukan cuma klaim:**
1.  **Arsitektur sudah siap menampung modul kepatuhan tanpa rebuild** — bounded fan-out 3-call yang sama dipakai untuk riset pasar dan checklist regulasi (lihat Tech Spec).
2.  **Tenggat Halal 17 Oktober 2026 adalah urgensi nyata dan terverifikasi**, bukan klaim generik "regulasi itu rumit."
3.  **Kategori "AI + UMKM Indonesia" sudah ramai** (Navigo, UMKM.AI) — argumen yang bertahan bukan "tidak ada yang melakukan ini," tapi kedalaman terverifikasi pada satu proses spesifik (kepatuhan berurutan + memori bisnis).

### Argumen penghubung ke tema Smart Commerce (wajib masuk proposal & slide)

Nama produk adalah APPA (Analisa Pasar Pintar & Akurat), dan tema yang disasar adalah Smart Commerce. Kedua hal ini terhubung langsung, bukan dipaksakan:

> Riset pasar tidak hanya tentang tren harga dan preferensi konsumen — riset pasar adalah tentang **kelayakan komersial dan operasional**. Di Indonesia, transaksi komersial (Smart Commerce) tidak dapat terjadi tanpa kepatuhan hukum dasar:
> - Tanpa **NIB**, UMKM tidak bisa mendaftar sebagai seller di marketplace (Shopee, Tokopedia).
> - Tanpa **SPP-IRT**, produk pangan olahan tidak bisa dijual legal di ritel modern (Indomaret, Alfamart).
> - Tanpa **Sertifikasi Halal** (tenggat 17 Oktober 2026), seluruh produk makanan-minuman UMKM kehilangan hak jual di pasar formal.
>
> **Sertifikasi Halal, SPP-IRT, dan NIB adalah kunci pembuka gerbang bagi UMKM untuk menjual produknya di platform e-commerce dan ritel modern secara legal.** APPA memastikan UMKM bukan hanya tahu *apa yang mau dijual* dan *ke siapa* (Riset Pasar), tapi juga *apakah mereka secara legal boleh menjualnya* (Regulasi) — dan langkah konkret untuk sampai ke sana.

| Komponen APPA | Relevansi ke Smart Commerce (Rulebook) |
|---|---|
| Analisis Peluang & Kompetitor | *"sisi konsumen, sales operasional"* — memahami pasar sebelum menjual |
| Checklist Regulasi (NIB → SPP-IRT → Halal) | *"transaksi komersial"* — syarat legal agar transaksi bisa terjadi |
| Rekomendasi Pembiayaan (KUR) | *"sales operasional"* — modal untuk menjalankan operasi penjualan |
| Rencana Aksi Konsolidasi | Menyatukan semua di atas jadi keputusan bisnis yang actionable |

Gunakan tabel ini di slide proposal untuk menunjukkan bahwa setiap modul memetakan langsung ke definisi Smart Commerce di rulebook.

---

## 2. Masalah Riil (data 2026)

*   **Dua akar kegagalan UMKM yang jarang dipisahkan:** ~50% UMKM baru gagal di tahun pertama (naik ke 50–60% dalam tiga tahun, ~80% dalam lima tahun). Survei KADIN: ~74% pelaku usaha meluncurkan produk baru tanpa riset pasar.
*   **Kesenjangan legalitas:** dari ~67 juta UMKM, riset independen mencatat baru ~5,8% yang punya NIB (2023) — bukan karena NIB sulit (gratis 100%, terbit dalam hitungan menit via OSS RBA sejak PP 28/2025), tapi karena UMKM tidak tahu izin apa yang dibutuhkan, urutannya, dan kapan wajib.
*   **Jendela waktu nyata:** seluruh produk makanan-minuman UMKM wajib bersertifikat halal per **17 Oktober 2026** (UU 33/2014 jo. PP 42/2024) — ~3 minggu setelah malam final AIC (27 September 2026). Program SEHATI 2026 menyediakan 1,35 juta kuota gratis, tapi kompetitif dan prosesnya (SIHALAL, Pendamping PPH, Komite Fatwa) tidak dipahami kebanyakan pelaku usaha rumahan.
*   **Kenapa "memori" penting justru untuk legalitas:** perjalanan izin bertahap (NIB → SPP-IRT → Halal) bisa berjarak minggu antar langkah — pola pemakaian yang jauh lebih cocok untuk asisten yang mengingat progres dibanding riset harga yang sifatnya point-in-time.

**Solusi:** asisten yang menggabungkan riset pasar real-time dengan regulasi bisnis, lewat lima alur kerja (Bagian 3), dan melacak progres legalitas pengguna (NIB ✅ → SPP-IRT belum → Halal belum) antar sesi.

---

## 3. Lima Modul Workflow

| # | Modul | Deskripsi | Status |
|---|---|---|---|
| 1 | Analisis Peluang | Demografi & Studi Kasus UMKM + fan-out real-time | Sudah ada |
| 2 | Analisis Kompetitor | Search API + Harga Acuan Komoditas | Sudah ada |
| 3 | Rekomendasi Harga (Pricing) | Menghitung harga jual berdasar modal (HPP) vs harga kompetitor saat ini (Web Search) | **FITUR BARU** (Aman dari risiko prediksi) |
| 4 | **Checklist Regulasi** | Panduan regulasi & perizinan (NIB, SPP-IRT, Halal) — *dihasilkan jika dibutuhkan* | Perlu pendalaman konten (Bagian 5) |
| 5 | Rencana Aksi — **satu laporan konsolidasi** | Laporan analisa pasar terstruktur dikombinasikan dengan checklist kepatuhan hukum | Perluasan kecil di dataset |

Integrasi pilar riset pasar dan perizinan memastikan pengguna mendapatkan analisis kelayakan komersial yang lengkap dan siap eksekusi.

---

## 4. Persona & Prioritas Demo

| # | Persona | Trigger | Contoh Query | Fitur Terkait | Output AI (Bentuk UI) |
|---|---|---|---|---|---|
| 1 | Calon pedagang (pre-launch) | Sebelum belanja bahan baku | "Modal 2 juta, jual keripik pedas di Surabaya, worth it?" | Format output baku | Laporan Kelayakan (Tingkat Kompetisi, Perkiraan Margin, Skor Kelayakan 1-10) |
| 2 | Pedagang mau ekspansi | Buka cabang/lini baru | "Bakso Malang, buka cabang di Batu?" | Fan-out multi-query | Tabel Perbandingan 2 Lokasi (Demografi, Kepadatan Kompetitor) |
| 3 | Reseller/dropship rutin | Cek harga rutin | "Harga skincare X turun nggak minggu ini?" | User Profile Persistence | Tabel Historis (*Price Tracker*) & Notifikasi Perubahan |
| 4 | Pengepul bahan baku | Reaktif (cuaca, gagal panen) | "Cabai rawit Bandung kenapa naik terus?" | Conditional Deep-Dive | Analisis Paragraf Mendalam (Hasil rangkuman berita Web Search terbaru) |
| **5** | **Produsen rumahan naik kelas legal** | Mau masuk marketplace/retail resmi, tenggat Halal mendekat | "Jual makanan dari rumah, urut dari mana?" | Checklist Regulasi + Profile Persistence | **1. Chat Klarifikasi:** "Makanannya jenis apa? Basah/Kering?"<br/>**2. Consolidated Report:** *Timeline* izin & estimasi biaya |
| 6 | Bisnis Stabil (Evaluasi Rutin) | Cek performa bulanan vs Tren Pasar | "Penjualan keripik bulan ini turun 20%, ada tren pasar baru nggak?" | Profile Persistence (Memory) + Web Search | **Mini Dashboard Evaluasi**: Grafik/Tabel perbandingan performa bulan lalu vs ringkasan tren pasar saat ini |

**Fokus demo: Persona 4 & 5.** Persona 4 paling visual secara teknis. Persona 5 menunjukkan perjalanan dua arah yang sangat organik: **AI tidak langsung mereset, melainkan melakukan klarifikasi (chit-chat)** sampai entitas bisnis dirasa cukup, barulah merender perjalanan legalitas (NIB → SPP-IRT → Halal) — cerita *profile persistence* paling kuat sekaligus menunjukkan kecerdasan *Agentic Workflow*. Persona 6 menegaskan bahwa APPA menemani *sepanjang* bisnis berjalan.

---

## 5. Kepatuhan Regulasi Terintegrasi (Fokus Ekosistem F&B)

**Strategi Integrasi Cerdas:** Untuk memberikan solusi analisis pasar yang bernilai tinggi, modul regulasi ditawarkan sebagai pendukung kelayakan bisnis, **difokuskan khusus pada ekosistem F&B Pangan Olahan**. Alasan bisnis: F&B mencakup lebih dari 60% UMKM Indonesia dan sedang menghadapi urgensi *Tenggat Wajib Halal 17 Oktober 2026*. APPA mengintegrasikan pengecekan izin ini secara otomatis ketika mendeteksi kategori bisnis makanan/minuman, sehingga pengguna tidak perlu bertanya secara terpisah tentang aspek hukum.

**Skenario Demo Aspek Kepatuhan:**
- *User:* bertanya tentang prospek jualan keripik pisang di pasar lokal $\rightarrow$ AI memberikan analisis pasar, lalu menambahkan checklist regulasi SPP-IRT (Risiko Rendah) dan sertifikat Halal Self-Declare.
- *User:* bertanya tentang jualan bakso sapi beku (frozen) $\rightarrow$ AI mendeteksi kategori makanan basah beku berisiko lebih tinggi, lalu mengarahkan ke wajib Izin Edar BPOM MD (bukan SPP-IRT).
Ini menunjukkan bahwa analisis kelayakan APPA mencakup aspek komersial sekaligus legalitas operasional secara seimbang.

*(Catatan: Jika kueri riset pasar tidak berkaitan dengan makanan, AI akan fokus pada parameter pasar standar dan memberikan disclaimer regulasi umum jika diperlukan).*

### Satu sumber kebenaran, bukan sekadar diagram

Alur keputusan (NIB → SPP-IRT/BPOM → Halal → PPh Final) diperlakukan sebagai **skema data bersama** (`regulatory_rules.json`) yang dipakai baik oleh koleksi Qdrant maupun generator dataset pelatihan, supaya keduanya tidak pernah tidak sinkron saat regulasi berubah. Contoh struktur minimal:

```json
{
  "kuliner_rumahan_risiko_rendah": {
    "urutan_izin": [
      {"izin": "NIB", "wajib": true, "dasar_hukum": "PP 28/2025"},
      {"izin": "SPP-IRT", "wajib": true, "dasar_hukum": "PerBPOM 4/2024", "prasyarat": "NIB"},
      {"izin": "Sertifikasi Halal (self-declare/SEHATI)", "wajib": true, "tenggat": "2026-10-17", "prasyarat": "NIB"}
    ]
  },
  "pangan_risiko_tinggi": {
    "urutan_izin": [
      {"izin": "NIB", "wajib": true, "dasar_hukum": "PP 28/2025"},
      {"izin": "Izin Edar BPOM MD/ML", "wajib": true, "prasyarat": "NIB"},
      {"izin": "Sertifikasi Halal", "wajib": true, "tenggat": "2026-10-17", "prasyarat": "NIB"}
    ]
  }
}
```

Satu orang di tim harus jadi pemilik file ini — setiap perubahan regulasi diedit di sini dulu, baru disebarkan ke Qdrant dan dataset.

### A. NIB via OSS RBA (fondasi semua izin lain)
Dasar hukum PP 28/2025. Daftar di oss.go.id → pilih "Usaha Mikro dan Kecil" → verifikasi NIK → isi KBLI → NIB terbit otomatis untuk risiko rendah, biasanya menit hingga 24 jam. **Gratis 100%** — model harus tegas soal ini karena banyak jasa pihak ketiga memungut biaya untuk sesuatu yang gratis. NIB adalah prasyarat wajib untuk KUR, Halal, SPP-IRT/BPOM, dan SNI; tidak kedaluwarsa.

### B. SPP-IRT vs. BPOM
SPP-IRT (dasar PerBPOM 4/2024): pangan olahan skala rumahan risiko rendah, proses online via sppirt.pom.go.id, **berlaku 5 tahun**, mensyaratkan NIB. Dikecualikan ke BPOM penuh (e-reg.pom.go.id): produk risiko tinggi (susu, daging olahan, makanan kaleng, bayi), klaim kesehatan/gizi, umur simpan < 7 hari, siap saji di tempat produksi. Kesalahan paling umum: pelaku usaha tidak tahu produknya masuk kategori mana — dataset harus melatih model membedakan berdasarkan deskripsi produk, bukan menjawab generik.

### C. Sertifikasi Halal — jendela waktu paling mendesak
Dasar hukum UU 33/2014 jo. PP 42/2024. **Wajib penuh 17 Oktober 2026** untuk seluruh produk makanan-minuman UMK. Skema self-declare (bahan halal terverifikasi, proses sederhana): SIHALAL → verifikasi Pendamping PPH → verifikasi BPJPH → STTD → Komite Fatwa → sertifikat. Program SEHATI 2026: 1,35 juta kuota gratis (Kepkaban BPJPH 146/2025), syarat NIB mikro/kecil + bahan halal terverifikasi. Satu-satunya area regulasi dengan tenggat keras publik dan terverifikasi — jadikan hook utama pitching dengan angka hari mundur konkret.

### D. PPh Final UMKM 0,5% — contoh nyata regulasi berubah di tengah proyek
PP 20/2026 (22 April 2026, mengubah PP 55/2022): tarif 0,5% dan ambang Rp4,8 miliar/tahun tetap, tapi subjek dipersempit ke WP Orang Pribadi, PT Perorangan, dan Koperasi — **CV, firma, dan PT umum tidak bisa lagi jadi peserta baru**. Batas waktu pemakaian untuk WP Orang Pribadi/PT Perorangan dihapus jadi tanpa batas waktu; Koperasi tetap dibatasi 4 tahun. Ini bukti hidup kenapa koleksi regulasi butuh pemilik yang aktif memantau.

---

## 6. Diferensiasi Kompetitif (baca ini sebelum pitching)

**Riset langsung ke situs UMKM.AI mengubah argumen ini.** Mereka sudah melakukan prediksi tren pasar & permintaan konsumen, rekomendasi harga/promosi, dan analisis kompetitor real-time — bukan hanya dokumen hukum seperti asumsi sebelumnya. Klaim "mereka generalis tanpa riset pasar" tidak akurat lagi.

| Kompetitor | Yang mereka lakukan (terverifikasi) | Klaim diferensiasi yang **bisa dipertahankan** |
|---|---|---|
| **UMKM.AI** | 25+ tools, 50 staf: chatbot WhatsApp, prediksi tren pasar, analisis kompetitor, draf dokumen hukum (kontrak/MOU/NDA/surat izin), HR | Mereka **draf dokumen** dan **prediksi satu-shot**; kami melacak **proses berurutan** (NIB→SPP-IRT→Halal) dengan status per pengguna dan tenggat hukum spesifik — beda kategori kemampuan, bukan cuma beda kedalaman |
| **Navigo** (UI, akademik) | Asisten hukum AI untuk kreator/UMKM | Tampak proyek riset kampus, belum produk publik berjalan |
| **Legalku, SAH.co.id** | Marketplace jasa legalitas manual | Status quo yang dibandingkan pengguna — lebih lambat, berbayar per jasa |
| **Feedloop LegalPro** | AI kepatuhan untuk tim legal korporat | Segmen pelanggan berbeda total (korporat vs. UMKM tanpa literasi hukum) |

**Kejujuran yang perlu disampaikan ke juri:** kategori "AI + UMKM Indonesia" sudah mulai ramai. Argumen yang bertahan: "kami sempit tapi dalam di satu proses spesifik (kepatuhan berurutan + memori bisnis), mereka lebar tapi dangkal di proses itu." Ini hanya kredibel kalau demo membuktikannya pada kasus yang sulit.

**Aksi wajib sebelum Preliminary Round selesai:** daftar akun UMKM.AI dan uji langsung dengan pertanyaan urutan izin yang sama persis dengan skenario Persona 5.

---

## 7. Model Bisnis

| Tingkat | Fitur | Catatan |
|---|---|---|
| **Free** | 5–10 kueri/hari, info regulasi umum, tanpa profil tersimpan | Validasi awal, bukan retensi |
| **Pro** | Kueri tanpa batas, business memory lintas sesi, checklist kepatuhan dengan tracking, laporan kesiapan legalitas (PDF) | Laporan bisa dipakai sebagai lampiran pengajuan KUR atau pendaftaran mitra marketplace |
| **Enterprise** | API/dashboard untuk bank, koperasi, dinas pemerintah | Bank: pra-skrining due diligence KUR. Koperasi: layanan tambahan anggota. Dinas: KPI pemantauan kepatuhan UMKM binaan |

Harga Pro (hipotesis, perlu validasi): Rp29.000–49.000/bulan — **harus diuji lewat wawancara, bukan diasumsikan dari biaya hosting saja.**

---

## 8. Validasi Bisnis

| Asumsi | Pertanyaan wawancara | Data sekunder (triangulasi, bukan bukti final) |
|---|---|---|
| UMKM sulit paham regulasi | "Bagaimana cara Anda cari tahu aturan usaha sekarang? Pernah salah langkah karena salah paham aturan?" | ~5,8% UMKM punya NIB (2023); 77,5% tanpa pembukuan teratur |
| UMKM mau pakai AI sebelum buka usaha | "Di titik mana Anda mulai memakai asisten seperti ini — sebelum mulai usaha, atau setelah ada masalah?" | ~22% UMKM terdigitalisasi (BCG/KADIN) |
| UMKM mau membayar | "Berapa yang biasa/bersedia dikeluarkan untuk konsultasi izin/riset pasar? Rp30–50rb/bulan wajar?" | ~20% UMKM punya akses kredit formal (BI) — sinyal sensitivitas harga tinggi |

**Minimal 5–10 wawancara**, campuran Persona 1 (pre-launch) dan Persona 5 (berjalan, belum legal lengkap). **Jadwalkan minggu ini**, paralel dengan build.

---

## 9. Penegasan Scope MVP (In-Scope vs Out-Scope)

Agar arah pengembangan jelas dalam batas waktu 3 minggu, MVP ini secara ketat membagi apa yang **dibangun** dan yang **ditinggalkan**.

### ✅ IN-SCOPE (Wajib Ada untuk Demo MVP)
| Fitur / Modul | Deskripsi Implementasi |
|---|---|
| **Chat Tunggal (Next.js)** | UI Chat 2 arah (Fase Klarifikasi natural) + *Consolidated Report* dalam bentuk **Bento Grid** interaktif yang di-update dinamis oleh AI Agent. |
| **Agent Orchestrator (FastAPI)** | Jantung AI. Memiliki fungsi RAG (Qdrant) untuk regulasi dan *Web Search Fan-out* untuk riset/harga kompetitor. |
| **Checklist Regulasi F&B** | *Fitur Pendukung Kritis*. Memandu *user* mengurus NIB -> SPP-IRT -> Halal tanpa halusinasi (*JSON Railway Pattern*) jika bisnisnya tergolong F&B. |
| **Rekomendasi Harga Jual** | *Pricing strategy* berdasar modal vs pasar saat ini (bukan tebak-tebakan masa depan). |
| **Profile Persistence** | Menyimpan profil bisnis *user* secara persisten lintas-sesi (Modal, Kategori, Status Izin). *Di-mock via state lokal pada V1, dan bermigrasi ke database SQLite pada V2.* |

### ❌ OUT-SCOPE (Kill Your Darlings - Sengaja Dibuang)
| Sengaja TIDAK dibangun | Alasan (Buat Juri) |
|---|---|
| Dashboard Analytics (Grafik Kompleks) | Terlalu berat dibangun dari nol; kita buktikan nilai lewat laporan *chat* konsolidasi. |
| Forecasting Harga Jangka Panjang | Murni menebak masa depan berisiko tinggi halusinasi, keluar dari *scope* 3-call arsitektur. |
| Notifikasi Otomatis (Email/WA) | *Rulebook* membatasi ke sistem web *synchronous*, notifikasi melanggar ini. |
| Aplikasi Mobile (Android/iOS) | Waktu tidak cukup; *Responsive Web App* Next.js sudah sangat memadai. |
| Regulasi luar Sektor F&B Pangan | Kita kejar *depth* (akurasi 100% untuk urgensi Halal 2026), bukan *breadth* (lebar tapi dangkal). |

Prinsip Utama: **Jangan bangun fitur yang tidak secara langsung menaikkan bobot penilaian juri atau mengurangi nilai compliance.**

---

## 10. Pembagian Peran Tim & Timeline

### Pembagian Peran (3 Anggota)

| Member | Fokus Utama | Tanggung Jawab Konkret |
|---|---|---|
| **Gilang** | Frontend, Backend (API), Prompts | Next.js UI/UX, layout output laporan Bento Grid (Agent-edited), FastAPI routes, prompt engineering |
| **Arya** | AI, Data, Infrastruktur | Kurasi `regulatory_rules.json`, dataset 1000 entri, QLoRA fine-tuning, deploy HF, Qdrant seeding, Docker setup, evaluasi model |
| **Adillah** | Bisnis, Deliverables, Validasi | Pembuatan proposal 20 halaman, produksi 2 video (Proof of Work & Promo), wawancara validasi bisnis, dokumentasi README |

*Catatan: Peran Adillah sangat kritis karena evaluasi Juri pada dokumen proposal dan video memiliki bobot gabungan sebesar 30%. Kesalahan data di regulasi juga bisa berakibat fatal pada kualitas output.*

### Roadmap Rilis & Fase Eksekusi

**V1: Tahap Penyisihan (MVP Inti) — Deadline 25 Agustus 2026**
Fokus utama: Menembus final dengan memamerkan *core engine* tanpa terbebani infrastruktur *database* berat.
- **Gilang:** Setup Next.js + FastAPI. Kembangkan UI Chat dengan output Bento Grid Artifact dan logika *Agent Orchestrator* yang mengupdate UI secara dinamis. Fitur *Profile Persistence* di-**MOCK** menggunakan *memory/state* lokal (hilang saat di-*refresh*).
- **Arya:** Kurasi `regulatory_rules.json`, susun dataset 1.000 entri (termasuk 15% *chit-chat*), *training* QLoRA, dan *ingest* ke Qdrant.
- **Adillah:** Draf kerangka proposal 20 halaman, rekam video *Proof of Work* (demo V1), dan *submit* berkas.

**V2: Tahap Finalis (Live Hackathon & Pitching) — 26 & 27 September 2026**
Fokus utama: Implementasi *database* sungguhan untuk memukau juri saat demo *live* dan sesi Hackathon *offline* 10 jam.
- **Gilang (Saat Hackathon 10 Jam):** Migrasi *Mock Profile* ke **SQLite** sesungguhnya. Tambahkan fitur UI *Mini Dashboard Evaluasi Bulanan* (Persona 6).
- **Arya:** *Tuning* ulang model berdasarkan hasil eval V1, perbaikan latensi pencarian Qdrant.
- **Adillah:** Menyusun bahan presentasi untuk *Live Pitching*, menekankan transisi sistem ke *database* permanen tingkat produksi.

**V3: Lanjutan Pasca-Lomba (Scale Up)**
- Implementasi daftar *Out-Scope*: Aplikasi Mobile Terpisah, Sistem Notifikasi Otomatis, dan ekspansi ke regulasi di luar sektor F&B.

---

## Referensi

*   COMPFEST 18 AIC — jadwal & hadiah: compfest.id/competition/aic
*   DJP — PP 20/2026, tarif PPh Final 0,5%: pajak.go.id/en/node/119950, /119954
*   Ortax — WP OP & PT Perorangan tanpa batas waktu: ortax.org
*   CNBC Indonesia — aturan PPh Final direvisi, CV/PT tak masuk kriteria: cnbcindonesia.com
*   OSS RBA — panduan NIB: oss.go.id
*   BPJPH — kriteria SEHATI 2026 & tenggat Halal: bpjph.halal.go.id
*   IZIN.co.id — panduan SPP-IRT/PIRT 2026 (PerBPOM 4/2024)
*   RM.id — data 67 juta UMKM & skema KUR
*   Insimen — tingkat kegagalan UMKM, data KADIN 74% & NIB 5,8%
*   IPIS UI — Navigo: ipis.ui.ac.id
*   **UMKM.AI — situs resmi (diakses 11 Juli 2026): umkm.ai** — konfirmasi langsung cakupan produk (prediksi pasar, kompetitor, dokumen hukum, HR)
*   Bisnis.com — daftar startup legaltech (Legalku, SAH.co.id)
*   Viva.co.id — Feedloop AI LegalPro
*   **Wayfinder (tim, lablab.ai/Bright Data "Web Data UNLOCKED" Hackathon, Mei 2026)** — rujukan desain untuk prinsip "satu laporan konsolidasi"

*Catatan: regulasi berubah — dibuktikan dokumen ini sendiri lewat kasus PP 20/2026 — informasi di atas adalah titik awal riset, bukan pengganti konsultasi resmi ke DJP/OSS/BPJPH/konsultan berlisensi.*
