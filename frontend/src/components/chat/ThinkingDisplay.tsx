'use client';

import { useState } from 'react';
import { PipelineGroup } from '@/lib/types';
import { ChevronDown, ChevronRight, Loader2, Check, X, Clock } from 'lucide-react';

const StepIcon = ({ status }: { status: string }) => {
  if (status === 'done') return <Check size={12} className="text-green-600" />;
  if (status === 'running') return <Loader2 size={12} className="text-gray-900 animate-spin" />;
  if (status === 'error') return <X size={12} className="text-red-500" />;
  return <Clock size={12} className="text-gray-300" />;
};

interface ThinkingDisplayProps {
  pipeline: PipelineGroup[];
  isComplete: boolean;
}

export function ThinkingDisplay({ pipeline, isComplete }: ThinkingDisplayProps) {
  const [expanded, setExpanded] = useState(true);

  // Auto-collapse when complete
  const isExpanded = isComplete ? expanded : true;

  const totalSteps = pipeline.reduce((sum, g) => sum + g.steps.length, 0);
  const doneSteps = pipeline.reduce((sum, g) => sum + g.steps.filter(s => s.status === 'done').length, 0);

  return (
    <div className="mb-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 transition-colors py-1"
      >
        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span className="font-mono">
          {isComplete ? `Proses selesai (${doneSteps}/${totalSteps})` : `Sedang memproses... (${doneSteps}/${totalSteps})`}
        </span>
        {!isComplete && <Loader2 size={12} className="animate-spin text-gray-400" />}
      </button>

      {isExpanded && (
        <div className="ml-1 mt-1 space-y-2 font-mono text-xs">
          {pipeline.map((group) => (
            <div key={group.id}>
              <div className="flex items-center gap-1.5 text-gray-700 font-medium">
                {group.icon && <span>{group.icon}</span>}
                <span>{group.label}</span>
              </div>
              <div className="ml-5 mt-0.5 space-y-0.5">
                {group.steps.map((step, i) => {
                  const isLast = i === group.steps.length - 1;
                  return (
                    <div key={step.id} className="flex items-center gap-1.5">
                      <span className="text-gray-300 select-none">{isLast ? '└─' : '├─'}</span>
                      <StepIcon status={step.status} />
                      <span className={step.status === 'done' ? 'text-gray-500' : step.status === 'running' ? 'text-gray-900' : 'text-gray-400'}>
                        {step.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
