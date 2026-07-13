'use client';

import { useState, useCallback, useRef } from 'react';
import { ChatMessage, Artifact, UserProfile, PipelineGroup, ArtifactBlock } from '../lib/types';
import { MOCK_PROFILE, createPipelineGroups, simulateResponse } from '../lib/mock';
import { sendChatMessage } from '../lib/api';

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== 'false';
const USER_ID = 'user_default'; // TODO: Replace with real auth when available

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
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
      pipeline: createPipelineGroups(content),
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
        .then((data) => {
          // Update assistant message with response text and mark pipeline done
          updateLastAssistant(msg => ({
            ...msg,
            content: data.response || '',
            isStreaming: false,
            pipelineComplete: true,
            pipeline: msg.pipeline?.map(group => ({
              ...group,
              steps: group.steps.map(step => ({ ...step, status: 'done' }))
            }))
          }));

          // Add artifacts if present
          if (data.artifacts && data.artifacts.length > 0) {
            setArtifacts(prev => [...prev, ...data.artifacts]);
          }

          // Update profile if backend says it was updated
          if (data.profile_updated) {
            // Re-fetch profile from backend could be done here
            // For now, we trust the implicit updates in SQLite
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
