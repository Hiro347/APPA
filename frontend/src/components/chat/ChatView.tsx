'use client';

import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '@/lib/types';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';

interface ChatViewProps {
  messages: ChatMessage[];
  isProcessing: boolean;
  onSend: (message: string) => void;
}

export function ChatView({ messages, isProcessing, onSend }: ChatViewProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const isEmpty = messages.length === 0;

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Initial state: centered input
  if (isEmpty) {
    return (
      <div className="flex-1 flex flex-col h-full">
        <ChatInput onSend={onSend} disabled={isProcessing} centered />
      </div>
    );
  }

  const WINDOW_SIZE = 10;
  const cutoffIndex = messages.length > WINDOW_SIZE ? messages.length - WINDOW_SIZE : -1;

  // Active state: messages + bottom input
  return (
    <div className="flex-1 flex flex-col h-full">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-3xl mx-auto">
          {messages.map((msg, idx) => (
            <React.Fragment key={msg.id}>
              {idx === cutoffIndex && (
                <div className="w-full flex items-center justify-center gap-4 my-8">
                  <div className="flex-1 border-t border-dashed border-gray-300"></div>
                  <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">
                    Batas Memori AI
                  </span>
                  <div className="flex-1 border-t border-dashed border-gray-300"></div>
                </div>
              )}
              <MessageBubble message={msg} />
            </React.Fragment>
          ))}
        </div>
      </div>
      <ChatInput onSend={onSend} disabled={isProcessing} />
    </div>
  );
}
