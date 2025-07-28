export interface Pin {
  _id: string;
  image_url: string;
  pin_url: string;
  title: string;
  description: string;
  match_score: number;
  status: 'approved' | 'disqualified';
  ai_explanation: string;
  metadata: {
    collected_at: string;
  };
}

export interface Prompt {
  _id: string;
  text: string;
  created_at: string;
  status: 'pending' | 'completed' | 'error';
}

export interface Session {
  _id: string;
  prompt_id: string;
  stage: 'warmup' | 'scraping' | 'validation';
  status: 'pending' | 'running' | 'completed' | 'failed';
  timestamp: string;
  logs: string[];
}

export interface ProgressStage {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  status: 'pending' | 'active' | 'completed' | 'failed';
  progress?: number;
  logs?: string[];
}

export type AppState = 'prompt' | 'progress' | 'review';
export type ViewMode = 'grid' | 'list';
export type StatusFilter = 'all' | 'approved' | 'disqualified';
