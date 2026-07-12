'use client';

import { useState, FormEvent, KeyboardEvent } from 'react';
import { ArrowUp, Paperclip, ChevronDown } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  centered?: boolean;
}

function InputPanel({ value, setValue, onSubmit, disabled }: {
  value: string;
  setValue: (v: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}) {
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="border border-gray-200 rounded-2xl bg-white hover:border-gray-300 transition-colors focus-within:ring-1 focus-within:ring-gray-400">
      {/* Top row: textarea */}
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ceritakan tentang bisnis Anda..."
        rows={2}
        className="w-full px-4 pt-3 pb-1 bg-transparent text-sm text-gray-900 placeholder:text-gray-400 outline-none resize-none"
        disabled={disabled}
      />

      {/* Bottom row: actions */}
      <div className="flex items-center justify-between px-3 pb-2.5">
        <div className="flex items-center gap-1">
          {/* Attachment */}
          <button
            type="button"
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            title="Lampiran"
          >
            <Paperclip size={16} />
          </button>

          {/* Model picker */}
          <button
            type="button"
            className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <span>APPA v1</span>
            <ChevronDown size={12} />
          </button>
        </div>

        {/* Send */}
        <button
          type="button"
          onClick={onSubmit}
          disabled={!value.trim() || disabled}
          className="p-2 rounded-lg bg-gray-900 text-white disabled:bg-gray-200 disabled:text-gray-400 transition-colors"
        >
          <ArrowUp size={16} />
        </button>
      </div>
    </div>
  );
}

const DISCLAIMER = (
  <p className="text-[10px] text-gray-400 text-center mt-2 italic font-medium">
    APPA adalah prototipe kompetisi. Hasil bisa tidak akurat, selalu verifikasi ulang.
  </p>
);

export function ChatInput({ onSend, disabled, centered }: ChatInputProps) {
  const [value, setValue] = useState('');

  const handleSubmit = () => {
    if (!value.trim() || disabled) return;
    onSend(value.trim());
    setValue('');
  };

  if (centered) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-1">APPA</h2>
        <p className="text-sm text-gray-400 mb-8">Analisa Pasar Pintar & Akurat</p>
        <div className="w-full max-w-xl">
          <InputPanel value={value} setValue={setValue} onSubmit={handleSubmit} disabled={disabled} />
          {DISCLAIMER}
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 bg-transparent">
      <div className="max-w-3xl mx-auto">
        <InputPanel value={value} setValue={setValue} onSubmit={handleSubmit} disabled={disabled} />
        {DISCLAIMER}
      </div>
    </div>
  );
}

