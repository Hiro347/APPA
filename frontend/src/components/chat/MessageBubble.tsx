'use client';

import { ChatMessage } from '@/lib/types';
import { ThinkingDisplay } from '@/components/chat/ThinkingDisplay';
import { User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';



import React, { useMemo } from 'react';

const AnimatedTokenStream = ({ text }: { text: string }) => {
  const tokens = text.split(/(\s+)/);
  let wordCount = 0;
  return (
    <div className="whitespace-pre-wrap leading-relaxed mt-1 text-sm text-gray-800">
      {tokens.map((token, i) => {
        if (!token.trim()) return <span key={i}>{token}</span>;
        const delay = wordCount * 25; // 25ms delay per token
        wordCount++;
        return (
          <span
            key={i}
            className="inline-block animate-slide-up-blur-fast"
            style={{ animationDelay: `${delay}ms`, animationFillMode: 'both' }}
          >
            {token}
          </span>
        );
      })}
    </div>
  );
};

const AnimatedMarkdownText = ({ children, isStreaming }: { children: React.ReactNode, isStreaming?: boolean }) => {
  const toArray = React.Children.toArray(children);
  return (
    <>
      {toArray.map((child, childIndex) => {
        if (typeof child === 'string') {
          const tokens = child.split(/(\s+)/);
          return tokens.map((token, i) => {
            if (!token.trim()) return <span key={`space-${childIndex}-${i}`}>{token}</span>;
            return (
              <span 
                key={`token-${childIndex}-${i}`} 
                className={isStreaming ? "inline-block animate-slide-up-blur-fast" : ""}
              >
                {token}
              </span>
            );
          });
        }
        return child;
      })}
    </>
  );
};

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  const markdownComponents = useMemo(() => ({
    p: ({ children }: any) => <p className="mb-2 last:mb-0"><AnimatedMarkdownText isStreaming={message.isStreaming}>{children}</AnimatedMarkdownText></p>,
    strong: ({ children }: any) => <strong className="font-semibold text-gray-950"><AnimatedMarkdownText isStreaming={message.isStreaming}>{children}</AnimatedMarkdownText></strong>,
    ul: ({ children }: any) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
    ol: ({ children }: any) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
    li: ({ children }: any) => <li className="text-gray-700"><AnimatedMarkdownText isStreaming={message.isStreaming}>{children}</AnimatedMarkdownText></li>,
    h1: ({ children }: any) => <h1 className="text-base font-bold text-gray-950 mt-3 mb-1"><AnimatedMarkdownText isStreaming={message.isStreaming}>{children}</AnimatedMarkdownText></h1>,
    h2: ({ children }: any) => <h2 className="text-sm font-semibold text-gray-950 mt-2.5 mb-1"><AnimatedMarkdownText isStreaming={message.isStreaming}>{children}</AnimatedMarkdownText></h2>,
    h3: ({ children }: any) => <h3 className="text-xs font-semibold text-gray-900 mt-2 mb-0.5"><AnimatedMarkdownText isStreaming={message.isStreaming}>{children}</AnimatedMarkdownText></h3>,
  }), [message.isStreaming]);

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="flex items-start gap-2.5 max-w-[75%] flex-row-reverse">
          <div className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
            <User size={14} className="text-gray-500" />
          </div>
          <div className="bg-gray-100 text-gray-900 text-sm px-4 py-2.5 rounded-2xl rounded-tr-sm">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="flex justify-start mb-4">
      <div className="flex items-start gap-2.5 max-w-[85%]">
        <div className="w-7 h-7 rounded-full bg-gray-900 flex items-center justify-center shrink-0">
          <Bot size={14} className="text-white" />
        </div>
        <div className="text-sm text-gray-800 min-w-0">
          {/* Pipeline / Thinking */}
          {message.pipeline && message.pipeline.length > 0 && (
            <ThinkingDisplay
              pipeline={message.pipeline}
              isComplete={message.pipelineComplete ?? false}
            />
          )}

          {/* Text content */}
          {message.content && (
            message.id === 'initial-greeting' ? (
              <AnimatedTokenStream text={message.content} />
            ) : (
              <div className="leading-relaxed mt-1 text-sm text-gray-800 animate-slide-up-blur-fast">
                <ReactMarkdown components={markdownComponents}>
                  {message.content}
                </ReactMarkdown>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
