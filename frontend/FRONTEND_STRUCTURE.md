# APPA Frontend Structure Plan

## Layout Overview

```
┌──────────────────────────────────────────────────────────┐
│  [ Profile Sidebar ]  │  [ Chat Tab ] [ Artifact Tab 1 ] │
│                       │──────────────────────────────────│
│  Nama Usaha           │                                  │
│  Kategori: F&B Mikro  │   (Active Tab Content Area)      │
│  Modal: Rp 5.000      │                                  │
│                       │   - Chat view (default)          │
│  ── Status Izin ──    │   - OR Artifact view (on click)  │
│  NIB      ✅          │                                  │
│  SPP-IRT  ❌          │                                  │
│  Halal    ❌          │──────────────────────────────────│
│                       │  [ Chat Input ]                  │
└──────────────────────────────────────────────────────────┘
```

---

## 1. Profile Sidebar (Left)

Sidebar kiri menampilkan **mock profile** secara read-only.
- Tipe bisnis, kategori produk, modal/HPP.
- Indikator status compliance (NIB ✅, SPP-IRT ❌, Halal ❌).
- **Ini hanya untuk demo MVP** — nanti akan diganti dengan halaman profil bisnis yang proper.
- Data di-update secara implisit dari hasil ekstraksi LLM di chat (tidak ada tombol edit).

---

## 2. Tab System (Top)

Tab bar di atas area konten utama. Sistem tab mengontrol apa yang ditampilkan di area konten.

- **Tab "Chat"** — Tab pertama, selalu ada, tidak bisa ditutup. Ini adalah tampilan utama obrolan.
- **Tab Artifact** — Dibuat secara dinamis oleh AI setelah menghasilkan laporan kelayakan bisnis terintegrasi. Setiap artifact mendapat tab sendiri yang tidak bisa ditutup.
- **Klik tab artifact → menggantikan tampilan chat** dengan bento grid layout yang berisi subkomponen analisis terintegrasi.
- Klik kembali ke tab Chat → kembali ke tampilan obrolan.

---

## 3. Chat View (Main Tab Content)

### 3a. Initial State (Belum ada pesan)
- **Input chat posisinya di tengah layar** (centered, seperti ChatGPT/Claude saat pertama buka).
- Bisa ada greeting text atau branding singkat di atas input.

### 3b. Active State (Sudah ada pesan)
- **Input chat transisi ke bawah layar** setelah pesan pertama dikirim.
- History pesan ditampilkan di atas, scroll otomatis ke pesan terbaru.

### 3c. Streaming Text
- Respons AI harus **streaming** (teks muncul secara bertahap, bukan sekaligus).
- Mirip seperti ChatGPT/Claude — karakter/kata muncul satu per satu.

### 3d. AI Thinking Display (WAJIB)
- Sebelum AI mulai menjawab, tampilkan **indikator "sedang berpikir"**.
- Bisa berupa collapsible section yang menunjukkan proses internal AI.
- Contoh: "Menganalisa konteks bisnis Anda..." → "Menentukan rute pencarian..."

### 3e. Research Pipeline Transparency (200% Transparency)
- Ketika backend menjalankan *research pipeline*, GUI **HARUS** mencerminkan setiap langkah yang sedang dilakukan AI secara real-time.
- Setiap tahapan pipeline ditampilkan dengan status yang jelas.
- **Contoh alur yang harus terlihat di GUI:**

  ```
  🔍 Dekomposisi Query
     ├─ ✅ Ekstraksi entitas: "keripik singkong", modal 5jt
     ├─ ✅ Generate search queries (3 queries)
     └─ ✅ Routing: market_research + compliance_check

  🌐 Pencarian Data Pasar
     ├─ ✅ Google Search: "harga keripik singkong grosir 2026"
     ├─ 🔄 Scraping: tokopedia.com/keripik-singkong...
     ├─ ⏳ Scraping: shopee.co.id/...
     └─ ⏳ Scraping: bfrbs.go.id/harga-pangan/...

  📊 Pemrosesan Data
     ├─ ⏳ Kondensasi hasil scraping → JSON fakta
     └─ ⏳ Validasi data dengan Pydantic

  📋 Pengecekan Regulasi
     ├─ ⏳ Qdrant RAG: query regulasi F&B
     └─ ⏳ Matching: regulatory_rules.json

  🧠 Sintesis Laporan
     └─ ⏳ Menunggu data...
  ```

- Status per item: `⏳ Menunggu` → `🔄 Sedang berjalan` → `✅ Selesai` → `❌ Gagal`
- **Ini HARUS mencerminkan PERSIS apa yang AI lakukan di backend pipeline. Tidak ada yang disembunyikan.**

---

## 4. Artifact System (Claude-style)

Artifact = **dokumen fleksibel yang dibuat oleh AI**, bukan tipe komponen rigid.

### Prinsip

- **AI yang menentukan** apa isinya dan bagaimana menyajikannya. Tidak ada template kaku.
- **Dipisahkan berdasarkan concern/topik**, bukan berdasarkan tipe komponen. Contoh:
  - "Analisa Harga Keripik Singkong" → berisi teks narasi + tabel perbandingan harga + chart tren, semua dalam satu bento grid artifact.
  - "Roadmap Perizinan F&B" → berisi checklist + penjelasan tiap langkah + timeline.
- **Satu artifact = satu halaman konten** yang mengandung kombinasi blok-blok visual (teks, tabel, chart, checklist, dsb).
- **Di-edit oleh AI Agent**, bukan oleh user. User tidak dapat mengedit isi/angka di dalam blok secara manual; pembaruan data dilakukan oleh AI Agent secara dinamis melalui chat.
- **Dipakai sebagai konteks** untuk percakapan selanjutnya. AI merujuk atau meng-update artifact yang sudah ada berdasarkan follow-up chat.
- Artifact yang sudah ada bisa **di-update** oleh AI tanpa membuat tab baru (jika concern-nya sama).

### Blok Konten (Building Blocks dalam 1 Artifact)

Satu artifact bisa mengandung kombinasi blok-blok berikut:

| Blok | Deskripsi |
|---|---|
| `text` | Paragraf, heading, markdown narasi |
| `table` | Tabel data (harga, perbandingan) |
| `checklist` | Daftar tugas/langkah dengan status |
| `chart` | Visualisasi data (bar, line) |
| `metric` | Angka/KPI besar (HPP, rekomendasi harga) |
| `callout` | Highlight/peringatan penting |

### Contoh Artifact: "Analisa Pasar Keripik Singkong"

```
┌─────────────────────────────────────────┐
│  Analisa Pasar Keripik Singkong         │
│─────────────────────────────────────────│
│                                         │
│  [metric] HPP: Rp5.000                  │
│  Sumber: Tokopedia                      │
│                                         │
│  [text] Berdasarkan data dari 3         │
│  marketplace, harga keripik singkong... │
│  Sumber: Analisis RAG APPA              │
│                                         │
│  [chart] Perbandingan Harga per         │
│  Platform (bar chart)                   │
│  Sumber: Google Shopping                │
│                                         │
└─────────────────────────────────────────┘
```

### Interaksi

- Klik tab artifact → mengganti tampilan chat dengan konten artifact.
- User tidak dapat mengedit isi blok secara manual; pembaruan data/status dilakukan oleh AI Agent secara dinamis melalui chat.
- Follow-up chat bisa merujuk artifact: "Update artifact harga, tambahkan data dari Shopee."
- Setiap subkomponen/blok memiliki sitasi **sumber data** masing-masing di bagian bawah card.

---

## 5. Component Tree (Planned)

```
app/
├── layout.tsx                  # Root layout, fonts, metadata
├── page.tsx                    # Orchestrator: sidebar + tab system + content area
│
├── components/
│   ├── layout/
│   │   ├── ProfileSidebar.tsx  # Mock profile (left)
│   │   └── TabBar.tsx          # Tab system (chat + artifact tabs)
│   │
│   ├── chat/
│   │   ├── ChatView.tsx        # Chat container (initial centered → bottom input)
│   │   ├── MessageBubble.tsx   # Single message (user vs assistant)
│   │   ├── ChatInput.tsx       # Text input + send button
│   │   └── ThinkingDisplay.tsx # AI thinking + pipeline status visualization
│   │
│   ├── artifacts/
│   │   └── ArtifactView.tsx    # Renders an artifact (mixed content blocks inside a bento grid)
│   │
│   └── hooks/
│       └── useChat.ts          # Chat state, message history, sliding window
│
├── lib/
│   ├── api.ts                  # Fetch wrappers (POST /chat, GET /profile)
│   └── types.ts                # Shared TypeScript interfaces
│
└── styles/
    └── globals.css
```

---

## 6. Design System — Monotone Light Theme

Filosofi: **Bersih, tenang, profesional.** Satu keluarga warna (gray/slate), minim distraksi, konten berbicara sendiri.

### Color Palette (Monotone)

| Token | Hex | Penggunaan |
|---|---|---|
| `--bg-primary` | `#FFFFFF` | Background utama (chat area, artifact view) |
| `--bg-secondary` | `#F8F9FA` | Sidebar, card backgrounds |
| `--bg-tertiary` | `#F1F3F5` | Hover states, alt rows |
| `--border` | `#E9ECEF` | Semua border & divider |
| `--text-primary` | `#212529` | Heading, body text utama |
| `--text-secondary` | `#6C757D` | Label, caption, placeholder |
| `--text-tertiary` | `#ADB5BD` | Hint, disabled text |
| `--accent` | `#343A40` | Tombol utama, link, active tab indicator |
| `--accent-hover` | `#495057` | Hover pada tombol/link |
| `--success` | `#40C057` | Status ✅ (satu-satunya warna non-gray yang boleh) |
| `--error` | `#FA5252` | Status ❌ |
| `--warning` | `#FD7E14` | Status 🔄 / pending |

> Aturan: **Tidak ada warna brand yang mencolok.** Semua UI menggunakan skala abu-abu. Warna hijau/merah/oranye HANYA untuk indikator status.

### Typography

- **Font:** `Geist Sans` (sudah ter-install dari Next.js scaffold) atau `Inter` sebagai fallback.
- **Heading:** `font-semibold`, bukan bold yang terlalu tebal.
- **Body:** `text-sm` (14px) sebagai default. `text-xs` (12px) untuk label/caption.
- **Spacing:** Generous whitespace. Jangan padatkan elemen.

### Component Styling Guidelines

- **Cards / Containers:** `bg-white`, `border border-gray-200`, `rounded-lg`. Tidak ada shadow kecuali hover.
- **Tabs:** Underline style (bukan pill/box). Active tab = `border-b-2 border-gray-900`. Inactive = `text-gray-400`.
- **Buttons:** Solid `bg-gray-900 text-white` untuk primary. Ghost `text-gray-600 hover:bg-gray-100` untuk secondary.
- **Chat bubbles:** User = `bg-gray-100 text-gray-900`. AI = tanpa background, teks langsung (clean, tanpa bubble).
- **Input:** `border border-gray-200 rounded-xl`, fokus = `ring-1 ring-gray-400`. Simpel.
- **Pipeline status:** Monospaced font (`font-mono`), tampilan tree-view. Status icons pakai warna sesuai token di atas.
- **Sidebar:** `bg-gray-50`, border kanan `border-r border-gray-200`.
- **Transitions:** `transition-all duration-200 ease-in-out`. Halus tapi cepat, tidak berlebihan.

### Prinsip

1. **Flat** — Tidak ada gradien, tidak ada shadow yang berlebihan.
2. **Content-first** — UI tidak boleh lebih menarik dari data yang ditampilkan.
3. **Whitespace is king** — Beri ruang napas antar elemen.
4. **Konsisten** — Semua radius `rounded-lg`, semua border `border-gray-200`, semua spacing kelipatan 4px.

---

## 7. Backend Contract Notes (untuk sinkronisasi)

Agar pipeline transparency bekerja, backend (FastAPI) perlu mengirim **status updates** secara real-time. Opsi:
1. **Server-Sent Events (SSE)** — Backend stream status per-step ke frontend.
2. **WebSocket** — Koneksi dua arah untuk status + streaming text.
3. **Polling** — Frontend poll status endpoint (kurang ideal tapi paling simpel).

> ⚠️ Ini perlu dikoordinasikan dengan Arya untuk backend implementation.

---

*Silakan edit dan tambahkan detail lebih lanjut.*
