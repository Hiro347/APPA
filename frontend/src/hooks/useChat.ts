'use client';

import { useState, useCallback, useRef } from 'react';
import { ChatMessage, Artifact, UserProfile, PipelineGroup, ArtifactBlock } from '../lib/types';
import { MOCK_PROFILE, createPipelineGroups, simulateResponse } from '../lib/mock';
import { sendChatMessage } from '../lib/api';

// TODO: [MOCK REPLACEMENT] Remove this flag when moving to production API.
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== 'false';
// TODO: [MOCK REPLACEMENT] Connect to real authentication provider (e.g. NextAuth) to get actual USER_ID.
const USER_ID = 'user_default'; 

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  // TODO: [MOCK REPLACEMENT] Fetch initial profile from database instead of MOCK_PROFILE
  const [profile, setProfile] = useState<UserProfile>(MOCK_PROFILE);
  const [isProcessing, setIsProcessing] = useState(false);
  const cancelRef = useRef<(() => void) | null>(null);

  const updateLastAssistant = useCallback((updater: (msg: ChatMessage) => ChatMessage) => {
    setMessages(prev => {
      const copy = [...prev];
      for (let i = copy.length - 1; i >= 0; i--) {
        if (copy[i].role === 'assistant') {
          copy[i] = updater(copy[i]);
          break;
        }
      }
      return copy;
    });
  }, []);

  const send = useCallback((content: string) => {
    if (!content.trim() || isProcessing) return;

    // Add user message
    const userMsg: ChatMessage = { id: `u-${Date.now()}`, role: 'user', content };
    const assistantMsg: ChatMessage = {
      id: `a-${Date.now()}`,
      role: 'assistant',
      content: '',
      isStreaming: true,
      pipeline: USE_MOCK ? createPipelineGroups(content) : [],
      pipelineComplete: false,
    };
    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setIsProcessing(true);

    if (USE_MOCK) {
      // === MOCK MODE (original behavior) ===
      const cancel = simulateResponse(content, {
        onPipelineUpdate: (groups: PipelineGroup[]) => {
          updateLastAssistant(msg => ({ ...msg, pipeline: groups }));
        },
        onPipelineComplete: () => {
          updateLastAssistant(msg => ({ ...msg, pipelineComplete: true }));
        },
        onStreamChar: (char: string) => {
          updateLastAssistant(msg => ({ ...msg, content: msg.content + char }));
        },
        onArtifacts: (newArtifacts: Artifact[]) => {
          setArtifacts(prev => [...prev, ...newArtifacts]);
          // Update mock profile after research
          setProfile(p => ({
            ...p,
            business_type: 'F&B Mikro',
            product_category: 'Keripik Singkong',
            capital_hpp: 5000,
            compliance_status: [
              { item: 'NIB', status: 'pending' },
              { item: 'SPP-IRT', status: 'not_started' },
              { item: 'Sertifikat Halal', status: 'not_started' },
            ],
          }));
        },
        onDone: () => {
          updateLastAssistant(msg => ({ ...msg, isStreaming: false }));
          setIsProcessing(false);
        },
      });

      cancelRef.current = cancel;
    } else {
      // === API MODE (real backend) ===
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      
      sendChatMessage(USER_ID, content, history)
        .then(async (res) => {
          if (!res.body) throw new Error("ReadableStream not supported in this browser.");
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep the incomplete line in the buffer
            
            for (const line of lines) {
              if (!line.trim()) continue;
              try {
                const data = JSON.parse(line);
                
                if (data.type === 'pipeline_init') {
                  updateLastAssistant(msg => ({ ...msg, pipeline: data.pipeline }));
                } else if (data.type === 'pipeline_update') {
                  updateLastAssistant(msg => {
                    if (!msg.pipeline) return msg;
                    const newPipeline = msg.pipeline.map(group => ({
                      ...group,
                      steps: group.steps.map(step => 
                        step.id === data.step_id ? { ...step, status: data.status, details: data.details, label: data.label || step.label } : step
                      )
                    }));
                    return { ...msg, pipeline: newPipeline };
                  });
                } else if (data.type === 'result') {
                  updateLastAssistant(msg => ({
                    ...msg,
                    content: data.data.response || '',
                    isStreaming: false,
                    pipelineComplete: true,
                    pipeline: msg.pipeline?.map(group => ({
                      ...group,
                      steps: group.steps.map(step => ({ ...step, status: 'done' }))
                    }))
                  }));

                  if (data.data.artifacts && data.data.artifacts.length > 0) {
                    setArtifacts(prev => [...prev, ...data.data.artifacts]);
                  }
                  
                  if (data.data.profile_updated) {
                    // Implicit update or trigger a refetch here if needed
                  }
                }
              } catch (e) {
                console.error("Failed to parse stream line:", line, e);
              }
            }
          }
        })
        .catch((err) => {
          console.error('Backend API error:', err);
          updateLastAssistant(msg => ({
            ...msg,
            content: 'Maaf, terjadi kesalahan koneksi ke server. Silakan coba lagi.',
            isStreaming: false,
            pipelineComplete: true,
          }));
        })
        .finally(() => {
          setIsProcessing(false);
        });
    }
  }, [isProcessing, updateLastAssistant, messages]);

  const updateArtifact = useCallback((id: string, blocks: ArtifactBlock[]) => {
    setArtifacts(prev => prev.map(a => a.id === id ? { ...a, blocks } : a));
  }, []);

  return { messages, artifacts, profile, isProcessing, send, updateArtifact };
}
