import type { Pin, Prompt, Session } from '../types';

// Dynamically use current hostname (works for Docker + dev)
const hostname = window.location.hostname;
const API_BASE_URL = `http://${hostname}:8000/api`;

console.log('🔍 API configuration:', {
  hostname: hostname,
  baseUrl: API_BASE_URL,
  isDocker: hostname !== 'localhost' && hostname !== '127.0.0.1'
});

export class ApiService {
  static async submitPrompt(text: string): Promise<{ prompt_id: string; status: string; message: string }> {
    const response = await fetch(`${API_BASE_URL}/prompts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      throw new Error(`Failed to submit prompt: ${response.statusText}`);
    }

    return response.json();
  }

  static async getPromptStatus(promptId: string): Promise<{
    prompt: Prompt;
    sessions: Session[];
    overall_progress: number;
    current_stage: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/prompts/${promptId}/status`);

    if (!response.ok) {
      throw new Error(`Failed to get prompt status: ${response.statusText}`);
    }

    return response.json();
  }

  static async getPins(promptId: string, filters?: {
    status?: 'all' | 'approved' | 'disqualified';
    min_score?: number;
  }): Promise<{
    pins: Pin[];
    total_count: number;
    approved_count: number;
    disqualified_count: number;
    avg_score: number;
  }> {
    const searchParams = new URLSearchParams();
    if (filters?.status && filters.status !== 'all') {
      searchParams.append('status', filters.status);
    }
    if (filters?.min_score !== undefined) {
      searchParams.append('min_score', filters.min_score.toString());
    }

    const url = `${API_BASE_URL}/prompts/${promptId}/pins${
      searchParams.toString() ? `?${searchParams.toString()}` : ''
    }`;

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to get pins: ${response.statusText}`);
    }

    return response.json();
  }

  static async getPromptHistory(): Promise<Prompt[]> {
    const response = await fetch(`${API_BASE_URL}/prompts`);

    if (!response.ok) {
      throw new Error(`Failed to get prompt history: ${response.statusText}`);
    }

    return response.json();
  }
}
