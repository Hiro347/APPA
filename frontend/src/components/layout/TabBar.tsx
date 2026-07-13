'use client';

import { TabItem } from '@/lib/types';
import { MessageSquare } from 'lucide-react';

interface TabBarProps {
  tabs: TabItem[];
  activeTabId: string;
  onTabClick: (id: string) => void;
}

export function TabBar({ tabs, activeTabId, onTabClick }: TabBarProps) {
  return (
    <div className="h-10 border-b border-gray-200 flex items-end px-2 gap-0 bg-white overflow-x-auto hide-scrollbar">
      {tabs.map((tab) => {
        const isActive = tab.id === activeTabId;
        return (
          <button
            key={tab.id}
            onClick={() => onTabClick(tab.id)}
            className={`
              group relative flex items-center gap-1.5 px-4 h-9 text-sm transition-colors shrink-0
              ${isActive
                ? 'text-gray-900 border-b-2 border-gray-900 font-medium'
                : 'text-gray-400 hover:text-gray-600'
              }
            `}
          >
            {tab.type === 'chat' && <MessageSquare size={14} />}
            <span className="truncate max-w-[120px]">{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
