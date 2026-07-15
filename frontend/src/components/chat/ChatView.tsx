'use client';

import React, { useRef, useEffect, useLayoutEffect } from 'react';
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
  const lastRectRef = useRef<DOMRect | null>(null);
  const isInitialState = messages.length <= 1;

  // Keep track of the centered input rect
  useEffect(() => {
    if (isInitialState) {
      const panel = document.getElementById('chat-input-panel');
      if (panel) {
        lastRectRef.current = panel.getBoundingClientRect();
      }
    }
  });

  useLayoutEffect(() => {
    if (!isInitialState && lastRectRef.current) {
      const panel = document.getElementById('chat-input-panel');
      if (!panel) return;

      const oldRect = lastRectRef.current;
      const newRect = panel.getBoundingClientRect();
      const deltaY = oldRect.top - newRect.top;

      let animationFrameId: number;
      const startTime = performance.now();
      const duration = 450; // Total animation duration in ms
      let lastY = deltaY;

      // Ease-in-out quintic function for a sharper acceleration and higher peak speed
      const easeInOutQuint = (t: number) => t < 0.5 ? 16 * t * t * t * t * t : 1 - Math.pow(-2 * t + 2, 5) / 2;

      const animate = (time: number) => {
        let progress = (time - startTime) / duration;
        if (progress > 1) progress = 1;

        const easedProgress = easeInOutQuint(progress);
        const currentY = deltaY * (1 - easedProgress);

        const speed = currentY - lastY;
        lastY = currentY;

        if (progress === 1) {
          panel.style.transform = '';
          panel.style.filter = '';
          lastRectRef.current = null;
          return;
        }

        // Apply stretch proportional to the per-frame speed
        const stretch = 1 + Math.abs(speed) * 0.05;
        // Apply motion blur proportional to speed
        const blur = Math.abs(speed) * 0.15;

        // Since we are moving down (currentY increases to 0), anchor at bottom
        panel.style.transformOrigin = speed > 0 ? 'bottom center' : 'top center';
        panel.style.transform = `translateY(${currentY}px) scaleY(${stretch})`;
        panel.style.filter = blur > 0.5 ? `blur(${blur}px)` : '';

        animationFrameId = requestAnimationFrame(animate);
      };

      animationFrameId = requestAnimationFrame(animate);

      return () => {
        cancelAnimationFrame(animationFrameId);
        panel.style.transform = '';
        panel.style.filter = '';
      };
    }
  }, [isInitialState]);

  const isAtBottomRef = useRef(true);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    // Consider them at the bottom if within a 200px trigger zone
    isAtBottomRef.current = scrollHeight - clientHeight - scrollTop < 200;
  };

  useEffect(() => {
    if (!scrollRef.current || isInitialState) return;
    
    // If the AI is not generating, disable the smooth auto-scroll completely.
    // We just snap to the bottom instantly if they were already there.
    if (!isProcessing) {
      if (isAtBottomRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight - scrollRef.current.clientHeight;
      }
      return;
    }

    // If the user has manually scrolled up to read history, DO NOT auto-scroll and interrupt them!
    if (!isAtBottomRef.current) return;

    const container = scrollRef.current;
    let animationFrameId: number;
    let lastExpectedScrollTop = container.scrollTop;

    const animate = () => {
      const targetScroll = container.scrollHeight - container.clientHeight;
      const diff = targetScroll - container.scrollTop;

      // Detect if the user interrupted the smooth scroll by manually scrolling with their mouse/finger
      if (Math.abs(container.scrollTop - lastExpectedScrollTop) > 5) {
        return; // Abort!
      }

      // Fix Zeno's paradox: browsers ignore fractional scroll adjustments < 1px, 
      // causing the loop to run endlessly in the background. Use 5px threshold.
      if (Math.abs(diff) < 5) {
        container.scrollTop = targetScroll;
        return;
      }

      const speed = diff * 0.15;
      container.scrollTop += speed;
      lastExpectedScrollTop = container.scrollTop;

      animationFrameId = requestAnimationFrame(animate);
    };

    animationFrameId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [messages, isInitialState, isProcessing]);

  const WINDOW_SIZE = 10;
  const cutoffIndex = messages.length > WINDOW_SIZE ? messages.length - WINDOW_SIZE : -1;

  return (
    <div className={`flex-1 flex flex-col h-full ${isInitialState ? 'justify-center' : ''}`}>
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className={`overflow-y-auto px-6 py-4 w-full ${isInitialState ? 'h-[180px]' : 'flex-1'}`}
      >
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
      <ChatInput onSend={onSend} disabled={isProcessing} centered={false} />
    </div>
  );
}
