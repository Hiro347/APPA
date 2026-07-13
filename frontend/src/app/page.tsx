'use client';

import { useState, useMemo, useEffect } from 'react';
import { useChat } from '@/hooks/useChat';
import { TabItem } from '@/lib/types';
import { ProfileSidebar } from '@/components/layout/ProfileSidebar';
import { TabBar } from '@/components/layout/TabBar';
import { ChatView } from '@/components/chat/ChatView';
import { ArtifactView } from '@/components/artifacts/ArtifactView';

export default function Home() {
  const { messages, artifacts, profile, isProcessing, send, updateArtifact } = useChat();
  const [activeTab, setActiveTab] = useState('chat');

  // Auto-switch is disabled to prevent jarring jumps when hitting enter

  // Derive tabs from artifacts
  const tabs: TabItem[] = useMemo(() => {
    const base: TabItem[] = [{ id: 'chat', label: 'Chat', type: 'chat', closeable: false }];
    const artifactTabs: TabItem[] = artifacts.map(a => ({
      id: a.id,
      label: a.title,
      type: 'artifact',
      artifactId: a.id,
      closeable: false,
    }));
    return [...base, ...artifactTabs];
  }, [artifacts]);

  // If active tab was closed/not found, fall back to chat
  const validActiveTab = tabs.find(t => t.id === activeTab) ? activeTab : 'chat';

  // Find active artifact
  const activeArtifact = artifacts.find(a => a.id === validActiveTab);

  return (
    <div className="h-screen w-full flex overflow-hidden bg-white">
      {/* Left: Profile Sidebar */}
      <ProfileSidebar profile={profile} />

      {/* Right: Tabs + Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Tab bar (hidden when no messages and no artifacts — show clean initial state) */}
        {(messages.length > 0 || artifacts.length > 0) && (
          <TabBar
            tabs={tabs}
            activeTabId={validActiveTab}
            onTabClick={setActiveTab}
          />
        )}

        {/* Content area */}
        <div className="flex-1 flex flex-col min-h-0">
          {validActiveTab === 'chat' ? (
            <ChatView messages={messages} isProcessing={isProcessing} onSend={send} />
          ) : activeArtifact ? (
            <div className="flex-1 overflow-y-auto bg-gray-50">
              <ArtifactView
                artifact={activeArtifact}
                onUpdate={(blocks) => updateArtifact(activeArtifact.id, blocks)}
              />
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
