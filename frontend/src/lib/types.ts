// === Pipeline Status ===
export type StepStatus = 'waiting' | 'running' | 'done' | 'error';

export interface PipelineStep {
  id: string;
  label: string;
  status: StepStatus;
  details?: string;
}

export interface PipelineGroup {
  id: string;
  icon: string;
  label: string;
  steps: PipelineStep[];
}

// === Chat ===
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
  pipeline?: PipelineGroup[];
  pipelineComplete?: boolean;
}

// === Artifacts ===
export type BlockType = 'text' | 'metric' | 'checklist' | 'chart' | 'table';

export interface TextBlock {
  type: 'text';
  content: string;
  sources?: string[];
}

export interface MetricBlock {
  type: 'metric';
  data: {
    hpp: number;
    market_avg: number;
    recommendation: number;
  };
  sources?: string[];
}

export interface ChecklistBlock {
  type: 'checklist';
  data: {
    items: { title: string; status: string; description?: string; }[];
  };
  sources?: string[];
}

export interface ChartBlock {
  type: 'chart';
  data: {
    chartType?: 'bar' | 'line';
    xAxis: string[];
    yAxis: number[];
    label?: string;
  };
  sources?: string[];
}

export interface TableBlock {
  type: 'table';
  data: {
    headers: string[];
    rows: string[][];
  };
  sources?: string[];
}

export type ArtifactBlock = TextBlock | MetricBlock | ChecklistBlock | ChartBlock | TableBlock;

export interface Artifact {
  id: string;
  title: string;
  blocks: ArtifactBlock[];
  sources: string[];
}

// === Profile ===
export interface ComplianceItem {
  item: string;
  status: 'done' | 'pending' | 'not_started';
}

export interface UserProfile {
  business_name?: string;
  business_type?: string;
  product_category?: string;
  capital_hpp?: number;
  compliance_status: ComplianceItem[];
}

// === Tabs ===
export interface TabItem {
  id: string;
  label: string;
  type: 'chat' | 'artifact';
  artifactId?: string;
  closeable: boolean;
}
