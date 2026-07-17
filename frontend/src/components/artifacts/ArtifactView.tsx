'use client';

import { Artifact, ArtifactBlock, TextBlock, MetricBlock, ChecklistBlock, ChartBlock, TableBlock } from '@/lib/types';
import { CheckCircle2, Circle, BarChart3, Info } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export function ArtifactView({
  artifact,
  onUpdate
}: {
  artifact: Artifact;
  onUpdate: (blocks: ArtifactBlock[]) => void;
}) {
  const handleToggleChecklist = (blockIndex: number, itemIndex: number) => {
    const nextBlocks = [...artifact.blocks];
    const block = nextBlocks[blockIndex];
    if (block.type === 'checklist') {
      const nextItems = [...block.data.items];
      const currentStatus = nextItems[itemIndex].status;
      nextItems[itemIndex] = {
        ...nextItems[itemIndex],
        status: currentStatus === 'done' ? 'pending' : 'done'
      };
      nextBlocks[blockIndex] = {
        ...block,
        data: { items: nextItems }
      };
      onUpdate(nextBlocks);
    }
  };

  const getBlockSpanClass = (block: ArtifactBlock) => {
    if (block.type === 'table') return 'w-full';
    if (block.type === 'text') return 'w-full lg:flex-1 lg:basis-[600px] min-w-[300px]';
    if (block.type === 'chart') return 'w-full lg:flex-1 lg:basis-[500px] min-w-[300px]';
    if (block.type === 'metric') return 'w-full md:flex-1 md:basis-[300px] min-w-[250px]';
    if (block.type === 'checklist') return 'w-full md:flex-1 md:basis-[300px] min-w-[250px]';
    return 'w-full';
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-white overflow-y-auto">
      {/* Header */}
      <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-gray-50/50 shrink-0">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-gray-400">Analisa Terkonsolidasi</span>
          <h2 className="text-xl font-semibold text-gray-900 mt-0.5">{artifact.title}</h2>
        </div>
      </div>

      {/* Content blocks (Bento Grid) */}
      <div className="p-8 max-w-6xl mx-auto w-full flex flex-wrap gap-4 flex-1 content-start items-stretch">
        {artifact.blocks.map((block, index) => {
          const spanClass = getBlockSpanClass(block);

          return (
            <div key={index} className={`relative group border border-gray-100 rounded-lg p-6 bg-white shadow-sm flex flex-col justify-between ${spanClass}`}>
              {/* Render Block by Type */}
              <div className="flex-1">
                {block.type === 'text' && (
                  <TextBlockRenderer block={block} />
                )}

                {block.type === 'metric' && (
                  <MetricBlockRenderer block={block} />
                )}

                {block.type === 'chart' && (
                  <ChartBlockRenderer block={block} />
                )}

                {block.type === 'checklist' && (
                  <ChecklistBlockRenderer
                    block={block}
                    onToggle={(itemIdx) => handleToggleChecklist(index, itemIdx)}
                  />
                )}

                {block.type === 'table' && (
                  <TableBlockRenderer block={block} />
                )}
              </div>

              {/* Dedicated Sources at bottom of block */}
              {block.sources && block.sources.length > 0 && (
                <div className="flex items-center gap-1.5 mt-4 text-[10px] text-gray-400 shrink-0">
                  <Info size={11} className="text-gray-400" />
                  <span>Sumber: {block.sources.join(', ')}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TextBlockRenderer({ block }: { block: TextBlock }) {
  return (
    <div className="prose prose-sm max-w-none text-gray-800 leading-relaxed">
      <ReactMarkdown
        components={{
          h1: ({ children }) => <h1 className="text-lg font-bold text-gray-950 mb-2">{children}</h1>,
          h2: ({ children }) => <h2 className="text-base font-semibold text-gray-950 mb-2">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-semibold text-gray-900 mb-1.5">{children}</h3>,
          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
        }}
      >
        {block.content}
      </ReactMarkdown>
    </div>
  );
}

function MetricBlockRenderer({ block }: { block: MetricBlock }) {
  const hpp = block.data.hpp || 0;
  const market_avg = block.data.market_avg || 0;
  const recommendation = block.data.recommendation || 0;

  const margin = recommendation - hpp;
  const marginPct = recommendation > 0
    ? Math.round((margin / recommendation) * 100)
    : 0;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="p-4 rounded-md border border-gray-100 bg-gray-50/50">
          <p className="text-[10px] uppercase tracking-wider text-gray-400 mb-0.5">Modal HPP</p>
          <p className="text-xl font-bold text-gray-900">Rp{hpp.toLocaleString()}</p>
        </div>
        <div className="p-4 rounded-md border border-gray-100 bg-gray-50/50">
          <p className="text-[10px] uppercase tracking-wider text-gray-400 mb-0.5">Rata-rata Pasar</p>
          <p className="text-xl font-bold text-gray-900">Rp{market_avg.toLocaleString()}</p>
        </div>
      </div>
      <div className="p-4 rounded-md border border-gray-905 bg-white">
        <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-0.5">Rekomendasi Harga Jual</p>
        <p className="text-2xl font-black text-gray-900">Rp{recommendation.toLocaleString()}</p>
        <p className="text-xs text-gray-500 mt-1 font-medium">Margin: Rp{margin.toLocaleString()} ({marginPct}%)</p>
      </div>
    </div>
  );
}

function ChartBlockRenderer({ block }: { block: ChartBlock }) {
  const chartData = block.data.xAxis.map((x, i) => ({ name: x, value: block.data.yAxis[i] }));
  const isLine = block.data.chartType === 'line';

  return (
    <div className="flex flex-col flex-1 h-full justify-between">
      <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-1.5 shrink-0">
        <BarChart3 size={15} /> {block.data.label || 'Perbandingan Harga'}
      </h3>
      <div className="flex-1 min-h-[220px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {isLine ? (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#9ca3af' }} angle={-25} textAnchor="end" height={50} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#9ca3af' }} width={55} tickFormatter={(v) => `Rp${(v/1000).toFixed(0)}k`} />
              <Tooltip
                cursor={{ stroke: '#d1d5db', strokeDasharray: '4 4' }}
                contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: 'none', fontSize: '11px' }}
                formatter={(value) => [`Rp${Number(value).toLocaleString()}`, 'Harga']}
              />
              <Line type="monotone" dataKey="value" stroke="#111827" strokeWidth={2} dot={{ r: 4, fill: '#111827' }} activeDot={{ r: 6 }} />
            </LineChart>
          ) : (
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#9ca3af' }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#9ca3af' }} width={45} />
              <Tooltip
                cursor={{ fill: '#f9fafb' }}
                contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: 'none', fontSize: '11px' }}
              />
              <Bar dataKey="value" fill="#111827" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ChecklistBlockRenderer({
  block,
  onToggle
}: {
  block: ChecklistBlock;
  onToggle: (index: number) => void;
}) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-900 mb-2">Checklist Regulasi & Izin</h3>
      <div className="space-y-2">
        {block.data.items.map((item, idx) => {
          const isDone = item.status === 'done';
          return (
            <div
              key={idx}
              onClick={() => onToggle(idx)}
              className="flex items-start gap-3 p-3 rounded-md border border-gray-100 bg-white hover:border-gray-300 transition-colors cursor-pointer select-none"
            >
              {isDone ? (
                <CheckCircle2 size={16} className="text-green-600 mt-0.5 shrink-0" />
              ) : (
                <Circle size={16} className="text-gray-300 mt-0.5 shrink-0" />
              )}
              <div>
                <p className={`text-xs font-semibold ${isDone ? 'text-gray-400 line-through' : 'text-gray-900'}`}>{item.title}</p>
                {item.description && (
                  <p className={`text-[10px] ${isDone ? 'text-gray-300' : 'text-gray-500'}`}>{item.description}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TableBlockRenderer({ block }: { block: TableBlock }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-100 text-xs text-left">
        <thead>
          <tr className="bg-gray-50/50">
            {block.data.headers.map((header, idx) => (
              <th key={idx} className="px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {block.data.rows.map((row, rowIdx) => (
            <tr key={rowIdx} className="hover:bg-gray-50/50 transition-colors">
              {row.map((cell, cellIdx) => (
                <td key={cellIdx} className="px-4 py-2.5 text-gray-700 font-medium">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
