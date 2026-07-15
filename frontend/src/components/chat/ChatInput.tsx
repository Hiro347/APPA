'use client';

import { useState, useRef, useEffect, FormEvent, KeyboardEvent } from 'react';
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
  const [isFocused, setIsFocused] = useState(false);
  const [canScrollTop, setCanScrollTop] = useState(false);
  const [canScrollBottom, setCanScrollBottom] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const checkScroll = () => {
    if (textareaRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = textareaRef.current;

      let effectiveClientHeight = clientHeight;
      if (isFocused) {
        // When focused, the textarea is trying to fit the scrollHeight,
        // but it is constrained by max-height (33vh).
        // By reading the computed max-height, we can predict the final clientHeight
        // and avoid flashing the gradient while the CSS transition is still animating.
        const computedStyle = window.getComputedStyle(textareaRef.current);
        const maxHeightStr = computedStyle.maxHeight;
        if (maxHeightStr && maxHeightStr !== 'none') {
          const maxH = parseFloat(maxHeightStr);
          if (!isNaN(maxH)) {
            effectiveClientHeight = Math.min(scrollHeight, maxH);
          }
        }
      }

      setCanScrollTop(scrollTop > 0);
      setCanScrollBottom(scrollHeight - effectiveClientHeight - Math.ceil(scrollTop) > 1);
    }
  };

  const prevIsFocused = useRef(isFocused);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const isFocusChange = prevIsFocused.current !== isFocused;
    prevIsFocused.current = isFocused;

    if (isFocused) {
      const currentHeight = textarea.style.height || `${textarea.offsetHeight}px`;
      const currentScrollTop = textarea.scrollTop;

      // Measure the new target height
      textarea.style.transition = 'none';
      textarea.style.height = 'auto';
      const targetHeight = textarea.scrollHeight;

      // If the height is already correct, don't trigger an animation
      if (currentHeight === `${targetHeight}px`) {
        textarea.style.height = currentHeight;
        textarea.scrollTop = currentScrollTop;
      } else {
        // Restore previous state
        textarea.style.height = currentHeight;
        textarea.scrollTop = currentScrollTop;
        void textarea.offsetHeight; // Force reflow

        // Use a faster, snappy animation for typing and resizing
        textarea.style.transition = 'height 150ms cubic-bezier(0.2, 0.8, 0.2, 1)';
        textarea.style.height = `${targetHeight}px`;
      }
    } else {
      if (isFocusChange) {
        // Animate collapse
        const currentHeight = textarea.style.height || `${textarea.offsetHeight}px`;
        const currentScrollTop = textarea.scrollTop;

        textarea.style.transition = 'none';
        textarea.style.height = '';
        const targetHeight = textarea.offsetHeight;

        textarea.style.height = currentHeight;
        textarea.scrollTop = currentScrollTop;
        void textarea.offsetHeight;

        textarea.style.transition = 'height 300ms cubic-bezier(0.2, 0.8, 0.2, 1)';
        textarea.style.height = `${targetHeight}px`;
      } else {
        textarea.style.transition = 'none';
        textarea.style.height = '';
      }
    }

    // Check scroll state after adjusting height
    requestAnimationFrame(checkScroll);
  }, [value, isFocused]);

  // Global auto-focus: focus the input field if the user starts typing anywhere on the page
  useEffect(() => {
    const handleGlobalKeyDown = (e: globalThis.KeyboardEvent) => {
      // Ignore if holding modifiers (Ctrl, Cmd, Alt) or pressing Escape
      if (e.ctrlKey || e.metaKey || e.altKey || e.key === 'Escape') return;

      // Ignore if already typing in another input, textarea, or contenteditable
      const target = e.target as HTMLElement;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) {
        return;
      }

      // Ignore purely functional keys (F1-F12, Arrows, etc.) but allow Backspace and Enter
      if (e.key.length > 1 && e.key !== 'Backspace' && e.key !== 'Enter') return;

      if (textareaRef.current && document.activeElement !== textareaRef.current) {
        textareaRef.current.focus();
        // The typed character will naturally be inserted into the textarea by the browser
      }
    };

    document.addEventListener('keydown', handleGlobalKeyDown);
    return () => document.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div
      id="chat-input-panel"
      className="border border-gray-200 rounded-xl bg-white hover:border-gray-300 transition-colors focus-within:ring-1 focus-within:ring-gray-400 overflow-hidden"
    >
      {/* Top row: textarea wrapper */}
      <div className="relative w-full">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            checkScroll();
          }}
          onScroll={checkScroll}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="Ceritakan tentang bisnis Anda..."
          rows={2}
          className={`w-full px-4 pt-3 pb-1 bg-transparent text-sm text-gray-900 placeholder:text-gray-400 outline-none resize-none [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] ${isFocused ? 'max-h-[33vh] overflow-y-auto' : 'overflow-hidden'}`}
          disabled={disabled}
        />
        {/* Scroll gradients */}
        <div
          className={`absolute top-0 inset-x-0 h-10 bg-gradient-to-b from-white to-transparent pointer-events-none transition-opacity duration-200 ${canScrollTop && isFocused ? 'opacity-100' : 'opacity-0'}`}
        />
        <div
          className={`absolute bottom-0 inset-x-0 h-10 bg-gradient-to-t from-white to-transparent pointer-events-none transition-opacity duration-200 ${canScrollBottom && isFocused ? 'opacity-100' : 'opacity-0'}`}
        />
      </div>

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

        <div className="w-full max-w-3xl">
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

