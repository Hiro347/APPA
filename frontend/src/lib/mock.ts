import { PipelineGroup, PipelineStep, Artifact, UserProfile } from './types';

export const MOCK_PROFILE: UserProfile = {
  compliance_status: [
    { item: 'NIB', status: 'not_started' },
    { item: 'SPP-IRT', status: 'not_started' },
    { item: 'Sertifikat Halal', status: 'not_started' },
  ],
};

export function getProductKeyword(message: string): string {
  const lowercase = message.toLowerCase();
  if (lowercase.includes('keripik singkong')) return 'keripik singkong';
  if (lowercase.includes('keripik')) return 'keripik';
  if (lowercase.includes('bakso')) return 'bakso';
  if (lowercase.includes('kopi')) return 'kopi';
  return 'produk';
}

export function createPipelineGroups(message: string): PipelineGroup[] {
  const isDeep = message.length > 20;
  const keyword = getProductKeyword(message);

  const groups: PipelineGroup[] = [
    {
      id: 'decompose', icon: '', label: 'Dekomposisi Query',
      steps: [
        { id: 'd1', label: 'Ekstraksi entitas dari pesan', status: 'waiting' },
        { id: 'd2', label: `Generate search queries untuk '${keyword}'`, status: 'waiting' },
        { id: 'd3', label: 'Routing & klasifikasi intent', status: 'waiting' },
      ],
    },
  ];
  if (isDeep) {
    groups.push(
      {
        id: 'search', icon: '', label: 'Pencarian Data Pasar & Regulasi',
        steps: [
          { id: 's1', label: `Google Search: 'regulasi perizinan ${keyword}'`, status: 'waiting' },
          { id: 's2', label: `Google Search: 'harga pasaran ${keyword}'`, status: 'waiting' },
          { id: 's3', label: `Google Shopping: '${keyword}'`, status: 'waiting' },
        ],
      },
      {
        id: 'process', icon: '', label: 'Pemrosesan Data',
        steps: [
          { id: 'p1', label: 'Kondensasi hasil scraping ke JSON', status: 'waiting' },
          { id: 'p2', label: 'Validasi data dengan Pydantic', status: 'waiting' },
        ],
      },
      {
        id: 'regulation', icon: '', label: 'Pengecekan Regulasi',
        steps: [
          { id: 'r1', label: `Qdrant RAG: query regulasi ${keyword}`, status: 'waiting' },
          { id: 'r2', label: 'Matching: regulatory_rules.json', status: 'waiting' },
        ],
      },
    );
  }
  groups.push({
    id: 'synthesis', icon: '', label: 'Sintesis Laporan',
    steps: [{ id: 'syn1', label: 'Menyusun respons akhir', status: 'waiting' }],
  });
  return groups;
}

function getAllSteps(groups: PipelineGroup[]): PipelineStep[] {
  return groups.flatMap(g => g.steps);
}

function updateStep(groups: PipelineGroup[], stepId: string, status: PipelineStep['status']): PipelineGroup[] {
  return groups.map(g => ({
    ...g,
    steps: g.steps.map(s => s.id === stepId ? { ...s, status } : s),
  }));
}

const MOCK_RESPONSE_SHORT = 'Halo! Saya APPA, asisten analisa pasar dan regulasi Anda. Ceritakan tentang bisnis yang ingin Anda jalankan, dan saya akan bantu riset pasar serta cek kebutuhan perizinannya.';

const MOCK_RESPONSE_LONG = `Berdasarkan analisa yang saya lakukan, berikut adalah ringkasan untuk bisnis keripik singkong Anda:

**Analisa Harga Pasar:**
Harga keripik singkong di marketplace berkisar antara Rp8.000 - Rp15.000 per 200g. Dengan modal HPP Rp5.000, margin yang sehat berada di kisaran Rp10.000 per unit.

**Status Perizinan:**
Untuk bisnis F&B olahan rumahan dengan risiko rendah, Anda perlu mengurus NIB (Nomor Induk Berusaha) terlebih dahulu, lalu SPP-IRT dari Dinas Kesehatan setempat.

Saya sudah membuat dashboard harga dan checklist perizinan untuk Anda. Silakan lihat tab di atas.`;

export interface MockCallbacks {
  onPipelineUpdate: (groups: PipelineGroup[]) => void;
  onStreamChar: (char: string) => void;
  onPipelineComplete: () => void;
  onArtifacts: (artifacts: Artifact[]) => void;
  onDone: () => void;
}

export function simulateResponse(message: string, cb: MockCallbacks): () => void {
  const isDeep = message.length > 20;
  const keyword = getProductKeyword(message);
  let groups = createPipelineGroups(message);
  const response = isDeep ? MOCK_RESPONSE_LONG : MOCK_RESPONSE_SHORT;
  const timeouts: ReturnType<typeof setTimeout>[] = [];
  let cancelled = false;

  const update = (stepId: string, status: PipelineStep['status']) => {
    if (cancelled) return;
    groups = updateStep(groups, stepId, status);
    cb.onPipelineUpdate(groups);
  };

  // Structured pipeline events
  const timeline: { time: number; action: () => void }[] = [];

  // Group 1: Decompose (Sequential)
  timeline.push(
    { time: 0, action: () => update('d1', 'running') },
    { time: 300, action: () => { update('d1', 'done'); update('d2', 'running'); } },
    { time: 600, action: () => { update('d2', 'done'); update('d3', 'running'); } },
    { time: 900, action: () => { update('d3', 'done'); } }
  );

  if (isDeep) {
    // Group 2: Search (Parallel)
    timeline.push(
      { time: 900, action: () => {
        update('s1', 'running');
        update('s2', 'running');
        update('s3', 'running');
      }},
      { time: 1300, action: () => update('s1', 'done') },
      { time: 1550, action: () => update('s2', 'done') },
      { time: 1800, action: () => update('s3', 'done') }
    );

    // Group 3: Process (Sequential)
    timeline.push(
      { time: 1800, action: () => update('p1', 'running') },
      { time: 2150, action: () => { update('p1', 'done'); update('p2', 'running'); } },
      { time: 2500, action: () => update('p2', 'done') }
    );

    // Group 4: Regulation (Sequential)
    timeline.push(
      { time: 2500, action: () => update('r1', 'running') },
      { time: 2900, action: () => { update('r1', 'done'); update('r2', 'running'); } },
      { time: 3200, action: () => update('r2', 'done') }
    );

    // Group 5: Synthesis
    timeline.push(
      { time: 3200, action: () => update('syn1', 'running') },
      { time: 3500, action: () => update('syn1', 'done') }
    );
  } else {
    // Non-deep synthesis starts right after decomposition
    timeline.push(
      { time: 900, action: () => update('syn1', 'running') },
      { time: 1200, action: () => update('syn1', 'done') }
    );
  }

  // Schedule timeline events
  timeline.forEach((event) => {
    timeouts.push(setTimeout(() => {
      if (cancelled) return;
      event.action();

      // Trigger completion and text streaming after the last pipeline step is done
      const lastTime = isDeep ? 3500 : 1200;
      if (event.time === lastTime) {
        cb.onPipelineComplete();

        // Stream text
        let charIdx = 0;
        const streamInterval = setInterval(() => {
          if (cancelled) { clearInterval(streamInterval); return; }
          if (charIdx < response.length) {
            cb.onStreamChar(response[charIdx]);
            charIdx++;
          } else {
            clearInterval(streamInterval);
            if (isDeep) {
              cb.onArtifacts([
                {
                  id: `artifact-consolidated-${Date.now()}`,
                  title: `Laporan Kelayakan Usaha ${keyword.charAt(0).toUpperCase() + keyword.slice(1)}`,
                  sources: ['Google Shopping', 'Tokopedia', 'Shopee', 'OSS Indonesia', 'PP 28/2025'],
                  blocks: [
                    {
                      type: 'text',
                      content: `### Ringkasan Eksekutif\nAnalisis kelayakan usaha komoditas **${keyword}** di pasar lokal. Dokumen ini merangkum struktur modal, pembanding harga pasar, kebutuhan izin edar, dan simulasi pendapatan.`,
                      sources: ['Analisis RAG APPA']
                    },
                    {
                      type: 'metric',
                      data: { hpp: 5000, market_avg: 12000, recommendation: 10000 },
                      sources: ['Tokopedia', 'Shopee']
                    },
                    {
                      type: 'chart',
                      data: {
                        xAxis: ['Tokopedia', 'Shopee', 'Rekomendasi'],
                        yAxis: [12000, 11500, 10000],
                        label: 'Analisis Komparasi Harga Jual'
                      },
                      sources: ['Google Shopping']
                    },
                    {
                      type: 'checklist',
                      data: {
                        items: [
                          { title: 'NIB (Nomor Induk Berusaha)', status: 'wajib', description: 'Daftar melalui Online Single Submission (OSS)' },
                          { title: 'SPP-IRT (Sertifikat Produksi Pangan Industri Rumah Tangga)', status: 'wajib', description: 'Pengajuan via SPPIRT BPOM / Dinas Kesehatan' },
                          { title: 'Sertifikat Halal (Self-Declare)', status: 'opsional', description: 'Daftar melalui BPJPH Kemenag' }
                        ]
                      },
                      sources: ['OSS Indonesia', 'PP 28/2025']
                    },
                    {
                      type: 'table',
                      data: {
                        headers: ['Skenario Penjualan', 'Volume Harian', 'Revenue Bulanan', 'Net Profit (Est)'],
                        rows: [
                          ['Konservatif', '50 Unit', 'Rp15.000.000', 'Rp7.500.000'],
                          ['Moderat', '100 Unit', 'Rp30.000.000', 'Rp15.000.000'],
                          ['Optimis', '200 Unit', 'Rp60.000.000', 'Rp30.000.000']
                        ]
                      },
                      sources: ['Proyeksi Pasar APPA']
                    }
                  ]
                }
              ]);
            }
            cb.onDone();
          }
        }, 15);
        timeouts.push(streamInterval as unknown as ReturnType<typeof setTimeout>);
      }
    }, event.time));
  });

  return () => { cancelled = true; timeouts.forEach(clearTimeout); };
}
